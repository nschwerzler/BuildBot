"""
hardware_input.py - Direct hardware-level mouse & keyboard control via Win32 API.

Capabilities:
  - Sustained key holds (key_down / key_up / hold_key for duration)
  - Key tapping with configurable delays
  - Mouse movement (absolute & relative)
  - Mouse clicks (left, right, middle)
  - Mouse drag operations
  - Combo keys (e.g. Ctrl+C)
  - Works with games that check isTrusted / reject JS-dispatched events

Uses SendInput (hardware-level) — the closest to real input you can get without
a physical device. Works with DirectInput games, browsers, everything.

Usage:
    from hardware_input import kbd, mouse

    kbd.tap('w')                    # single press
    kbd.hold('w', 2.0)             # hold W for 2 seconds
    kbd.key_down('space')          # press and hold
    kbd.key_up('space')            # release
    kbd.combo('ctrl', 'c')         # Ctrl+C

    mouse.move_to(500, 300)        # absolute move
    mouse.move_rel(10, -5)         # relative move
    mouse.click()                  # left click
    mouse.click('right')           # right click
    mouse.double_click()           # double left click
    mouse.drag(100, 100, 500, 300) # drag from (100,100) to (500,300)
    mouse.scroll(3)                # scroll up 3 notches
    mouse.scroll(-3)              # scroll down 3 notches
"""

import ctypes
import ctypes.wintypes
import time
import threading
from typing import Optional

# ─── Win32 Constants ────────────────────────────────────────────────
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800

# ─── Win32 Structures ──────────────────────────────────────────────
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("union", _INPUT_UNION)]

SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
SendInput.restype = ctypes.c_uint

MapVirtualKeyW = ctypes.windll.user32.MapVirtualKeyW
GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics
SM_CXSCREEN = 0
SM_CYSCREEN = 1

# ─── Virtual Key Code Map ──────────────────────────────────────────
VK_MAP = {
    # Letters
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    # Numbers
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    # F-keys
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B,
    # Modifiers
    'shift': 0x10, 'ctrl': 0x11, 'control': 0x11, 'alt': 0x12, 'menu': 0x12,
    'lshift': 0xA0, 'rshift': 0xA1, 'lctrl': 0xA2, 'rctrl': 0xA3,
    'lalt': 0xA4, 'ralt': 0xA5,
    # Navigation
    'escape': 0x1B, 'esc': 0x1B, 'tab': 0x09, 'capslock': 0x14,
    'space': 0x20, 'enter': 0x0D, 'return': 0x0D, 'backspace': 0x08,
    'delete': 0x2E, 'insert': 0x2D,
    'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
    # Arrow keys (extended)
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'arrowup': 0x26, 'arrowdown': 0x28, 'arrowleft': 0x25, 'arrowright': 0x27,
    # Misc
    'numlock': 0x90, 'scrolllock': 0x91, 'printscreen': 0x2C,
    'pause': 0x13, 'win': 0x5B, 'lwin': 0x5B, 'rwin': 0x5C,
    'apps': 0x5D,
    # Punctuation
    'minus': 0xBD, '-': 0xBD, 'equals': 0xBB, '=': 0xBB,
    'lbracket': 0xDB, '[': 0xDB, 'rbracket': 0xDD, ']': 0xDD,
    'backslash': 0xDC, '\\': 0xDC, 'semicolon': 0xBA, ';': 0xBA,
    'quote': 0xDE, "'": 0xDE, 'comma': 0xBC, ',': 0xBC,
    'period': 0xBE, '.': 0xBE, 'slash': 0xBF, '/': 0xBF,
    'grave': 0xC0, '`': 0xC0,
}

# Extended keys that need the KEYEVENTF_EXTENDEDKEY flag
EXTENDED_KEYS = {
    0x26, 0x28, 0x25, 0x27,  # arrows
    0x2D, 0x2E, 0x24, 0x23,  # insert, delete, home, end
    0x21, 0x22,              # pageup, pagedown
    0x5B, 0x5C,              # win keys
    0xA3, 0xA5,              # rctrl, ralt
}


