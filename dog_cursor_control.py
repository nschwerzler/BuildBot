"""
AI-controlled dog cursor overlay v4.0 — clicking + speech bubbles!
Reads commands from dog_cursor_cmd.json and moves the dog there.
Supports: move, click, drag, type, keypress, scroll, speech bubbles.

Command format:
  {"x": N, "y": N, "speed": 0.08}                    — move only
  {"x": N, "y": N, "click": "left"}                   — move + left click (waits for arrival)
  {"x": N, "y": N, "click": "right"}                  — move + right click
  {"x": N, "y": N, "click": "double"}                 — move + double click
  {"x": N, "y": N, "click": "left", "hold": 500}      — move + hold click for N ms
  {"x": N, "y": N, "drag_to": {"x": N2, "y": N2}}     — drag from (x,y) to (x2,y2)
  {"type": "hello world"}                              — type text at current pos
  {"key": "enter"}                                     — press a key (enter, tab, escape, etc)
  {"scroll": -3}                                       — scroll wheel (negative=down, positive=up)
  {"x": N, "y": N, "click": "none"}                   — move only (explicit no-click)
  {"say": "Hello!"}                                    — show speech bubble near dog
  {"say": "Hi!", "say_duration": 5}                    — speech bubble for 5 seconds (default 3)
  {"x": N, "y": N, "click": "left", "say": "Clicking!"} — combine speech + action
"""
import tkinter as tk
from PIL import Image, ImageTk
import json, os, ctypes, time, threading

ctypes.windll.shcore.SetProcessDpiAwareness(1)

CMD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dog_cursor_cmd.json")

# --- Real mouse input via ctypes ---
user32 = ctypes.windll.user32

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]

# Virtual key codes for common keys
VK_MAP = {
    "enter": 0x0D, "return": 0x0D, "tab": 0x09, "escape": 0x1B, "esc": 0x1B,
    "space": 0x20, "backspace": 0x08, "delete": 0x2E, "up": 0x26, "down": 0x28,
    "left": 0x25, "right": 0x27, "home": 0x24, "end": 0x23, "pageup": 0x21,
    "pagedown": 0x22, "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78,
    "f10": 0x79, "f11": 0x7A, "f12": 0x7B, "ctrl": 0x11, "alt": 0x12,
    "shift": 0x10, "win": 0x5B,
}

def real_move(x, y):
    """Move the REAL mouse cursor to (x, y)."""
    user32.SetCursorPos(int(x), int(y))

def real_click(x, y, button="left"):
    """Move cursor and click."""
    real_move(x, y)
    time.sleep(0.02)
    if button == "left":
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == "right":
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    elif button == "double":
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def real_hold_click(x, y, duration_ms):
    """Move cursor, hold left click for duration_ms, then release."""
    real_move(x, y)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(duration_ms / 1000.0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def real_drag(x1, y1, x2, y2, steps=30):
    """Drag from (x1,y1) to (x2,y2) with smooth movement."""
    real_move(x1, y1)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    for i in range(1, steps + 1):
        t = i / steps
        mx = x1 + (x2 - x1) * t
        my = y1 + (y2 - y1) * t
        real_move(mx, my)
        time.sleep(0.01)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def real_scroll(amount):
    """Scroll the mouse wheel. Negative = down, positive = up."""
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(amount * 120), 0)

def real_type(text):
    """Type text using SendInput."""
    for char in text:
        vk = ctypes.windll.user32.VkKeyScanW(ord(char))
        scan = ctypes.windll.user32.MapVirtualKeyW(vk & 0xFF, 0)
        # Key down
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = 0
        inp.union.ki.wScan = ord(char)
        inp.union.ki.dwFlags = 0x0004  # KEYEVENTF_UNICODE
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        # Key up
        inp2 = INPUT()
        inp2.type = INPUT_KEYBOARD
        inp2.union.ki.wVk = 0
        inp2.union.ki.wScan = ord(char)
        inp2.union.ki.dwFlags = 0x0004 | 0x0002  # KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        user32.SendInput(1, ctypes.byref(inp2), ctypes.sizeof(INPUT))
        time.sleep(0.02)

def real_keypress(key_name):
    """Press and release a named key."""
    vk = VK_MAP.get(key_name.lower())
    if vk is None:
        # Try single character
        if len(key_name) == 1:
            vk = ctypes.windll.user32.VkKeyScanW(ord(key_name)) & 0xFF
        else:
            print(f"Unknown key: {key_name}")
            return
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    inp.union.ki.dwFlags = 0
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(0.02)
    inp2 = INPUT()
    inp2.type = INPUT_KEYBOARD
    inp2.union.ki.wVk = vk
    inp2.union.ki.dwFlags = 0x0002  # KEYEVENTF_KEYUP
    user32.SendInput(1, ctypes.byref(inp2), ctypes.sizeof(INPUT))

