"""Tetris Bot v8 - PLAY MODE with smooth AI.

Opens freetetris.org, starts the game, detects the board,
and plays Tetris using AI with gentle, deliberate inputs.
"""
import time
import math
import json
import os
import io
import sys
from playwright.sync_api import sync_playwright
from PIL import Image

BOARD_COLS = 10
BOARD_ROWS = 20
LEARNING_FILE = os.path.join(os.path.dirname(__file__), "tetris_learning.json")
DEBUG_IMG = os.path.join(os.path.dirname(__file__), "tetris_debug.png")

EMPTY_CELL_COLOR = (198, 216, 242)
PAGE_BG_COLOR = (220, 238, 255)

# Piece definitions: rotation variants as (row, col) offsets from top-left
PIECES = {
    "I": [[(0,0),(0,1),(0,2),(0,3)],
          [(0,0),(1,0),(2,0),(3,0)]],
    "O": [[(0,0),(0,1),(1,0),(1,1)]],
    "T": [[(0,0),(0,1),(0,2),(1,1)],
          [(0,0),(1,0),(2,0),(1,1)],
          [(1,0),(1,1),(1,2),(0,1)],
          [(0,0),(1,0),(2,0),(1,-1)]],
    "S": [[(0,1),(0,2),(1,0),(1,1)],
          [(0,0),(1,0),(1,1),(2,1)]],
    "Z": [[(0,0),(0,1),(1,1),(1,2)],
          [(0,1),(1,0),(1,1),(2,0)]],
    "J": [[(0,0),(1,0),(1,1),(1,2)],
          [(0,0),(0,1),(1,0),(2,0)],
          [(0,0),(0,1),(0,2),(1,2)],
          [(0,0),(1,0),(2,0),(2,-1)]],
    "L": [[(0,2),(1,0),(1,1),(1,2)],
          [(0,0),(1,0),(2,0),(2,1)],
          [(0,0),(0,1),(0,2),(1,0)],
          [(0,0),(0,1),(1,1),(2,1)]],
}

# AI scoring weights
W_LINES = 10.0
W_HOLES = -0.75
W_BUMP = -0.18
W_HEIGHT = -0.5


def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def is_empty_cell(r, g, b):
    return color_distance((r, g, b), EMPTY_CELL_COLOR) < 30


def is_filled_cell(r, g, b):
    if is_empty_cell(r, g, b):
        return False
    if color_distance((r, g, b), PAGE_BG_COLOR) < 15:
        return False
    if (r + g + b) / 3 < 140:
        return False
    return color_distance((r, g, b), EMPTY_CELL_COLOR) > 50


def get_iframe_element(page):
    return page.query_selector("#gameIFrame")


def get_game_frame(page):
    for f in page.frames:
        if f.name == "gameIFrame":
            return f
    el = page.query_selector("#gameIFrame")
    if el:
        return el.content_frame()
    return None


def screenshot_iframe(iframe_el):
    data = iframe_el.screenshot()
    return Image.open(io.BytesIO(data))


def find_board_in_iframe(img):
    w, h = img.size
    max_x = int(w * 0.65)
    empty_xs = []
    empty_ys = []
    for y in range(0, h, 4):
        for x in range(0, max_x, 4):
            r, g, b = img.getpixel((x, y))[:3]
            if is_empty_cell(r, g, b):
                empty_xs.append(x)
                empty_ys.append(y)
    if len(empty_xs) < 50:
        return None
    empty_xs.sort()
    empty_ys.sort()
    trim = max(1, len(empty_xs) // 20)
    left, right = empty_xs[trim], empty_xs[-trim]
    top, bottom = empty_ys[trim], empty_ys[-trim]
    if (right - left) < 100 or (bottom - top) < 200:
        return None
    cell_w = (right - left) / BOARD_COLS
    cell_h = (bottom - top) / BOARD_ROWS
    if cell_w < 15 or cell_w > 80 or cell_h < 10 or cell_h > 50:
        return None
    return (left, top, right, bottom)


def read_board(iframe_el, bounds):
    img = screenshot_iframe(iframe_el)
    x1, y1, x2, y2 = bounds
    cell_w = (x2 - x1) / BOARD_COLS
    cell_h = (y2 - y1) / BOARD_ROWS
    board = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            cx = int(x1 + col * cell_w + cell_w * 0.5)
            cy = int(y1 + row * cell_h + cell_h * 0.5)
            filled = 0
            for dx, dy in [(0, 0), (int(cell_w * 0.2), 0),
                           (0, int(cell_h * 0.2)), (-int(cell_w * 0.2), 0)]:
                px, py = cx + dx, cy + dy
                if 0 <= px < img.width and 0 <= py < img.height:
                    r, g, b = img.getpixel((px, py))[:3]
                    if is_filled_cell(r, g, b):
                        filled += 1
            if filled >= 2:
                board[row][col] = 1
    return board


def get_column_heights(board):
    heights = []
    for col in range(BOARD_COLS):
        for row in range(BOARD_ROWS):
            if board[row][col]:
                heights.append(BOARD_ROWS - row)
                break
        else:
            heights.append(0)
    return heights


def count_holes(board):
    holes = 0
    for col in range(BOARD_COLS):
        found = False
        for row in range(BOARD_ROWS):
            if board[row][col]:
                found = True
            elif found:
                holes += 1
    return holes


def count_filled(board):
    return sum(sum(row) for row in board)


def get_bumpiness(heights):
    return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))


