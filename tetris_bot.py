"""Tetris Bot v10 - PLAY MODE with slow-paced screenshots.

Takes exactly ONE screenshot per piece cycle (~2s apart).
This eliminates the seizure caused by rapid screenshot spam.
Flow: screenshot -> detect piece -> AI decide -> execute keys -> wait -> repeat
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

EMPTY_CELL_COLOR = (198, 216, 242)
PAGE_BG_COLOR = (220, 238, 255)

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

W_LINES = 10.0
W_HOLES = -0.75
W_BUMP = -0.18
W_HEIGHT = -0.5


def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def is_empty_cell(r, g, b):
    return color_distance((r, g, b), EMPTY_CELL_COLOR) < 30


def is_filled_cell(r, g, b):
    """Detect piece cells by saturation. Tetris pieces are highly saturated
    (max-min > 100): blue, green, red, cyan, yellow, orange, purple.
    Empty cells, grid lines, borders are all desaturated (max-min < 50)."""
    mx = max(r, g, b)
    mn = min(r, g, b)
    saturation = mx - mn
    # All piece colors have saturation > 150, all non-pieces < 50
    return saturation > 80 and mx > 100


def screenshot_iframe(page, iframe_el):
    """Take a FULL PAGE screenshot and crop to iframe region.
    This avoids the flicker/seizure caused by iframe_el.screenshot()."""
    box = iframe_el.bounding_box()
    if not box:
        return None
    data = page.screenshot(type="png")
    full = Image.open(io.BytesIO(data))
    x, y, w, h = int(box['x']), int(box['y']), int(box['width']), int(box['height'])
    return full.crop((x, y, x + w, y + h))


def find_board_in_iframe(img):
    w, h = img.size
    max_x = int(w * 0.65)
    empty_xs, empty_ys = [], []
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


def read_board(img, bounds):
    """Read board state from a screenshot image. No new screenshot taken."""
    x1, y1, x2, y2 = bounds
    cell_w = (x2 - x1) / BOARD_COLS
    cell_h = (y2 - y1) / BOARD_ROWS
    board = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            cx = int(x1 + col * cell_w + cell_w * 0.5)
            cy = int(y1 + row * cell_h + cell_h * 0.5)
            filled = 0
            # Sample 5 points: center + 4 offsets (stay well inside cell)
            for dx, dy in [(0, 0),
                           (int(cell_w * 0.25), 0),
                           (-int(cell_w * 0.25), 0),
                           (0, int(cell_h * 0.25)),
                           (0, -int(cell_h * 0.25))]:
                px, py = cx + dx, cy + dy
                if 0 <= px < img.width and 0 <= py < img.height:
                    r, g, b = img.getpixel((px, py))[:3]
                    if is_filled_cell(r, g, b):
                        filled += 1
            if filled >= 3:
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


def detect_piece_single(board):
    """Find an active tetromino in the board (single snapshot, no diff).
    Scans from top down for groups of exactly 4 connected filled cells
    that match a known tetromino shape AND float above the stack."""
    # Collect all filled cells
    all_filled = []
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col]:
                all_filled.append((row, col))
    if len(all_filled) < 4:
        return None, []

    groups = find_connected_groups(all_filled)
    # Sort groups by their topmost row (ascending = highest first)
    groups.sort(key=lambda g: min(r for r, c in g))

    for group in groups:
        if len(group) != 4:
            continue
        min_r = min(r for r, c in group)
        min_c = min(c for r, c in group)
        normalized = tuple(sorted((r - min_r, c - min_c) for r, c in group))
        for ptype, rotations in PIECES.items():
            for cells in rotations:
                if tuple(sorted(cells)) == normalized:
                    # Check that this group has empty space below it
                    # (i.e., it's not resting on the bottom or other pieces)
                    max_r = max(r for r, c in group)
                    if max_r < BOARD_ROWS - 1:
                        below_empty = False
                        for r, c in group:
                            if r == max_r and (r + 1 < BOARD_ROWS):
                                if not board[r + 1][c]:
                                    below_empty = True
                        if below_empty:
                            return ptype, list(group)
                    # If near top (row < 4), accept it even without gap below
                    if min_r < 4:
                        return ptype, list(group)
    return None, []


def find_connected_groups(cells):
    """Find groups of connected cells (4-connected)."""
    cell_set = set(cells)
    visited = set()
    groups = []
    for cell in cells:
        if cell in visited:
            continue
        group = []
        stack = [cell]
        while stack:
            c = stack.pop()
            if c in visited:
                continue
            visited.add(c)
            group.append(c)
            r, col = c
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nb = (r+dr, col+dc)
                if nb in cell_set and nb not in visited:
                    stack.append(nb)
        groups.append(group)
    return groups


def execute_move(page, iframe_el, rotation, target_col, spawn_col):
    """Click iframe for focus, then send keys via page.keyboard."""
    try:
        iframe_el.click(position={"x": 200, "y": 300})
    except Exception:
        pass
    time.sleep(0.05)
    for _ in range(rotation):
        page.keyboard.press("ArrowUp")
        time.sleep(0.08)
    diff = target_col - spawn_col
    key = "ArrowRight" if diff > 0 else "ArrowLeft"
    for _ in range(abs(diff)):
        page.keyboard.press(key)
        time.sleep(0.08)
    time.sleep(0.05)
    page.keyboard.press("Space")


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
    print("  TETRIS BOT v10 - PAGE SCREENSHOT + IFRAME KEYS")
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

        iframe_el = page.query_selector("#gameIFrame")
        if not iframe_el:
            print("  ERROR: No iframe!")
            browser.close()
            return

        try:
            iframe_el.click()
        except Exception:
            pass
        time.sleep(2)

        print("  >>> Click PLAY in the game window! <<<")
        print("  Waiting for board to appear...")
        sys.stdout.flush()

        # Wait for user to start game + detect board
        board_bounds = None
        for attempt in range(120):
            time.sleep(1)
            iframe_el = page.query_selector("#gameIFrame")
            if not iframe_el:
                continue
            try:
                img = screenshot_iframe(page, iframe_el)
                if img is None:
                    continue
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
                    print(f"  BOARD found: ({x1},{y1})-({x2},{y2}) "
                          f"cell:{cell_w:.1f}x{cell_h:.1f}")
                    sys.stdout.flush()
                    break
            if attempt % 10 == 0 and attempt > 0:
                print(f"  ... still waiting ({attempt}s)")
                sys.stdout.flush()

        if not board_bounds:
            print("  Board not found after 2min!")
            browser.close()
            return

        # Re-fetch iframe element and focus it for keyboard
        iframe_el = page.query_selector("#gameIFrame")
        try:
            iframe_el.click(position={"x": 200, "y": 300})
        except Exception:
            pass
        time.sleep(0.5)

        print("  Using page.keyboard for key input (iframe focused)")

        print("\n" + "=" * 60)
        print("  PLAYING TETRIS!")
        print("=" * 60 + "\n")
        sys.stdout.flush()

        # Take initial board snapshot (for line clear tracking)
        try:
            img = screenshot_iframe(page, iframe_el)
            settled_board = read_board(img, board_bounds) if img else [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]
            init_filled = count_filled(settled_board)
            print(f"  Initial board: {init_filled} filled cells")
            if init_filled > 0:
                for row in range(BOARD_ROWS):
                    cols = [c for c in range(BOARD_COLS) if settled_board[row][c]]
                    if cols:
                        print(f"    row {row:2d}: cols {cols}")
            sys.stdout.flush()
        except Exception:
            settled_board = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]

        pieces_played = 0
        total_clears = 0
        no_piece_count = 0
        last_action_time = time.time()

        try:
            while True:
                # === Poll interval: 0.4s (page screenshot = no seizure) ===
                time.sleep(0.4)

                iframe_el = page.query_selector("#gameIFrame")
                if not iframe_el:
                    print("  iframe lost!")
                    break

                try:
                    img = screenshot_iframe(page, iframe_el)
                    if img is None:
                        iframe_el = page.query_selector("#gameIFrame")
                        continue
                    board = read_board(img, board_bounds)
                except Exception as e:
                    print(f"  screenshot error: {e}")
                    sys.stdout.flush()
                    continue

                filled = count_filled(board)

                # === Game over check ===
                top_filled = sum(board[0])
                if top_filled >= 8 and pieces_played > 5:
                    print(f"\n  GAME OVER (topped out)!")
                    break

                # Don't act too fast after last move (let piece land)
                elapsed = time.time() - last_action_time
                if elapsed < 0.6:
                    continue

                # === Detect piece in single snapshot ===
                piece_type, new_cells = detect_piece_single(board)

                if piece_type:
                    no_piece_count = 0
                    pieces_played += 1

                    # Board without the active piece
                    clean_board = [r[:] for r in board]
                    for r, c in new_cells:
                        clean_board[r][c] = 0

                    # === AI decides best move ===
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

                    # === Execute the move ===
                    execute_move(page, iframe_el, rot, col, spawn_col)
                    last_action_time = time.time()

                    # Wait for piece to land, then snapshot clean board
                    time.sleep(0.5)
                    try:
                        iframe_el = page.query_selector("#gameIFrame")
                        if iframe_el:
                            post_img = screenshot_iframe(page, iframe_el)
                            post_board = read_board(post_img, board_bounds) if post_img else None
                            if post_board:
                                post_filled = count_filled(post_board)
                                expected = count_filled(clean_board) + 4
                                if post_filled < expected - 5:
                                    lines = max(1, (expected - post_filled) // BOARD_COLS)
                                    total_clears += lines
                                    label = {1: "SINGLE", 2: "DOUBLE",
                                             3: "TRIPLE", 4: "TETRIS!!"}.get(
                                        lines, f"{lines}x")
                                    print(f"   *** {label}! "
                                          f"(total: {total_clears})")
                                    sys.stdout.flush()
                                settled_board = post_board
                            else:
                                settled_board = clean_board
                        else:
                            settled_board = clean_board
                    except Exception:
                        settled_board = clean_board

                    # Save periodically
                    if pieces_played % 20 == 0:
                        learning["total_pieces"] = (
                            learning.get("total_pieces", 0) + 20)
                        save_learning(learning)
                else:
                    no_piece_count += 1

                    if no_piece_count % 20 == 0 and no_piece_count > 0:
                        print(f"  ... waiting for piece "
                              f"(filled:{filled} polls:{no_piece_count})")
                        sys.stdout.flush()

                    if no_piece_count > 120 and pieces_played > 0:
                        print(f"\n  GAME OVER (no new pieces for 30s)!")
                        break

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n  Error: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
        finally:
            print(f"\n  Result: {pieces_played} pieces, "
                  f"{total_clears} clears")
            learning["games_watched"] = (
                learning.get("games_watched", 0) + 1)
            learning["total_clears"] = (
                learning.get("total_clears", 0) + total_clears)
            learning["total_pieces"] = (
                learning.get("total_pieces", 0) + pieces_played)
            save_learning(learning)
            print(f"  Saved. Lifetime: {learning['total_clears']} clears")
            sys.stdout.flush()
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    play_tetris()
