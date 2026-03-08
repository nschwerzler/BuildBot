"""
Tetris AI Bot v2 - Direct Playwright control with calibration-based vision
Plays Tetris N-Blox on freetetris.org
Learns from mistakes: calibrates board position, validates piece detection

WORKFLOW: Player (d0g3) handles all menu buttons — Play, New Game, level select.
Bot waits for the game to be running, then takes over piece placement.
"""
import time
import math
import json
import os
from playwright.sync_api import sync_playwright
from PIL import Image
import io

BOARD_COLS = 10
BOARD_ROWS = 20
CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), 'tetris_calibration.json')

# Piece shapes: each piece has list of rotations, each rotation is list of (row, col) offsets
PIECES = {
    'I': [[(0,0),(0,1),(0,2),(0,3)], [(0,0),(1,0),(2,0),(3,0)]],
    'O': [[(0,0),(0,1),(1,0),(1,1)]],
    'T': [[(0,0),(0,1),(0,2),(1,1)], [(0,0),(1,0),(1,1),(2,0)],
           [(0,1),(1,0),(1,1),(1,2)], [(0,0),(1,0),(1,-1),(2,0)]],
    'S': [[(0,1),(0,2),(1,0),(1,1)], [(0,0),(1,0),(1,1),(2,1)]],
    'Z': [[(0,0),(0,1),(1,1),(1,2)], [(0,1),(1,0),(1,1),(2,0)]],
    'J': [[(0,0),(1,0),(1,1),(1,2)], [(0,0),(0,1),(1,0),(2,0)],
           [(0,0),(0,1),(0,2),(1,2)], [(0,0),(1,0),(2,0),(2,-1)]],
    'L': [[(0,2),(1,0),(1,1),(1,2)], [(0,0),(1,0),(2,0),(2,1)],
           [(0,0),(0,1),(0,2),(1,0)], [(0,0),(0,1),(1,1),(2,1)]],
}


def identify_piece_color(r, g, b):
    """Identify which Tetris piece a color belongs to"""
    if is_empty_cell(r, g, b):
        return None
    # Check if it's dark enough to be a piece


# ── BOARD READING ──────────────────────────────────────────────

def is_filled_cell(r, g, b, bg_color):
    """Check if pixel is a filled block vs empty background"""
    br, bg, bb = bg_color
    # If the color differs significantly from background, it's filled
    dist = math.sqrt((r - br)**2 + (g - bg)**2 + (b - bb)**2)
    return dist > 60


def calibrate_board(page):
    """Calibrate board position using N-Blox's known proportional layout."""
    
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE) as f:
            cal = json.load(f)
            print(f"Loaded calibration: board at ({cal['x1']},{cal['y1']}) to ({cal['x2']},{cal['y2']})")
            return cal
    
    print("Calibrating board position...")
    iframe_el = page.query_selector('#gameIFrame')
    if not iframe_el:
        return None
    
    box = iframe_el.bounding_box()
    if not box:
        return None
    
    screenshot = page.screenshot()
    img = Image.open(io.BytesIO(screenshot))
    w, h = img.size
    
    img.save(os.path.join(os.path.dirname(__file__), 'tetris_debug.png'))
    
    ix, iy = int(box['x']), int(box['y'])
    iw, ih = int(box['width']), int(box['height'])
    print(f"Debug screenshot saved. Page: {w}x{h}, iframe at ({ix},{iy}) size {iw}x{ih}")
    
    # N-Blox known layout proportions within the game iframe:
    # Board occupies roughly left 45% of iframe width, and ~95% of height
    # with small borders on each side
    # The board has 10 cols, 20 rows
    
    # Use pixel sampling to find exact board edges
    # Strategy: scan a horizontal line in the middle of iframe.
    # The board interior is lighter than the dark borders.
    # We want to find the INTERIOR area (excluding dark borders).
    
    mid_y = iy + ih // 2
    
    # Scan horizontal at mid_y through left 55% of iframe
    scan_end = ix + int(iw * 0.55)
    
    # Find transitions: look for first block of light pixels (board interior)
    in_board = False
    board_left = None
    board_right = None
    
    # First, sample what "light" looks like in the board area
    # The board cells are either empty (~200,205,220 light blue) or filled (colored)
    for x in range(ix, scan_end):
        if x >= w:
            break
        r, g, b = img.getpixel((x, mid_y))[:3]
        brightness = (r + g + b) / 3
        
        if not in_board:
            # Look for start of board interior (light area after dark border)
            if brightness > 150:
                board_left = x
                in_board = True
        else:
            # Look for end of board (dark border on right side)
            if brightness < 100:
                board_right = x - 1
                break
    
    if not board_right:
        board_right = scan_end
    
    # Now scan vertical at the center of found board area
    board_mid_x = (board_left + board_right) // 2 if board_left else ix + iw // 4
    board_top = None
    board_bottom = None
    in_board_v = False
    
    for y in range(iy, iy + ih):
        if y >= h:
            break
        r, g, b = img.getpixel((board_mid_x, y))[:3]
        brightness = (r + g + b) / 3
        
        if not in_board_v:
            if brightness > 150:
                board_top = y
                in_board_v = True
        else:
            if brightness < 100:
                board_bottom = y - 1
                break
    
    if not board_bottom:
        board_bottom = iy + ih - 5
    
    # Fallback if detection failed
    if not board_left or not board_top:
        print("Edge detection failed. Using proportional estimates.")
        board_left = ix + int(iw * 0.01)
        board_right = ix + int(iw * 0.44)
        board_top = iy + int(ih * 0.01)
        board_bottom = iy + int(ih * 0.98)
    
    # Sample background color from empty area of board
    bg_x = board_left + (board_right - board_left) // 2
    bg_y = board_top + 10  # top part likely empty at game start
    bg_color = list(img.getpixel((bg_x, bg_y))[:3])
    
    cell_w = (board_right - board_left) / BOARD_COLS
    cell_h = (board_bottom - board_top) / BOARD_ROWS
    
    cal = {
        'x1': board_left, 'y1': board_top,
        'x2': board_right, 'y2': board_bottom,
        'bg_color': bg_color,
        'iframe_x': ix, 'iframe_y': iy,
        'iframe_w': iw, 'iframe_h': ih
    }
    
    print(f"Board: ({board_left},{board_top}) to ({board_right},{board_bottom})")
    print(f"Cell size: {cell_w:.1f} x {cell_h:.1f} px")
    print(f"Background color: {bg_color}")
    
    with open(CALIBRATION_FILE, 'w') as f:
        json.dump(cal, f, indent=2)
    
    return cal