def clear_lines(board):
    new_board = [row[:] for row in board if not all(row)]
    cleared = BOARD_ROWS - len(new_board)
    while len(new_board) < BOARD_ROWS:
        new_board.insert(0, [0] * BOARD_COLS)
    return new_board, cleared


def drop_piece(board, cells, col_offset):
    for row_offset in range(BOARD_ROWS):
        valid = True
        for dr, dc in cells:
            r, c = row_offset + dr, col_offset + dc
            if r >= BOARD_ROWS or c < 0 or c >= BOARD_COLS:
                valid = False
                break
            if r >= 0 and board[r][c]:
                valid = False
                break
        if not valid:
            if row_offset == 0:
                return None
            new_board = [r[:] for r in board]
            for dr, dc in cells:
                r, c = row_offset - 1 + dr, col_offset + dc
                if 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS:
                    new_board[r][c] = 1
            return new_board
    # Piece falls to absolute bottom
    max_dr = max(dr for dr, dc in cells)
    bottom_row = BOARD_ROWS - 1 - max_dr
    new_board = [r[:] for r in board]
    for dr, dc in cells:
        r, c = bottom_row + dr, col_offset + dc
        if 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS:
            new_board[r][c] = 1
    return new_board


def evaluate_board(board, lines_cleared):
    heights = get_column_heights(board)
    return (W_LINES * lines_cleared +
            W_HOLES * count_holes(board) +
            W_BUMP * get_bumpiness(heights) +
            W_HEIGHT * max(heights))


def find_best_move(board, piece_type):
    if piece_type not in PIECES:
        return (0, 4, 0)
    rotations = PIECES[piece_type]
    best = (0, 4, float("-inf"))
    for rot_idx, cells in enumerate(rotations):
        min_c = min(dc for _, dc in cells)
        max_c = max(dc for _, dc in cells)
        for col in range(-min_c, BOARD_COLS - max_c):
            result = drop_piece(board, cells, col)
            if result is None:
                continue
            cleared, lines = clear_lines(result)
            score = evaluate_board(cleared, lines)
            if score > best[2]:
                best = (rot_idx, col, score)
    return best


def detect_piece(old_board, new_board):
    """Find new cells in top 6 rows that appeared since last board."""
    new_cells = []
    for row in range(6):
        for col in range(BOARD_COLS):
            if new_board[row][col] and not old_board[row][col]:
                new_cells.append((row, col))
    if len(new_cells) != 4:
        return None, new_cells
    min_r = min(r for r, c in new_cells)
    min_c = min(c for r, c in new_cells)
    normalized = tuple(sorted((r - min_r, c - min_c) for r, c in new_cells))
    for ptype, rotations in PIECES.items():
        for cells in rotations:
            if tuple(sorted(cells)) == normalized:
                return ptype, new_cells
    return "?", new_cells


