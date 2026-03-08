"""
AI-controlled DUAL dog cursor overlay v1.0 — two hands!
Left hand (blue dog): dog_cursor_cmd_left.json
Right hand (brown dog): dog_cursor_cmd_right.json

Same command format as dog_cursor_control.py v4.0:
  {"x": N, "y": N, "speed": 0.08, "id": "unique"}    — move
  {"x": N, "y": N, "click": "left", "id": "unique"}   — click
  {"say": "Hello!", "id": "unique"}                    — speech bubble
  {"type": "text", "id": "unique"}                     — type
  {"key": "enter", "id": "unique"}                     — keypress
  {"scroll": -3, "id": "unique"}                       — scroll
  {"x": N, "y": N, "drag_to": {"x": N2, "y": N2}, "id": "unique"} — drag

Each hand operates independently. Both can move and act simultaneously.
Only ONE real mouse cursor exists, so click actions execute sequentially via a shared queue.
"""
import tkinter as tk
from PIL import Image, ImageTk
import json, os, ctypes, time, threading

ctypes.windll.shcore.SetProcessDpiAwareness(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CMD_LEFT = os.path.join(BASE_DIR, "dog_cursor_cmd_left.json")
CMD_RIGHT = os.path.join(BASE_DIR, "dog_cursor_cmd_right.json")

# --- Real mouse input via ctypes ---
user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800

INPUT_KEYBOARD = 1

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]

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
    user32.SetCursorPos(int(x), int(y))

def real_click(x, y, button="left"):
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
    real_move(x, y)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(duration_ms / 1000.0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def real_drag(x1, y1, x2, y2, steps=30):
    real_move(x1, y1)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    for i in range(1, steps + 1):
        t = i / steps
        real_move(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        time.sleep(0.01)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def real_scroll(amount):
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(amount * 120), 0)

def real_type(text):
    for char in text:
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = 0
        inp.union.ki.wScan = ord(char)
        inp.union.ki.dwFlags = 0x0004
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        inp2 = INPUT()
        inp2.type = INPUT_KEYBOARD
        inp2.union.ki.wVk = 0
        inp2.union.ki.wScan = ord(char)
        inp2.union.ki.dwFlags = 0x0004 | 0x0002
        user32.SendInput(1, ctypes.byref(inp2), ctypes.sizeof(INPUT))
        time.sleep(0.02)

def real_keypress(key_name):
    vk = VK_MAP.get(key_name.lower())
    if vk is None:
        if len(key_name) == 1:
            vk = ctypes.windll.user32.VkKeyScanW(ord(key_name)) & 0xFF
        else:
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
    inp2.union.ki.dwFlags = 0x0002
    user32.SendInput(1, ctypes.byref(inp2), ctypes.sizeof(INPUT))

# --- Shared action queue (mouse is singular, so actions are sequential) ---
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
root.withdraw()  # hide root — we use two Toplevels

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x80

def make_click_through(win):
    hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                                         style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)

def load_cursor_image(filename):
    img = Image.open(os.path.join(BASE_DIR, filename)).convert('RGBA')
    bg = Image.new('RGBA', img.size, (255, 0, 255, 255))
    composite = Image.alpha_composite(bg, img)
    return ImageTk.PhotoImage(composite)