def _get_vk(key: str) -> int:
    """Resolve a key name to its virtual key code."""
    k = key.lower().strip()
    if k in VK_MAP:
        return VK_MAP[k]
    if len(k) == 1:
        return ord(k.upper())
    raise ValueError(f"Unknown key: {key!r}. Use a name from VK_MAP or a single character.")


def _make_key_input(vk: int, scan: int, flags: int) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    inp.union.ki.wScan = scan
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = None
    return inp


# ─── Keyboard Controller ───────────────────────────────────────────
class Keyboard:
    """Hardware-level keyboard control using SendInput."""

    def __init__(self):
        self._held_keys: set[int] = set()

    def key_down(self, key: str):
        """Press a key down (stays held until key_up is called)."""
        vk = _get_vk(key)
        scan = MapVirtualKeyW(vk, 0) & 0xFF
        flags = KEYEVENTF_SCANCODE
        if vk in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY
        inp = _make_key_input(vk, scan, flags)
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        self._held_keys.add(vk)

    def key_up(self, key: str):
        """Release a held key."""
        vk = _get_vk(key)
        scan = MapVirtualKeyW(vk, 0) & 0xFF
        flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        if vk in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY
        inp = _make_key_input(vk, scan, flags)
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        self._held_keys.discard(vk)

    def tap(self, key: str, duration: float = 0.02):
        """Press and release a key with a short delay between."""
        self.key_down(key)
        time.sleep(duration)
        self.key_up(key)

    def hold(self, key: str, duration: float = 1.0):
        """Hold a key for a specific duration (blocking)."""
        self.key_down(key)
        time.sleep(duration)
        self.key_up(key)

    def hold_async(self, key: str, duration: float = 1.0) -> threading.Thread:
        """Hold a key for a duration in a background thread. Returns the thread."""
        t = threading.Thread(target=self.hold, args=(key, duration), daemon=True)
        t.start()
        return t

    def combo(self, *keys: str):
        """Press a key combination (e.g. combo('ctrl', 'c'))."""
        for k in keys:
            self.key_down(k)
        time.sleep(0.02)
        for k in reversed(keys):
            self.key_up(k)

    def type_text(self, text: str, delay: float = 0.03):
        """Type a string character by character."""
        for ch in text:
            self.tap(ch, delay)
            time.sleep(delay)

    def release_all(self):
        """Release all currently held keys."""
        for vk in list(self._held_keys):
            scan = MapVirtualKeyW(vk, 0) & 0xFF
            flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
            if vk in EXTENDED_KEYS:
                flags |= KEYEVENTF_EXTENDEDKEY
            inp = _make_key_input(vk, scan, flags)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        self._held_keys.clear()