def read_board(page, cal):
    """Read board state from a fresh screenshot using calibration data"""
    screenshot = page.screenshot()
    img = Image.open(io.BytesIO(screenshot))
    
    x1, y1 = cal['x1'], cal['y1']
    x2, y2 = cal['x2'], cal['y2']
    bg_color = tuple(cal['bg_color'])
    
    cell_w = (x2 - x1) / BOARD_COLS
    cell_h = (y2 - y1) / BOARD_ROWS
    
    board = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]
    colors = [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]
    
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            # Sample center of cell
            px = int(x1 + col * cell_w + cell_w * 0.5)
            py = int(y1 + row * cell_h + cell_h * 0.5)
            
            r, g, b = img.getpixel((px, py))[:3]
            if is_filled_cell(r, g, b, bg_color):
                board[row][col] = 1
                colors[row][col] = (r, g, b)
    
    return board, colors


def separate_falling_piece(board, colors, prev_board):
    """Separate falling piece from locked-down blocks.
    
    Strategy: compare with previous board. Cells that are new and 
    in the top portion are likely the falling piece. If no prev_board,
    assume top 4 rows contain the falling piece.
    """
    piece_cells = []
    static_board = [row[:] for row in board]
    
    if prev_board:
        # New cells that weren't in the previous board = falling piece
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if board[row][col] and not prev_board[row][col]:
                    piece_cells.append((row, col))
        
        # Sanity: falling piece should be 4 cells
        if len(piece_cells) == 4:
            for r, c in piece_cells:
                static_board[r][c] = 0
            return piece_cells, static_board
    
    # Fallback: look at top portion of board for exactly 4 connected cells
    # Find the highest filled row
    top_row = BOARD_ROWS
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col]:
                top_row = row
                break
        if top_row < BOARD_ROWS:
            break
    
    # If we can find 4 cells near the top with the same color, that's the piece
    if colors:
        for row in range(min(top_row, BOARD_ROWS - 4), min(top_row + 5, BOARD_ROWS)):
            for col in range(BOARD_COLS):
                if board[row][col] and colors[row][col]:
                    target_color = colors[row][col]
                    group = [(row, col)]
                    # BFS for same-color neighbors
                    visited = {(row, col)}
                    queue = [(row, col)]
                    while queue:
                        cr, cc = queue.pop(0)
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = cr+dr, cc+dc
                            if (nr,nc) not in visited and 0 <= nr < BOARD_ROWS and 0 <= nc < BOARD_COLS:
                                if board[nr][nc] and colors[nr][nc]:
                                    cdist = math.sqrt(sum((a-b)**2 for a,b in zip(colors[nr][nc], target_color)))
                                    if cdist < 50:
                                        visited.add((nr, nc))
                                        group.append((nr, nc))
                                        queue.append((nr, nc))
                    
                    if len(group) == 4:
                        # Likely the falling piece
                        for r, c in group:
                            static_board[r][c] = 0
                        return group, static_board
    
    # Last fallback: top 4 rows
    for row in range(6):
        for col in range(BOARD_COLS):
            if board[row][col]:
                piece_cells.append((row, col))
    
    if len(piece_cells) >= 4:
        piece_cells = piece_cells[:4]
        for r, c in piece_cells:
            static_board[r][c] = 0
    
    return piece_cells, static_board


