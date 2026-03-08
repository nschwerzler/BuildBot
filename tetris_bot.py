"""Tetris Bot v6 - Watch Mode with Iframe-Based Detection.

Opens freetetris.org, clicks Play to start game,
detects board from IFRAME screenshots (not full page),
then watches and learns from gameplay.
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

# Board empty cell color (confirmed from pixel analysis)
EMPTY_CELL_COLOR = (198, 216, 242)
PAGE_BG_COLOR = (220, 238, 255)

# Known board proportions within iframe (728x600):
# Board is left ~55%, cells ~39x23px
FALLBACK_BOARD = {
    "left_frac": 0.015,
    "right_frac": 0.55,
    "top_frac": 0.01,
    "bottom_frac": 0.78,
}


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


def get_game_frame(page):
    for f in page.frames:
        if f.name == "gameIFrame":
            return f
    el = page.query_selector("#gameIFrame")
    if el:
        return el.content_frame()
    return None


def get_iframe_element(page):
    return page.query_selector("#gameIFrame")


def screenshot_iframe(iframe_el):
    data = iframe_el.screenshot()
    return Image.open(io.BytesIO(data))


def find_board_in_iframe(img):
    """Find board by scanning for empty-cell colored pixels in left 65% of iframe."""
    w, h = img.size
    max_x = int(w * 0.65)

    empty_xs = []
    empty_ys = []
    step = 4

    for y in range(0, h, step):
        for x in range(0, max_x, step):
            r, g, b = img.getpixel((x, y))[:3]
            if is_empty_cell(r, g, b):
                empty_xs.append(x)
                empty_ys.append(y)

    if len(empty_xs) < 50:
        return None

    empty_xs.sort()
    empty_ys.sort()

    trim = max(1, len(empty_xs) // 20)
    left = empty_xs[trim]
    right = empty_xs[-trim]
    top = empty_ys[trim]
    bottom = empty_ys[-trim]

    width = right - left
    height = bottom - top

    if width < 100 or height < 200:
        return None

    cell_w = width / BOARD_COLS
    cell_h = height / BOARD_ROWS
    if cell_w < 15 or cell_w > 80 or cell_h < 10 or cell_h > 50:
        return None

    return (left, top, right, bottom)


def find_board_fallback(img):
    w, h = img.size
    fb = FALLBACK_BOARD
    return (int(w * fb["left_frac"]), int(h * fb["top_frac"]),
            int(w * fb["right_frac"]), int(h * fb["bottom_frac"]))


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

            filled_count = 0
            offsets = [(0, 0), (int(cell_w * 0.2), 0),
                       (0, int(cell_h * 0.2)), (-int(cell_w * 0.2), 0)]
            for dx, dy in offsets:
                px, py = cx + dx, cy + dy
                if 0 <= px < img.width and 0 <= py < img.height:
                    r, g, b = img.getpixel((px, py))[:3]
                    if is_filled_cell(r, g, b):
                        filled_count += 1

            if filled_count >= 2:
                board[row][col] = 1

    return board


def get_column_heights(board):
    heights = []
    for col in range(BOARD_COLS):
        h = 0
        for row in range(BOARD_ROWS):
            if board[row][col]:
                h = BOARD_ROWS - row
                break
        heights.append(h)
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


def detect_changes(old_board, new_board):
    new_cells = []
    removed = []
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if new_board[row][col] and not old_board[row][col]:
                new_cells.append((row, col))
            elif old_board[row][col] and not new_board[row][col]:
                removed.append((row, col))
    return new_cells, removed


def load_learning():
    if os.path.exists(LEARNING_FILE):
        with open(LEARNING_FILE) as f:
            return json.load(f)
    return {
        "games_watched": 0,
        "total_clears": 0,
        "total_pieces": 0,
        "clear_events": [],
        "clears_by_height": {},
        "best_clear_streak": 0,
        "avg_height_at_clear": 0.0,
        "insights": [],
    }


def save_learning(data):
    if len(data.get("clear_events", [])) > 50:
        data["clear_events"] = data["clear_events"][-50:]
    with open(LEARNING_FILE, "w") as f:
        json.dump(data, f, indent=2)


def check_game_state(game_frame):
    try:
        return game_frame.evaluate("""() => {
            const info = {playing: false, state: null};
            if (typeof window.mBPSApp !== 'undefined' && window.mBPSApp.mStateMachine) {
                info.state = window.mBPSApp.mStateMachine.mCurrentState;
                info.prev_state = window.mBPSApp.mStateMachine.mPreviousState;
            }
            return info;
        }""")
    except Exception:
        return {"playing": False, "state": None}


def click_play_button(page, iframe_el, game_frame):
    """Click the Play button on the Cocos Creator canvas."""
    bbox = iframe_el.bounding_box()
    if not bbox:
        return False

    iw = bbox["width"]
    ih = bbox["height"]

    # Play button is centered horizontally, upper-middle area
    positions = [
        (iw * 0.5, ih * 0.42),
        (iw * 0.5, ih * 0.45),
        (iw * 0.5, ih * 0.38),
        (iw * 0.5, ih * 0.48),
        (iw * 0.5, ih * 0.35),
    ]

    for px, py in positions:
        try:
            iframe_el.click(position={"x": px, "y": py})
            print(f"  Clicked ({px:.0f}, {py:.0f})")
            sys.stdout.flush()
            time.sleep(1.5)

            if game_frame:
                state = check_game_state(game_frame)
                s = state.get("state")
                if s is not None and s != 7:
                    print(f"  State changed: {s}")
                    sys.stdout.flush()
                    return True
        except Exception as e:
            print(f"  Click err: {e}")
            sys.stdout.flush()

    return False


def watch_tetris():
    print("=" * 60)
    print("  TETRIS WATCH BOT v6 - Auto Start + Iframe Detection")
    print("=" * 60)
    sys.stdout.flush()

    learning = load_learning()
    print(f"\n  Brain: {learning['games_watched']} games, "
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
            print("  ERROR: No iframe found!")
            browser.close()
            return

        try:
            iframe_el.click()
        except Exception:
            pass
        time.sleep(2)

        game_frame = get_game_frame(page)

        # Initial screenshot
        img = screenshot_iframe(iframe_el)
        img.save(DEBUG_IMG)
        print(f"  Iframe size: {img.size}")
        sys.stdout.flush()

        # Color samples across iframe
        w, h = img.size
        for frac in [0.1, 0.25, 0.4, 0.5, 0.6, 0.75]:
            x = int(w * frac)
            c = img.getpixel((x, h // 2))[:3]
            print(f"    x={x} ({frac:.0%}): RGB{c} empty={is_empty_cell(*c)}")
        sys.stdout.flush()

        # Click Play
        print("\n  Clicking Play button...")
        sys.stdout.flush()
        click_play_button(page, iframe_el, game_frame)
        time.sleep(3)

        # Scan for board
        print("\n  Scanning for board...")
        sys.stdout.flush()

        board_bounds = None
        for attempt in range(60):
            time.sleep(1)
            try:
                img = screenshot_iframe(iframe_el)
            except Exception:
                continue

            if attempt == 0:
                img.save(DEBUG_IMG)
                print(f"  Post-click iframe: {img.size}")
                for frac in [0.1, 0.25, 0.4, 0.5, 0.6]:
                    x = int(img.width * frac)
                    c = img.getpixel((x, img.height // 2))[:3]
                    print(f"    x={x}: RGB{c} empty={is_empty_cell(*c)}")
                sys.stdout.flush()

            bounds = find_board_in_iframe(img)
            if bounds:
                x1, y1, x2, y2 = bounds
                cell_w = (x2 - x1) / BOARD_COLS
                cell_h = (y2 - y1) / BOARD_ROWS

                empty_count = 0
                for row in range(BOARD_ROWS):
                    for col in range(BOARD_COLS):
                        cx = int(x1 + col * cell_w + cell_w * 0.5)
                        cy = int(y1 + row * cell_h + cell_h * 0.5)
                        if 0 <= cx < img.width and 0 <= cy < img.height:
                            r, g, b = img.getpixel((cx, cy))[:3]
                            if is_empty_cell(r, g, b):
                                empty_count += 1

                if empty_count > 100:
                    board_bounds = bounds
                    print(f"\n  BOARD FOUND! ({x1},{y1})-({x2},{y2})")
                    print(f"    Cell: {cell_w:.1f}x{cell_h:.1f}px")
                    print(f"    Empty: {empty_count}/200")
                    sys.stdout.flush()
                    break
                elif attempt % 5 == 0:
                    print(f"  ... region found, {empty_count} empty (need >100)")
                    sys.stdout.flush()
            elif attempt % 5 == 0:
                print(f"  ... scanning (attempt {attempt})")
                sys.stdout.flush()

        if not board_bounds:
            print("  Using fallback proportions...")
            board_bounds = find_board_fallback(img)
            x1, y1, x2, y2 = board_bounds
            print(f"  Fallback: ({x1},{y1})-({x2},{y2})")
            sys.stdout.flush()

        # Debug image with grid overlay
        from PIL import ImageDraw
        debug_img = screenshot_iframe(iframe_el)
        draw = ImageDraw.Draw(debug_img)
        x1, y1, x2, y2 = board_bounds
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        cell_w = (x2 - x1) / BOARD_COLS
        cell_h = (y2 - y1) / BOARD_ROWS
        for col in range(BOARD_COLS + 1):
            gx = int(x1 + col * cell_w)
            draw.line([(gx, y1), (gx, y2)], fill="red", width=1)
        for row in range(BOARD_ROWS + 1):
            gy = int(y1 + row * cell_h)
            draw.line([(x1, gy), (x2, gy)], fill="red", width=1)
        debug_img.save(DEBUG_IMG)
        print(f"  Debug image saved: {DEBUG_IMG}")
        sys.stdout.flush()

        # Watch game
        print("\n" + "=" * 60)
        print("  WATCHING! Play Tetris - I'm learning.")
        print("=" * 60 + "\n")
        sys.stdout.flush()

        prev_board = None
        prev_filled = 0
        game_active = False
        pieces_this_game = 0
        clears_this_game = 0
        clear_streak = 0
        max_clear_streak = 0
        last_board_str = None
        stale_count = 0
        save_counter = 0

        try:
            while True:
                try:
                    board = read_board(iframe_el, board_bounds)
                except Exception:
                    time.sleep(0.5)
                    continue

                filled = count_filled(board)
                board_str = str(board)

                if board_str == last_board_str:
                    stale_count += 1
                    if stale_count > 200:
                        stale_count = 0
                        try:
                            img = screenshot_iframe(iframe_el)
                            nb = find_board_in_iframe(img)
                            if nb:
                                board_bounds = nb
                                print("  (Re-calibrated)")
                                sys.stdout.flush()
                        except Exception:
                            pass
                    time.sleep(0.08)
                    continue

                stale_count = 0
                last_board_str = board_str

                if not game_active and 0 < filled < 20:
                    game_active = True
                    pieces_this_game = 0
                    clears_this_game = 0
                    clear_streak = 0
                    max_clear_streak = 0
                    learning["games_watched"] += 1
                    print(f"  >>> GAME STARTED (#{learning['games_watched']})")
                    sys.stdout.flush()

                if prev_board is not None and game_active:
                    new_cells, removed_cells = detect_changes(prev_board, board)
                    heights = get_column_heights(board)
                    holes = count_holes(board)
                    max_h = max(heights) if heights else 0

                    if 2 <= len(new_cells) <= 8 and len(removed_cells) == 0:
                        pieces_this_game += 1
                        learning["total_pieces"] += 1

                        if pieces_this_game % 5 == 0:
                            print(f"  Piece #{pieces_this_game:3d} | "
                                  f"H:{max_h:2d} | "
                                  f"Holes:{holes:2d} | "
                                  f"Clears:{clears_this_game}")
                            sys.stdout.flush()

                    if len(removed_cells) >= BOARD_COLS:
                        lines = len(removed_cells) // BOARD_COLS
                        if lines > 0:
                            clears_this_game += lines
                            learning["total_clears"] += lines
                            clear_streak += lines
                            if clear_streak > max_clear_streak:
                                max_clear_streak = clear_streak
                            if clear_streak > learning["best_clear_streak"]:
                                learning["best_clear_streak"] = clear_streak

                            prev_heights = get_column_heights(prev_board)
                            prev_max_h = max(prev_heights) if prev_heights else 0
                            prev_holes = count_holes(prev_board)

                            h_bucket = str((prev_max_h // 5) * 5)
                            learning["clears_by_height"][h_bucket] = \
                                learning["clears_by_height"].get(h_bucket, 0) + lines

                            event = {
                                "lines": lines,
                                "height": prev_max_h,
                                "holes": prev_holes,
                                "piece_num": pieces_this_game,
                            }
                            learning["clear_events"].append(event)

                            n = len(learning["clear_events"])
                            learning["avg_height_at_clear"] = (
                                learning["avg_height_at_clear"] * (n - 1) + prev_max_h
                            ) / n

                            label = {1: "SINGLE", 2: "DOUBLE", 3: "TRIPLE",
                                     4: "TETRIS!!"}.get(lines, f"{lines}x")
                            print(f"  {'*' * lines} LINE CLEAR: {label}! "
                                  f"(game:{clears_this_game} total:{learning['total_clears']})")
                            sys.stdout.flush()
                    elif len(new_cells) > 0:
                        clear_streak = 0

                    if filled == 0 and prev_filled > 20:
                        game_active = False
                        print(f"\n  >>> GAME OVER!")
                        print(f"      Pieces: {pieces_this_game}")
                        print(f"      Clears: {clears_this_game}")
                        print(f"      Streak: {max_clear_streak}")
                        print(f"      Total clears: {learning['total_clears']}")

                        if learning["total_clears"] > 0:
                            print(f"  INSIGHTS:")
                            print(f"      Avg height at clear: "
                                  f"{learning['avg_height_at_clear']:.1f}")
                            if learning["clears_by_height"]:
                                best = max(learning["clears_by_height"],
                                           key=lambda k: learning["clears_by_height"][k])
                                print(f"      Most clears at height ~{best}")

                        save_learning(learning)
                        print(f"  Brain saved!\n")
                        sys.stdout.flush()

                prev_board = [row[:] for row in board]
                prev_filled = filled

                save_counter += 1
                if save_counter >= 200:
                    save_counter = 0
                    save_learning(learning)

                time.sleep(0.05)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n  Error: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
        finally:
            save_learning(learning)
            print(f"\n  Session ended. Games: {learning['games_watched']}, "
                  f"Clears: {learning['total_clears']}")
            sys.stdout.flush()
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    watch_tetris()