# ─── Mouse Controller ──────────────────────────────────────────────
class Mouse:
    """Hardware-level mouse control using SendInput."""

    def _send_mouse(self, flags: int, dx: int = 0, dy: int = 0, data: int = 0):
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dx = dx
        inp.union.mi.dy = dy
        inp.union.mi.mouseData = data
        inp.union.mi.dwFlags = flags
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = None
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def move_to(self, x: int, y: int):
        """Move mouse to absolute screen coordinates."""
        screen_w = GetSystemMetrics(SM_CXSCREEN)
        screen_h = GetSystemMetrics(SM_CYSCREEN)
        # Convert to normalized 0-65535 range
        abs_x = int(x * 65535 / screen_w)
        abs_y = int(y * 65535 / screen_h)
        self._send_mouse(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, abs_x, abs_y)

    def move_rel(self, dx: int, dy: int):
        """Move mouse relative to current position."""
        self._send_mouse(MOUSEEVENTF_MOVE, dx, dy)

    def click(self, button: str = 'left', count: int = 1):
        """Click a mouse button. button: 'left', 'right', or 'middle'."""
        down_flag, up_flag = {
            'left':   (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
            'right':  (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
            'middle': (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        }[button.lower()]
        for _ in range(count):
            self._send_mouse(down_flag)
            time.sleep(0.01)
            self._send_mouse(up_flag)
            if count > 1:
                time.sleep(0.02)

    def double_click(self, button: str = 'left'):
        """Double-click a mouse button."""
        self.click(button, count=2)

    def mouse_down(self, button: str = 'left'):
        """Press a mouse button down (stays held)."""
        flag = {'left': MOUSEEVENTF_LEFTDOWN, 'right': MOUSEEVENTF_RIGHTDOWN,
                'middle': MOUSEEVENTF_MIDDLEDOWN}[button.lower()]
        self._send_mouse(flag)

    def mouse_up(self, button: str = 'left'):
        """Release a mouse button."""
        flag = {'left': MOUSEEVENTF_LEFTUP, 'right': MOUSEEVENTF_RIGHTUP,
                'middle': MOUSEEVENTF_MIDDLEUP}[button.lower()]
        self._send_mouse(flag)

    def drag(self, x1: int, y1: int, x2: int, y2: int,
             button: str = 'left', duration: float = 0.3, steps: int = 20):
        """Drag from (x1,y1) to (x2,y2) over duration seconds."""
        self.move_to(x1, y1)
        time.sleep(0.05)
        self.mouse_down(button)
        for i in range(1, steps + 1):
            t = i / steps
            ix = int(x1 + (x2 - x1) * t)
            iy = int(y1 + (y2 - y1) * t)
            self.move_to(ix, iy)
            time.sleep(duration / steps)
        self.mouse_up(button)

    def scroll(self, clicks: int):
        """Scroll the mouse wheel. Positive = up, negative = down."""
        self._send_mouse(MOUSEEVENTF_WHEEL, data=clicks * 120)

    def get_position(self) -> tuple[int, int]:
        """Get current mouse cursor position."""
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)


# ─── Module-level singletons ───────────────────────────────────────
kbd = Keyboard()
mouse = Mouse()


# ─── CLI demo ───────────────────────────────────────────────────────
if __name__ == '__main__':
    print("hardware_input.py — Direct hardware mouse & keyboard control")
    print("=" * 60)
    print(f"Screen: {GetSystemMetrics(SM_CXSCREEN)}x{GetSystemMetrics(SM_CYSCREEN)}")
    print(f"Mouse at: {mouse.get_position()}")
    print()
    print("Available keyboard methods:")
    print("  kbd.key_down(key)        — press key (holds)")
    print("  kbd.key_up(key)          — release key")
    print("  kbd.tap(key)             — quick press+release")
    print("  kbd.hold(key, secs)      — hold for duration (blocking)")
    print("  kbd.hold_async(key, s)   — hold for duration (background)")
    print("  kbd.combo('ctrl', 'c')   — key combo")
    print("  kbd.type_text('hello')   — type a string")
    print("  kbd.release_all()        — release everything")
    print()
    print("Available mouse methods:")
    print("  mouse.move_to(x, y)      — absolute move")
    print("  mouse.move_rel(dx, dy)   — relative move")
    print("  mouse.click('left')      — click (left/right/middle)")
    print("  mouse.double_click()     — double click")
    print("  mouse.mouse_down('left') — hold button")
    print("  mouse.mouse_up('left')   — release button")
    print("  mouse.drag(x1,y1,x2,y2)  — drag operation")
    print("  mouse.scroll(3)          — scroll wheel")
    print("  mouse.get_position()     — get cursor pos")
    print()
    print(f"Supported keys: {len(VK_MAP)} named keys + any single character")
    print("Run 'from hardware_input import kbd, mouse' to use in your scripts!")