def identify_piece_type(cells):
    """Identify piece type from cell positions"""
    if len(cells) != 4:
        return None
    
    min_r = min(r for r, c in cells)
    min_c = min(c for r, c in cells)
    normalized = tuple(sorted((r - min_r, c - min_c) for r, c in cells))
    
    for piece_type, rotations in PIECES.items():
        for shape in rotations:
            if tuple(sorted(shape)) == normalized:
                return piece_type
    return None


# ── AI EVALUATION ──────────────────────────────────────────────

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
        found_block = False
        for row in range(BOARD_ROWS):
            if board[row][col]:
                found_block = True
            elif found_block:
                holes += 1
    return holes


def get_bumpiness(heights):
    return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights) - 1))


def simulate_drop(board, shape, col_offset):
    """Drop a piece shape at col_offset and return resulting board, or None if invalid"""
    for dr, dc in shape:
        c = col_offset + dc
        if c < 0 or c >= BOARD_COLS:
            return None
    
    # Find landing row
    land_row = -1
    for test_row in range(BOARD_ROWS):
        ok = True
        for dr, dc in shape:
            r, c = test_row + dr, col_offset + dc
            if r >= BOARD_ROWS or (0 <= r < BOARD_ROWS and board[r][c]):
                ok = False
                break
        if not ok:
            land_row = test_row - 1
            break
    else:
        land_row = BOARD_ROWS - 1 - max(dr for dr, dc in shape)
    
    if land_row < 0:
        return None
    
    new_board = [row[:] for row in board]
    for dr, dc in shape:
        r, c = land_row + dr, col_offset + dc
        if r < 0 or r >= BOARD_ROWS or c < 0 or c >= BOARD_COLS:
            return None
        new_board[r][c] = 1
    return new_board


def evaluate_board(board):
    heights = get_column_heights(board)
    holes = count_holes(board)
    bumpiness = get_bumpiness(heights)
    agg_height = sum(heights)
    max_height = max(heights) if heights else 0
    
    # Count complete lines
    complete = sum(1 for row in range(BOARD_ROWS) if all(board[row]))
    
    # Well-tuned weights from research
    return (
        -0.510066 * agg_height
        + 0.760666 * complete
        - 0.35663 * holes
        - 0.184483 * bumpiness
    )


def find_best_move(board, piece_type):
    """Find best (rotation_index, target_column) for piece placement"""
    if piece_type not in PIECES:
        return 0, 4
    
    rotations = PIECES[piece_type]
    best_score = float('-inf')
    best_rot = 0
    best_col = 4
    
    for rot_idx, shape in enumerate(rotations):
        min_dc = min(dc for _, dc in shape)
        max_dc = max(dc for _, dc in shape)
        
        for col in range(-min_dc, BOARD_COLS - max_dc):
            result = simulate_drop(board, shape, col)
            if result is None:
                continue
            
            # Clear lines for evaluation
            cleared = [row for row in result if not all(row)]
            lines = BOARD_ROWS - len(cleared)
            while len(cleared) < BOARD_ROWS:
                cleared.insert(0, [0] * BOARD_COLS)
            
            score = evaluate_board(cleared) + lines * 5.0
            if score > best_score:
                best_score = score
                best_rot = rot_idx
                best_col = col
    
    return best_rot, best_col


# ── MOVE EXECUTION ─────────────────────────────────────────────

def execute_move(page, target_rot, target_col, spawn_col=4):
    """Send key presses to rotate and position piece, then hard drop.
    N-Blox spawns pieces at approximately column 4 (center).
    """
    # First rotate
    for _ in range(target_rot):
        page.keyboard.press('ArrowUp')
        time.sleep(0.025)
    
    # Then move horizontally
    diff = target_col - spawn_col
    key = 'ArrowRight' if diff > 0 else 'ArrowLeft'
    for _ in range(abs(diff)):
        page.keyboard.press(key)
        time.sleep(0.025)
    
    # Hard drop (space)
    page.keyboard.press(' ')
    time.sleep(0.04)


# ── MAIN GAME LOOP ─────────────────────────────────────────────

