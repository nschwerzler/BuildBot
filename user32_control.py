"""
User32.dll real mouse & keyboard control via ctypes.
Gives h4x3r REAL OS-level input — no virtual browser nonsense.
"""
import ctypes
import ctypes.wintypes
import time

# DPI awareness so coordinates aren't lying to us
ctypes.windll.shcore.SetProcessDpiAwareness(1)

user32 = ctypes.windll.user32

# --- Mouse event flags ---
MOUSEEVENTF_MOVE       = 0x0001
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
MOUSEEVENTF_ABSOLUTE   = 0x8000

# --- Keyboard event flags ---
KEYEVENTF_KEYUP = 0x0002

# --- Common virtual key codes ---
VK = {
    'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
    'space': 0x20, 'enter': 0x0D, 'escape': 0x1B, 'tab': 0x09,
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
}


def move_to(x, y):
    """Move the REAL mouse cursor to screen coords (x, y)."""
    user32.SetCursorPos(int(x), int(y))


def get_pos():
    """Get current cursor position as (x, y)."""
    pt = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def click(x=None, y=None, button='left'):
    """Click at (x, y). If coords omitted, clicks at current position."""
    if x is not None and y is not None:
        move_to(x, y)
        time.sleep(0.02)
    if button == 'left':
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == 'right':
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    elif button == 'middle':
        user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)


def double_click(x=None, y=None):
    """Double-click at (x, y)."""
    click(x, y)
    time.sleep(0.05)
    click(x, y)


def mouse_down(button='left'):
    """Hold mouse button down."""
    flag = {'left': MOUSEEVENTF_LEFTDOWN, 'right': MOUSEEVENTF_RIGHTDOWN, 'middle': MOUSEEVENTF_MIDDLEDOWN}[button]
    user32.mouse_event(flag, 0, 0, 0, 0)


def mouse_up(button='left'):
    """Release mouse button."""
    flag = {'left': MOUSEEVENTF_LEFTUP, 'right': MOUSEEVENTF_RIGHTUP, 'middle': MOUSEEVENTF_MIDDLEUP}[button]
    user32.mouse_event(flag, 0, 0, 0, 0)


def drag(x1, y1, x2, y2, duration=0.3, steps=20):
    """Drag from (x1,y1) to (x2,y2) smoothly."""
    move_to(x1, y1)
    time.sleep(0.05)
    mouse_down()
    for i in range(1, steps + 1):
        t = i / steps
        cx = x1 + (x2 - x1) * t
        cy = y1 + (y2 - y1) * t
        move_to(cx, cy)
        time.sleep(duration / steps)
    mouse_up()


def key_down(key):
    """Press key down. Use VK dict keys or raw vk code."""
    vk = VK.get(key, key) if isinstance(key, str) else key
    user32.keybd_event(vk, 0, 0, 0)


def key_up(key):
    """Release key. Use VK dict keys or raw vk code."""
    vk = VK.get(key, key) if isinstance(key, str) else key
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def key_press(key, hold=0.02):
    """Press and release a key."""
    key_down(key)
    time.sleep(hold)
    key_up(key)


def type_text(text, delay=0.03):
    """Type a string character by character."""
    for ch in text:
        lch = ch.lower()
        if lch in VK:
            if ch.isupper():
                key_down('shift')
                key_press(lch)
                key_up('shift')
            else:
                key_press(lch)
        elif ch == ' ':
            key_press('space')
        elif ch == '\n':
            key_press('enter')
        time.sleep(delay)


def get_window_rect(hwnd):
    """Get window rect as (left, top, right, bottom)."""
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def find_window(class_name=None, title=None):
    """Find window by class name and/or title. Returns HWND or 0."""
    return user32.FindWindowW(class_name, title)


def get_foreground_window():
    """Get the currently focused window handle."""
    return user32.GetForegroundWindow()


def set_foreground(hwnd):
    """Bring a window to the front."""
    user32.SetForegroundWindow(hwnd)


def get_screen_size():
    """Get screen resolution as (width, height)."""
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


# --- Quick test when run directly ---
if __name__ == '__main__':
    print("=== User32.dll Control Module ===")
    sw, sh = get_screen_size()
    print(f"Screen: {sw}x{sh}")
    cx, cy = get_pos()
    print(f"Cursor at: ({cx}, {cy})")

    # Demo: move cursor in a small square and back
    print("Moving cursor in a quick square pattern...")
    orig_x, orig_y = cx, cy
    for dx, dy in [(100, 0), (0, 100), (-100, 0), (0, -100)]:
        cx += dx
        cy += dy
        move_to(cx, cy)
        time.sleep(0.15)

    # Return to original position
    move_to(orig_x, orig_y)
    print(f"Cursor returned to ({orig_x}, {orig_y})")

    fg = get_foreground_window()
    if fg:
        r = get_window_rect(fg)
        print(f"Foreground window rect: {r}")

    print("User32.dll is READY. h4x3r has real mouse + keyboard control now.")
