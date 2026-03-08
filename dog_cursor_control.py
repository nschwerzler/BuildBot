"""
AI-controlled dog cursor overlay.
Reads target position from dog_cursor_cmd.json and moves the dog there.
The AI writes commands, the cursor follows.
"""
import tkinter as tk
from PIL import Image, ImageTk
import json, os, math, ctypes, time

ctypes.windll.shcore.SetProcessDpiAwareness(1)

CMD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dog_cursor_cmd.json")

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

def update_pos():
    global cur_x, cur_y, target_x, target_y, speed, last_mtime

    # Check for new commands
    try:
        mtime = os.path.getmtime(CMD_FILE)
        if mtime != last_mtime:
            last_mtime = mtime
            with open(CMD_FILE, 'r') as f:
                cmd = json.load(f)
            target_x = float(cmd.get("x", target_x))
            target_y = float(cmd.get("y", target_y))
            speed = float(cmd.get("speed", speed))
    except (json.JSONDecodeError, FileNotFoundError, OSError, ValueError):
        pass

    # Smooth lerp toward target
    cur_x += (target_x - cur_x) * speed
    cur_y += (target_y - cur_y) * speed

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
print(f"Dog cursor ready! Screen: {screen_w}x{screen_h}")
print(f"Control file: {CMD_FILE}")
print("Write {{\"x\": N, \"y\": N, \"speed\": 0.08}} to move the dog.")
root.mainloop()