def play_tetris():
    print("=== TETRIS AI BOT v2 ===")
    print("Now with calibration + board diff tracking!")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 900, 'height': 750})
        page = context.new_page()
        
        print("Opening freetetris.org...")
        page.goto('https://www.freetetris.org/', wait_until='domcontentloaded')
        time.sleep(5)
        
        # Focus game iframe
        try:
            page.click('#gameIFrame', timeout=5000)
            time.sleep(0.5)
        except Exception:
            print("Could not click game iframe")
        
        # Calibrate board position
        cal = calibrate_board(page)
        if not cal:
            print("FATAL: Could not calibrate board. Exiting.")
            browser.close()
            return
        
        # Debug: read and print initial board to verify calibration
        print("\n--- DEBUG: Reading initial board ---")
        board, colors = read_board(page, cal)
        filled = sum(sum(row) for row in board)
        print(f"Total filled cells: {filled} / {BOARD_ROWS * BOARD_COLS}")
        # Print visual board
        for row in range(BOARD_ROWS):
            line = ""
            for col in range(BOARD_COLS):
                line += "#" if board[row][col] else "."
            print(f"  {row:2d} |{line}|")
        print()
        
        # Player handles menu buttons (Play, New Game, level select)
        # Bot just waits for the game to be running
        print("\n>>> Waiting for YOU to start the game (click Play, pick level, etc.)...")
        print(">>> Bot takes over once pieces start falling.\n")
        
        # Focus iframe for keyboard input
        try:
            page.click('#gameIFrame', timeout=3000)
        except Exception:
            pass
        time.sleep(0.5)
        
        print("--- BOT v2 READY ---")
        print("Controls: Close browser or Ctrl+C to stop\n")
        
        move_count = 0
        lines_total = 0
        prev_board = None
        consecutive_fails = 0
        last_board_hash = None
        
        try:
            while True:
                # Read current board state
                board, colors = read_board(page, cal)
                
                # Hash the board to detect if anything changed
                board_hash = str(board)
                if board_hash == last_board_hash:
                    consecutive_fails += 1
                    if consecutive_fails > 20:
                        # Board hasn't changed — game might be paused/over
                        print("Board unchanged for 20 reads. Trying to unpause/restart...")
                        page.keyboard.press('Enter')
                        time.sleep(1)
                        page.keyboard.press(' ')
                        time.sleep(1)
                        consecutive_fails = 0
                        
                        # Delete calibration and recalibrate
                        if os.path.exists(CALIBRATION_FILE):
                            os.remove(CALIBRATION_FILE)
                        cal = calibrate_board(page)
                        if not cal:
                            print("Recalibration failed!")
                            time.sleep(3)
                            continue
                        prev_board = None
                    time.sleep(0.08)
                    continue
                
                consecutive_fails = 0
                last_board_hash = board_hash
                
                # Separate falling piece from static board
                piece_cells, static_board = separate_falling_piece(board, colors, prev_board)
                piece_type = identify_piece_type(piece_cells)
                
                if piece_type:
                    # Find optimal placement
                    target_rot, target_col = find_best_move(static_board, piece_type)
                    
                    # Execute move
                    execute_move(page, target_rot, target_col)
                    move_count += 1
                    
                    # Wait for piece to lock
                    time.sleep(0.12)
                    
                    # Read new board to track state
                    new_board, _ = read_board(page, cal)
                    
                    # Count cleared lines
                    old_filled = sum(sum(row) for row in static_board)
                    new_filled = sum(sum(row) for row in new_board)
                    if new_filled < old_filled:
                        cleared = (old_filled + 4 - new_filled) // BOARD_COLS
                        if cleared > 0:
                            lines_total += cleared
                            print(f"  CLEARED {cleared} line(s)! Total: {lines_total}")
                    
                    prev_board = new_board
                    
                    if move_count % 5 == 0:
                        heights = get_column_heights(new_board)
                        print(f"Move {move_count} | {piece_type} -> col {target_col} rot {target_rot} | Height: {max(heights)} | Lines: {lines_total}")
                else:
                    # No piece detected — wait for next piece
                    prev_board = board
                    time.sleep(0.08)
                    
                    # Check for game over (top rows packed)
                    top_fill = sum(board[0]) + sum(board[1])
                    if top_fill > 8:
                        print(f"GAME OVER after {move_count} moves, {lines_total} lines!")
                        time.sleep(2)
                        # Try restart
                        page.keyboard.press('Enter')
                        time.sleep(2)
                        prev_board = None
                        move_count = 0
                        lines_total = 0
                
                time.sleep(0.03)
        
        except KeyboardInterrupt:
            print(f"\nBot stopped! {move_count} moves, {lines_total} lines cleared")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == '__main__':
    play_tetris()