def execute_move(page, rotation, target_col, spawn_col):
    """Send key presses with deliberate timing."""
    # Rotate first
    for _ in range(rotation):
        page.keyboard.press("ArrowUp")
        time.sleep(0.10)

    # Move horizontally
    diff = target_col - spawn_col
    key = "ArrowRight" if diff > 0 else "ArrowLeft"
    for _ in range(abs(diff)):
        page.keyboard.press(key)
        time.sleep(0.10)

    # Hard drop
    time.sleep(0.05)
    page.keyboard.press("Space")


def check_game_state(game_frame):
    try:
        return game_frame.evaluate("""() => {
            const info = {state: null};
            if (typeof window.mBPSApp !== 'undefined' && window.mBPSApp.mStateMachine)
                info.state = window.mBPSApp.mStateMachine.mCurrentState;
            return info;
        }""")
    except Exception:
        return {"state": None}


def click_play(page, iframe_el, game_frame):
    bbox = iframe_el.bounding_box()
    if not bbox:
        return False
    iw, ih = bbox["width"], bbox["height"]
    for px, py in [(iw*0.5, ih*0.42), (iw*0.5, ih*0.45),
                   (iw*0.5, ih*0.38), (iw*0.5, ih*0.48)]:
        try:
            iframe_el.click(position={"x": px, "y": py})
            time.sleep(1.5)
            if game_frame:
                s = check_game_state(game_frame).get("state")
                if s is not None and s != 7:
                    return True
        except Exception:
            pass
    return False


def load_learning():
    if os.path.exists(LEARNING_FILE):
        with open(LEARNING_FILE) as f:
            return json.load(f)
    return {"games_watched": 0, "total_clears": 0, "total_pieces": 0,
            "clear_events": [], "clears_by_height": {},
            "best_clear_streak": 0, "avg_height_at_clear": 0.0, "insights": []}


def save_learning(data):
    if len(data.get("clear_events", [])) > 100:
        data["clear_events"] = data["clear_events"][-100:]
    with open(LEARNING_FILE, "w") as f:
        json.dump(data, f, indent=2)


