"""
User32.dll quiz clicker v2 — pixel scanning + cursor tracker overlay.
Finds the game visually, shows where clicks land with a dog cursor tracker.
"""
import ctypes
import ctypes.wintypes
import time
import subprocess
import sys
import os
import math
from PIL import ImageGrab, Image

# DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)
user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# --- Known answer positions (% of game area) ---
ANSWERS = {
    1: (0.72, 0.72, "FOUR (bottom-right)"),
    2: (0.28, 0.72, "TIN CAN (bottom-left)"),
    3: (0.28, 0.72, "K.O (bottom-left)"),
    4: (0.52, 0.22, "THE ANSWER (question text)"),
    # Q5 = hover on red dot — special
    6: (0.72, 0.50, "Shallots (top-right)"),
    7: (0.28, 0.50, "An elephant (top-left)"),
    9: (0.72, 0.72, "BLAM! (bottom-right)"),
    20: (0.245, 0.7125, "SEAL! (bottom-left)"),
}


def enum_windows():
    results = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            results.append((hwnd, buf.value))
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return results


def find_chrome_window():
    windows = enum_windows()
    for hwnd, title in windows:
        if "Impossible Quiz" in title or "CrazyGames" in title:
            return hwnd, title
    for hwnd, title in windows:
        if "Chrome" in title or "Google Chrome" in title:
            return hwnd, title
    return None, None


def get_client_origin(hwnd):
    pt = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