# --- Action queue (runs clicks in background thread to not block UI) ---
action_queue = []
action_lock = threading.Lock()

def action_worker():
    while True:
        action = None
        with action_lock:
            if action_queue:
                action = action_queue.pop(0)
        if action:
            try:
                action()
            except Exception as e:
                print(f"Action error: {e}")
        time.sleep(0.01)

worker_thread = threading.Thread(target=action_worker, daemon=True)
worker_thread.start()

# --- GUI setup ---
root = tk.Tk()
root.overrideredirect(True)
root.attributes('-topmost', True)
root.attributes('-transparentcolor', 'magenta')
root.configure(bg='magenta')
root.geometry('32x32+500+500')

img = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dog_cursor.png')).convert('RGBA')
bg = Image.new('RGBA', img.size, (255, 0, 255, 255))
composite = Image.alpha_composite(bg, img)
photo = ImageTk.PhotoImage(composite)

label = tk.Label(root, image=photo, bg='magenta', borderwidth=0)
label.pack()

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

# --- Speech bubble window ---
bubble_win = tk.Toplevel(root)
bubble_win.overrideredirect(True)
bubble_win.attributes('-topmost', True)
bubble_win.configure(bg='#222222')
bubble_win.geometry('1x1+0+0')
bubble_win.withdraw()

bubble_frame = tk.Frame(bubble_win, bg='#222222', padx=8, pady=5,
                        highlightbackground='#00ccff', highlightthickness=2)
bubble_frame.pack()

bubble_label = tk.Label(bubble_frame, text='', bg='#222222', fg='#ffffff',
                        font=('Segoe UI', 10, 'bold'), wraplength=250, justify='left')
bubble_label.pack()

# Tail indicator (small triangle-ish label below bubble)
tail_label = tk.Label(bubble_win, text='▼', bg='#222222', fg='#00ccff',
                      font=('Segoe UI', 8), borderwidth=0)

# Make bubble click-through too
def make_click_through(win):
    hwnd_b = ctypes.windll.user32.GetParent(win.winfo_id())
    style_b = ctypes.windll.user32.GetWindowLongW(hwnd_b, -20)
    ctypes.windll.user32.SetWindowLongW(hwnd_b, -20, style_b | 0x80000 | 0x20)

bubble_hide_after = [None]  # timer ID for auto-hide

def show_bubble(text, duration=3.0):
    """Show a speech bubble near the dog cursor."""
    if bubble_hide_after[0]:
        root.after_cancel(bubble_hide_after[0])
        bubble_hide_after[0] = None

    bubble_label.config(text=text)
    bubble_win.deiconify()
    bubble_win.update_idletasks()

    # Make click-through after showing
    make_click_through(bubble_win)

    # Auto-hide after duration
    bubble_hide_after[0] = root.after(int(duration * 1000), hide_bubble)
    print(f"  💬 \"{text}\" ({duration}s)")

def hide_bubble():
    bubble_win.withdraw()
    bubble_hide_after[0] = None