def play_tetris():
    print("=" * 60)
    print("  TETRIS BOT v8 - PLAY MODE (smooth)")
    print("=" * 60)
    sys.stdout.flush()

    learning = load_learning()
    print(f"  Brain: {learning['games_watched']} games, "
          f"{learning['total_clears']} clears\n")
    sys.stdout.flush()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 900, "height": 750})
        page = ctx.new_page()

        print("  Opening freetetris.org...")
        sys.stdout.flush()
        page.goto("https://www.freetetris.org/", wait_until="domcontentloaded")
        time.sleep(5)

        iframe_el = get_iframe_element(page)
        if not iframe_el:
            print("  ERROR: No iframe!")
            browser.close()
            return

        # Click iframe to focus it, then wait
        try:
            iframe_el.click()
        except Exception:
            pass
        time.sleep(2)

        game_frame = get_game_frame(page)

        # Click Play
        print("  Starting game...")
        sys.stdout.flush()
        click_play(page, iframe_el, game_frame)
        time.sleep(3)

        # Detect board
        print("  Detecting board...")
        sys.stdout.flush()
        board_bounds = None
        for attempt in range(30):
            time.sleep(1)
            try:
                img = screenshot_iframe(iframe_el)
            except Exception:
                continue
            bounds = find_board_in_iframe(img)
            if bounds:
                x1, y1, x2, y2 = bounds
                cell_w = (x2 - x1) / BOARD_COLS
                cell_h = (y2 - y1) / BOARD_ROWS
                empty = 0
                for row in range(BOARD_ROWS):
                    for col in range(BOARD_COLS):
                        cx = int(x1 + col * cell_w + cell_w * 0.5)
                        cy = int(y1 + row * cell_h + cell_h * 0.5)
                        if 0 <= cx < img.width and 0 <= cy < img.height:
                            r, g, b = img.getpixel((cx, cy))[:3]
                            if is_empty_cell(r, g, b):
                                empty += 1
                if empty > 100:
                    board_bounds = bounds
                    print(f"  BOARD: ({x1},{y1})-({x2},{y2}) "
                          f"cell:{cell_w:.1f}x{cell_h:.1f} empty:{empty}")
                    sys.stdout.flush()
                    break
            if attempt % 5 == 0:
                print(f"  ... scanning ({attempt})")
                sys.stdout.flush()

        if not board_bounds:
            print("  Board not found!")
            browser.close()
            return

        # Focus the iframe canvas for keyboard input
        # Click once in the board area, then DON'T click again
        try:
            iframe_el.click(position={"x": 200, "y": 300})
        except Exception:
            pass
        time.sleep(0.5)

        print("\n" + "=" * 60)
        print("  PLAYING TETRIS!")
        print("=" * 60 + "\n")
        sys.stdout.flush()

        prev_board = read_board(iframe_el, board_bounds)
        pieces_played = 0
        total_clears = 0
        consecutive_empty = 0
        last_move_time = 0

        try:
            while True:
                # Wait between board reads - don't spam screenshots
                time.sleep(0.2)

                try:
                    board = read_board(iframe_el, board_bounds)
                except Exception:
                    time.sleep(1)
                    continue

                filled = count_filled(board)

                # Game over detection: board stays empty for a while
                # or board is completely full at the top
                if filled == 0:
                    consecutive_empty += 1
                    if consecutive_empty > 10 and pieces_played > 0:
                        print(f"\n  GAME OVER!")
                        print(f"    Pieces: {pieces_played}")
                        print(f"    Lines cleared: {total_clears}")
                        sys.stdout.flush()
                        break
                else:
                    consecutive_empty = 0

                # Check if top row is mostly filled (game over)
                top_filled = sum(board[0])
                if top_filled >= 8 and pieces_played > 5:
                    print(f"\n  GAME OVER (topped out)!")
                    print(f"    Pieces: {pieces_played}")
                    print(f"    Lines cleared: {total_clears}")
                    sys.stdout.flush()
                    break

                # Detect new piece
                piece_type, new_cells = detect_piece(prev_board, board)

                # Rate limit: wait at least 0.3s between moves
                now = time.time()
                if piece_type and piece_type != "?" and len(new_cells) == 4:
                    if now - last_move_time < 0.3:
                        prev_board = [r[:] for r in board]
                        continue

                    pieces_played += 1

                    # Board without the falling piece
                    clean_board = [r[:] for r in board]
                    for r, c in new_cells:
                        clean_board[r][c] = 0

                    # AI decision
                    rot, col, score = find_best_move(clean_board, piece_type)
                    spawn_col = round(sum(c for _, c in new_cells) / len(new_cells))

                    heights = get_column_heights(clean_board)
                    max_h = max(heights) if heights else 0
                    holes = count_holes(clean_board)

                    print(f"  #{pieces_played:3d} {piece_type} -> "
                          f"rot:{rot} col:{col} "
                          f"H:{max_h} holes:{holes} "
                          f"(score:{score:.1f})")
                    sys.stdout.flush()

                    # Execute the move with gentle timing
                    execute_move(page, rot, col, spawn_col)
                    last_move_time = time.time()

                    # Wait for piece to drop and settle
                    time.sleep(0.4)

                    # Read post-drop board to detect clears
                    try:
                        post = read_board(iframe_el, board_bounds)
                        post_filled = count_filled(post)
                        expected = count_filled(clean_board) + 4
                        if post_filled < expected - 5:
                            lines = max(1, (expected - post_filled) // BOARD_COLS)
                            total_clears += lines
                            label = {1: "SINGLE", 2: "DOUBLE", 3: "TRIPLE",
                                     4: "TETRIS!!"}.get(lines, f"{lines}x")
                            print(f"   *** {label}! (total: {total_clears})")
                            sys.stdout.flush()
                        board = post
                    except Exception:
                        pass

                    # Save periodically
                    if pieces_played % 20 == 0:
                        learning["total_pieces"] = (
                            learning.get("total_pieces", 0) + 20)
                        learning["total_clears"] = (
                            learning.get("total_clears", 0) + total_clears)
                        save_learning(learning)

                prev_board = [r[:] for r in board]

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n  Error: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
        finally:
            learning["games_watched"] = learning.get("games_watched", 0) + 1
            learning["total_clears"] = learning.get("total_clears", 0) + total_clears
            learning["total_pieces"] = learning.get("total_pieces", 0) + pieces_played
            save_learning(learning)
            print(f"\n  Saved. Lifetime: {learning['total_clears']} clears")
            sys.stdout.flush()
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    play_tetris()