class DogHand:
    """One controllable dog cursor with its own window, bubble, and command file."""

    def __init__(self, name, cmd_file, photo, start_x, start_y, bubble_color):
        self.name = name
        self.cmd_file = cmd_file
        self.photo = photo  # keep reference

        # Dog sprite window
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.attributes('-transparentcolor', 'magenta')
        self.win.configure(bg='magenta')
        self.win.geometry(f'32x32+{int(start_x)}+{int(start_y)}')

        lbl = tk.Label(self.win, image=self.photo, bg='magenta', borderwidth=0)
        lbl.pack()

        self.win.update_idletasks()
        make_click_through(self.win)

        # Speech bubble window
        self.bubble_win = tk.Toplevel(root)
        self.bubble_win.overrideredirect(True)
        self.bubble_win.attributes('-topmost', True)
        self.bubble_win.configure(bg='#222222')
        self.bubble_win.geometry('1x1+0+0')
        self.bubble_win.withdraw()

        bubble_frame = tk.Frame(self.bubble_win, bg='#222222', padx=8, pady=5,
                                highlightbackground=bubble_color, highlightthickness=2)
        bubble_frame.pack()

        self.bubble_label = tk.Label(bubble_frame, text='', bg='#222222', fg='#ffffff',
                                     font=('Segoe UI', 10, 'bold'), wraplength=250, justify='left')
        self.bubble_label.pack()

        # Name tag under bubble
        self.name_tag = tk.Label(self.bubble_win, text=f'[{name}]', bg='#222222',
                                  fg=bubble_color, font=('Segoe UI', 7))
        self.name_tag.pack()

        self.bubble_hide_after = None

        # Position state
        self.cur_x = float(start_x)
        self.cur_y = float(start_y)
        self.target_x = self.cur_x
        self.target_y = self.cur_y
        self.speed = 0.08

        # Command tracking
        self.last_mtime = 0
        self.last_cmd_id = None

        # Pending action (click waits for arrival)
        self.pending_action = None
        self.ARRIVE_THRESHOLD = 5

        # Write initial command
        self._write_default()

    def _write_default(self):
        cmd = {"x": int(self.cur_x), "y": int(self.cur_y), "speed": 0.08}
        with open(self.cmd_file, 'w') as f:
            json.dump(cmd, f)

    def show_bubble(self, text, duration=3.0):
        if self.bubble_hide_after:
            root.after_cancel(self.bubble_hide_after)
            self.bubble_hide_after = None
        self.bubble_label.config(text=text)
        self.bubble_win.deiconify()
        self.bubble_win.update_idletasks()
        make_click_through(self.bubble_win)
        self.bubble_hide_after = root.after(int(duration * 1000), self.hide_bubble)
        print(f"  [{self.name}] 💬 \"{text}\" ({duration}s)")

    def hide_bubble(self):
        self.bubble_win.withdraw()
        self.bubble_hide_after = None

    def update_bubble_pos(self):
        if self.bubble_win.winfo_viewable():
            bw = self.bubble_win.winfo_reqwidth()
            bh = self.bubble_win.winfo_reqheight()
            bx = int(self.cur_x + 16 - bw // 2)
            by = int(self.cur_y - bh - 8)
            bx = max(4, min(screen_w - bw - 4, bx))
            by = max(4, min(screen_h - bh - 4, by))
            self.bubble_win.geometry(f'+{bx}+{by}')

    def queue_or_immediate(self, cmd):
        text = cmd.get("type")
        key = cmd.get("key")
        scroll = cmd.get("scroll")

        if text is not None:
            with action_lock:
                action_queue.append(lambda t=str(text): real_type(t))
            print(f"  [{self.name}] -> typing: {text[:30]}...")
            return
        if key is not None:
            with action_lock:
                action_queue.append(lambda k=str(key): real_keypress(k))
            print(f"  [{self.name}] -> keypress: {key}")
            return
        if scroll is not None:
            with action_lock:
                action_queue.append(lambda s=int(scroll): real_scroll(s))
            print(f"  [{self.name}] -> scroll: {scroll}")
            return

        click = cmd.get("click")
        hold = cmd.get("hold")
        drag_to = cmd.get("drag_to")
        x = float(cmd.get("x", self.target_x))
        y = float(cmd.get("y", self.target_y))

        if drag_to is not None:
            dx, dy = float(drag_to["x"]), float(drag_to["y"])
            self.pending_action = (lambda: real_drag(x, y, dx, dy), x, y)
            print(f"  [{self.name}] -> drag ({x},{y}) -> ({dx},{dy})")
        elif click and click != "none":
            if hold:
                self.pending_action = (lambda: real_hold_click(x, y, int(hold)), x, y)
                print(f"  [{self.name}] -> hold-click ({x},{y}) for {hold}ms")
            else:
                self.pending_action = (lambda c=str(click): real_click(x, y, c), x, y)
                print(f"  [{self.name}] -> {click}-click at ({x},{y})")
        else:
            print(f"  [{self.name}] -> move to ({x},{y})")

    def check_arrival(self):
        if self.pending_action is None:
            return
        action_fn, tx, ty = self.pending_action
        dist = ((self.cur_x - tx) ** 2 + (self.cur_y - ty) ** 2) ** 0.5
        if dist < self.ARRIVE_THRESHOLD:
            self.pending_action = None
            with action_lock:
                action_queue.append(action_fn)
            print(f"  [{self.name}] ✓ arrived — executing!")

    def update(self):
        # Check command file
        try:
            mtime = os.path.getmtime(self.cmd_file)
            if mtime != self.last_mtime:
                self.last_mtime = mtime
                with open(self.cmd_file, 'r') as f:
                    cmd = json.load(f)

                cmd_id = cmd.get("id", mtime)
                new_cmd = cmd_id != self.last_cmd_id
                self.last_cmd_id = cmd_id

                self.target_x = float(cmd.get("x", self.target_x))
                self.target_y = float(cmd.get("y", self.target_y))
                self.speed = float(cmd.get("speed", self.speed))

                if new_cmd:
                    say_text = cmd.get("say")
                    if say_text:
                        say_dur = float(cmd.get("say_duration", 3.0))
                        self.show_bubble(str(say_text), say_dur)
                    self.queue_or_immediate(cmd)
        except (json.JSONDecodeError, FileNotFoundError, OSError, ValueError):
            pass

        # Lerp movement
        self.cur_x += (self.target_x - self.cur_x) * self.speed
        self.cur_y += (self.target_y - self.cur_y) * self.speed

        self.check_arrival()

        ix = int(max(0, min(screen_w - 32, self.cur_x)))
        iy = int(max(0, min(screen_h - 32, self.cur_y)))
        self.win.geometry(f'32x32+{ix}+{iy}')

        self.update_bubble_pos()


# --- Load cursor images (keep references!) ---
photo_left = load_cursor_image('dog_cursor_dark.png')
photo_right = load_cursor_image('dog_cursor_light.png')

# Create the two hands
left_hand = DogHand("LEFT", CMD_LEFT, photo_left,
                     screen_w // 3, screen_h // 2, '#8B5E3C')
right_hand = DogHand("RIGHT", CMD_RIGHT, photo_right,
                      2 * screen_w // 3, screen_h // 2, '#D4A76A')

def tick():
    left_hand.update()
    right_hand.update()
    root.after(16, tick)

tick()

print(f"=== DUAL DOG CURSORS v1.0 ===")
print(f"Screen: {screen_w}x{screen_h}")
print(f"Left hand (dark brown):  {CMD_LEFT}")
print(f"Right hand (light brown): {CMD_RIGHT}")
print(f"Both hands share the real mouse — actions queue sequentially.")
print(f"Close this terminal to stop.")
root.mainloop()