def get_client_size(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    return rect.right, rect.bottom


def click_screen(x, y, label="", pause=0.05):
    """Move cursor and click at screen coordinates. Cursor tracker shows where."""
    if label:
        print(f"  >> Click: {label} at ({x}, {y})")
    user32.SetCursorPos(int(x), int(y))
    time.sleep(pause)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def move_to(x, y):
    """Move cursor without clicking (for hover actions like Q5)."""
    user32.SetCursorPos(int(x), int(y))


def screenshot_full():
    """Full screen screenshot."""
    return ImageGrab.grab()


def screenshot_region(x, y, w, h):
    return ImageGrab.grab(bbox=(x, y, x + w, y + h))


def color_distance(c1, c2):
    """Euclidean RGB distance."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))


def find_color_region(img, target_rgb, tolerance=60, min_cluster=20):
    """Find the center of a region matching target_rgb within tolerance.
    Returns (cx, cy) in image coords or None."""
    w, h = img.size
    matches = []
    # Sample every 3rd pixel for speed
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            px = img.getpixel((x, y))[:3]
            if color_distance(px, target_rgb) < tolerance:
                matches.append((x, y))

    if len(matches) < min_cluster:
        return None

    # Centroid of matching pixels
    avg_x = sum(m[0] for m in matches) / len(matches)
    avg_y = sum(m[1] for m in matches) / len(matches)
    return int(avg_x), int(avg_y), len(matches)


def find_game_boundary(img, client_x, client_y):
    """Scan screenshot to find the Flash game area by looking for its border/background.
    The game has a distinctive blue background: around RGB(70,130,180) steel blue area,
    surrounded by the CrazyGames page (darker/different colors).
    Returns (game_x, game_y, game_w, game_h) in screen coords or None."""
    w, h = img.size

    # The game iframe is roughly in the center-left of the page
    # Scan for a large rectangular region of consistent background color
    # Flash game background: look for clusters of blue-ish pixels

    # Strategy: scan horizontally across the middle for color transitions
    mid_y = h // 2
    row_colors = []
    for x in range(0, w, 2):
        px = img.getpixel((x, mid_y))[:3]
        row_colors.append((x, px))

    # Find transitions — game area will be a broad swath of similar color
    # Just find the largest contiguous run of "not-webpage-background" pixels
    # CrazyGames page is typically dark (RGB < 50) or white/gray (RGB > 230)

    # Look for the game canvas — it's usually colorful/medium brightness
    runs = []
    current_run_start = None
    for i, (x, rgb) in enumerate(row_colors):
        brightness = sum(rgb) / 3
        # Game content: medium brightness, not pure white/black/gray
        is_game = 40 < brightness < 220 and max(rgb) - min(rgb) > 10
        if is_game:
            if current_run_start is None:
                current_run_start = x
        else:
            if current_run_start is not None:
                runs.append((current_run_start, x))
                current_run_start = None
    if current_run_start is not None:
        runs.append((current_run_start, w))

    if not runs:
        return None

    # Pick the widest run
    best = max(runs, key=lambda r: r[1] - r[0])
    game_left, game_right = best
    game_width = game_right - game_left

    # Now scan vertically at the center of the game to find top/bottom
    center_x = (game_left + game_right) // 2
    col_colors = []
    for y in range(0, h, 2):
        px = img.getpixel((center_x, y))[:3]
        col_colors.append((y, px))

    v_runs = []
    v_start = None
    for y, rgb in col_colors:
        brightness = sum(rgb) / 3
        is_game = 40 < brightness < 220 and max(rgb) - min(rgb) > 10
        if is_game:
            if v_start is None:
                v_start = y
        else:
            if v_start is not None:
                v_runs.append((v_start, y))
                v_start = None
    if v_start is not None:
        v_runs.append((v_start, h))

    if not v_runs:
        return None

    best_v = max(v_runs, key=lambda r: r[1] - r[0])
    game_top, game_bottom = best_v
    game_height = game_bottom - game_top

    # Convert to screen coords
    sx = client_x + game_left
    sy = client_y + game_top
    return sx, sy, game_width, game_height


def launch_cursor_tracker():
    """Launch the dog cursor tracker overlay as a background process."""
    tracker_code = '''
import tkinter as tk
from PIL import Image, ImageTk
import ctypes, ctypes.wintypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)
u32 = ctypes.windll.user32

root = tk.Tk()
root.overrideredirect(True)
root.attributes('-topmost', True)
root.attributes('-transparentcolor', 'magenta')
root.configure(bg='magenta')

img = Image.open(r'D:\\BuildBot\\dog_cursor.png').convert('RGBA')
size = max(img.size)
root.geometry(f'{img.width}x{img.height}+0+0')

bg = Image.new('RGBA', img.size, (255, 0, 255, 255))
composite = Image.alpha_composite(bg, img)
photo = ImageTk.PhotoImage(composite)
label = tk.Label(root, image=photo, bg='magenta', borderwidth=0)
label.pack()

GWL_EXSTYLE = -20
hwnd = u32.GetParent(root.winfo_id())
style = u32.GetWindowLongW(hwnd, GWL_EXSTYLE)
u32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | 0x80000 | 0x20)

half_w = img.width // 2
half_h = img.height // 2
def chase():
    pt = ctypes.wintypes.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    root.geometry(f'{img.width}x{img.height}+{pt.x - half_w}+{pt.y - half_h}')
    root.after(8, chase)
chase()
root.mainloop()
'''
    proc = subprocess.Popen(
        [sys.executable, "-c", tracker_code],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    print(f"  Cursor tracker launched (PID {proc.pid})")
    return proc


def main():
    print("=" * 50)
    print("  User32 Quiz Clicker v2")
    print("  Pixel Scanning + Cursor Tracker")
    print("=" * 50)

    # Launch cursor tracker so we can SEE where clicks go
    tracker = launch_cursor_tracker()
    time.sleep(0.5)

    # 1. Find Chrome
    hwnd, title = find_chrome_window()
    if not hwnd:
        print("ERROR: No Chrome window found!")
        tracker.terminate()
        return
    print(f"Found: \"{title}\"")

    # 2. Bring to front
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    # 3. Get client area
    cx, cy = get_client_origin(hwnd)
    cw, ch = get_client_size(hwnd)
    print(f"Client origin: ({cx}, {cy}), size: {cw}x{ch}")

    # 4. Screenshot the client area
    client_img = screenshot_region(cx, cy, cw, ch)
    client_img.save("d:\\BuildBot\\user32_client.png")
    print("Saved client screenshot to user32_client.png")

    # 5. Pixel-scan to find the game area
    print("\nScanning for game area...")
    bounds = find_game_boundary(client_img, cx, cy)
    if bounds:
        game_sx, game_sy, game_w, game_h = bounds
        print(f"  Game found at screen ({game_sx}, {game_sy}) size {game_w}x{game_h}")

        # Sanity check: game should be at least 400x300
        if game_w < 400 or game_h < 300:
            print(f"  WARNING: Game area seems too small ({game_w}x{game_h}), trying hardcoded fallback")
            bounds = None

    if not bounds:
        # Fallback: use known proportions within Chrome viewport
        # Game is roughly centered in the page, about 72% of viewport width
        chrome_ui = max(ch - 1245, 60)  # estimate Chrome UI height
        game_w = int(cw * 0.53)
        game_h = int(game_w * 0.73)  # game aspect ratio ~889:647
        game_sx = cx + int(cw * 0.145)
        game_sy = cy + chrome_ui + int((ch - chrome_ui) * 0.06)
        print(f"  Using fallback: screen ({game_sx}, {game_sy}) size {game_w}x{game_h}")

    # 6. Screenshot game area
    game_img = screenshot_region(game_sx, game_sy, game_w, game_h)
    game_img.save("d:\\BuildBot\\user32_game_area.png")
    print(f"  Saved game area to user32_game_area.png")

    # 7. Look for the blue START button via pixel scanning
    # START button is blue: roughly RGB(0, 100, 200) to (50, 150, 255)
    print("\nScanning for START button (blue)...")
    start_result = find_color_region(game_img, (30, 120, 220), tolerance=70, min_cluster=30)

    if start_result:
        sx, sy, count = start_result
        screen_start_x = game_sx + sx
        screen_start_y = game_sy + sy
        print(f"  Found blue region: game({sx}, {sy}), screen({screen_start_x}, {screen_start_y}), {count} pixels")

        # Move there first so tracker shows position
        move_to(screen_start_x, screen_start_y)
        time.sleep(1.0)  # let user see where it's going
        print("  Cursor is hovering over START — clicking in 1 sec...")
        time.sleep(1.0)
        click_screen(screen_start_x, screen_start_y, "START (pixel-scanned)")
    else:
        print("  No blue START found. Trying percentage-based positions...")
        # Try known percentage positions
        positions = [
            (0.28, 0.52, "28%/52%"),
            (0.30, 0.55, "30%/55%"),
            (0.25, 0.50, "25%/50%"),
            (0.35, 0.60, "35%/60%"),
            (0.50, 0.80, "center-bottom"),
        ]
        for px, py, label in positions:
            sx = game_sx + int(game_w * px)
            sy = game_sy + int(game_h * py)
            move_to(sx, sy)
            time.sleep(0.5)
            click_screen(sx, sy, f"START ({label})")
            time.sleep(0.8)

    # 8. Wait and check if game started
    time.sleep(2.0)
    after_img = screenshot_region(game_sx, game_sy, game_w, game_h)
    after_img.save("d:\\BuildBot\\user32_after_start.png")

    # Compare screenshots
    before_px = game_img.getpixel((game_w // 2, game_h // 2))[:3]
    after_px = after_img.getpixel((game_w // 2, game_h // 2))[:3]
    changed = color_distance(before_px, after_px) > 30
    print(f"\n  Before center: {before_px}, After: {after_px}, Changed: {changed}")

    if changed:
        print("\n  GAME STARTED! Ready for Q1...")
        # Q1: "How many holes in a polo?" -> FOUR (bottom-right)
        time.sleep(1.5)
        q1_x = game_sx + int(game_w * 0.72)
        q1_y = game_sy + int(game_h * 0.72)
        move_to(q1_x, q1_y)
        time.sleep(0.5)
        click_screen(q1_x, q1_y, "Q1: FOUR")
    else:
        print("\n  Game didn't start. Check user32_game_area.png and user32_after_start.png")
        print("  The cursor tracker is still running — you can see where clicks are landing.")
        print("  Press Ctrl+C to stop.")

    # Keep tracker alive for a bit so d0g3 can see what happened
    print("\n  Tracker will stay on for 15 seconds...")
    try:
        time.sleep(15)
    except KeyboardInterrupt:
        pass

    tracker.terminate()
    print("  Cursor tracker stopped. Done!")


if __name__ == "__main__":
    main()