def update_bubble_pos():
    """Keep bubble positioned above the dog cursor."""
    if bubble_win.winfo_viewable():
        bw = bubble_win.winfo_reqwidth()
        bh = bubble_win.winfo_reqheight()
        # Position above and slightly right of dog
        bx = int(cur_x + 16 - bw // 2)
        by = int(cur_y - bh - 8)
        # Keep on screen
        bx = max(4, min(screen_w - bw - 4, bx))
        by = max(4, min(screen_h - bh - 4, by))
        bubble_win.geometry(f'+{bx}+{by}')
    root.after(16, update_bubble_pos)

cur_x = float(screen_w // 2)
cur_y = float(screen_h // 2)
target_x = cur_x
target_y = cur_y
speed = 0.08  # lerp factor

# Write initial command file
def write_default_cmd():
    cmd = {"x": screen_w // 2, "y": screen_h // 2, "speed": 0.08}
    with open(CMD_FILE, 'w') as f:
        json.dump(cmd, f)

write_default_cmd()

last_mtime = 0
last_cmd_id = None  # Track command IDs to avoid re-executing

# --- Pending action: waits for dog to arrive before executing ---
pending_action = [None]  # stores (action_fn, target_x, target_y) or None
ARRIVE_THRESHOLD = 5  # pixels — close enough = arrived

def queue_or_immediate(cmd):
    """For type/key/scroll: execute immediately. For click/drag: wait for arrival."""
    text = cmd.get("type")
    key = cmd.get("key")
    scroll = cmd.get("scroll")

    if text is not None:
        with action_lock:
            action_queue.append(lambda t=str(text): real_type(t))
        print(f"  -> typing: {text[:30]}...")
        return
    if key is not None:
        with action_lock:
            action_queue.append(lambda k=str(key): real_keypress(k))
        print(f"  -> keypress: {key}")
        return
    if scroll is not None:
        with action_lock:
            action_queue.append(lambda s=int(scroll): real_scroll(s))
        print(f"  -> scroll: {scroll}")
        return

    # For click/drag — store as pending (fires when dog arrives)
    click = cmd.get("click")
    hold = cmd.get("hold")
    drag_to = cmd.get("drag_to")
    x = float(cmd.get("x", target_x))
    y = float(cmd.get("y", target_y))

    if drag_to is not None:
        dx, dy = float(drag_to["x"]), float(drag_to["y"])
        pending_action[0] = (lambda: real_drag(x, y, dx, dy), x, y)
        print(f"  -> drag ({x},{y}) -> ({dx},{dy}) [waiting for arrival]")
    elif click and click != "none":
        if hold:
            pending_action[0] = (lambda: real_hold_click(x, y, int(hold)), x, y)
            print(f"  -> hold-click ({x},{y}) for {hold}ms [waiting for arrival]")
        else:
            pending_action[0] = (lambda c=str(click): real_click(x, y, c), x, y)
            print(f"  -> {click}-click at ({x},{y}) [waiting for arrival]")
    else:
        print(f"  -> move to ({x},{y})")

def check_arrival():
    """If dog has arrived at pending action's target, fire the action."""
    if pending_action[0] is None:
        return
    action_fn, tx, ty = pending_action[0]
    dist = ((cur_x - tx) ** 2 + (cur_y - ty) ** 2) ** 0.5
    if dist < ARRIVE_THRESHOLD:
        pending_action[0] = None
        with action_lock:
            action_queue.append(action_fn)
        print(f"  ✓ arrived — executing action!")

def update_pos():
    global cur_x, cur_y, target_x, target_y, speed, last_mtime, last_cmd_id

    # Check for new commands
    try:
        mtime = os.path.getmtime(CMD_FILE)
        if mtime != last_mtime:
            last_mtime = mtime
            with open(CMD_FILE, 'r') as f:
                cmd = json.load(f)

            # Use cmd_id to prevent re-executing same click
            cmd_id = cmd.get("id", mtime)
            new_cmd = cmd_id != last_cmd_id
            last_cmd_id = cmd_id

            target_x = float(cmd.get("x", target_x))
            target_y = float(cmd.get("y", target_y))
            speed = float(cmd.get("speed", speed))

            if new_cmd:
                # Handle speech bubble
                say_text = cmd.get("say")
                if say_text:
                    say_dur = float(cmd.get("say_duration", 3.0))
                    show_bubble(str(say_text), say_dur)

                queue_or_immediate(cmd)
    except (json.JSONDecodeError, FileNotFoundError, OSError, ValueError):
        pass

    # Smooth lerp toward target
    cur_x += (target_x - cur_x) * speed
    cur_y += (target_y - cur_y) * speed

    # Check if pending action should fire (dog arrived at target)
    check_arrival()

    ix = int(max(0, min(screen_w - 32, cur_x)))
    iy = int(max(0, min(screen_h - 32, cur_y)))
    root.geometry(f'32x32+{ix}+{iy}')
    root.after(16, update_pos)

# Click-through
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

update_pos()
update_bubble_pos()
print(f"Dog cursor v4.0 ready! Screen: {screen_w}x{screen_h}")
print(f"Control file: {CMD_FILE}")
print("Commands:")
print('  Move:   {{"x": N, "y": N, "speed": 0.08}}')
print('  Click:  {{"x": N, "y": N, "click": "left|right|double"}}')
print('  Say:    {{"say": "Hello!", "say_duration": 3}}')
print('  Type:   {{"type": "hello"}}')
print('  Key:    {{"key": "enter"}}')
print('  Scroll: {{"scroll": -3}}')
print('  Drag:   {{"x": N, "y": N, "drag_to": {{"x": N2, "y": N2}}}}')
root.mainloop()
