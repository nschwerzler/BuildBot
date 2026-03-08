"""
Matrix Rain Desktop Overlay
Green falling characters across the whole screen. Click-through, always-on-top.
Press Escape or close terminal to stop.
"""
import tkinter as tk
import ctypes
import random
import math

ctypes.windll.shcore.SetProcessDpiAwareness(1)

root = tk.Tk()
root.overrideredirect(True)
root.attributes('-topmost', True)
root.attributes('-transparentcolor', 'black')
root.configure(bg='black')

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(f'{screen_w}x{screen_h}+0+0')

canvas = tk.Canvas(root, width=screen_w, height=screen_h, bg='black',
                   highlightthickness=0, bd=0)
canvas.pack()

# Click-through
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x80
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
    style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)

# Matrix characters - mix of katakana, latin, numbers, symbols
CHARS = list("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモ"
             "ヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
             "@#$%&*=+<>{}[]|/\\~^")

FONT_SIZE = 16
COLS = screen_w // FONT_SIZE
ROWS = screen_h // FONT_SIZE

# Shades of green for trail effect
GREENS = [
    '#001100', '#002200', '#003300', '#004400', '#005500',
    '#006600', '#007700', '#008800', '#00aa00', '#00cc00',
    '#00ee00', '#00ff00', '#33ff33', '#66ff66', '#aaffaa', '#ffffff'
]

class Drop:
    def __init__(self, col):
        self.col = col
        self.x = col * FONT_SIZE
        self.reset()

    def reset(self):
        self.y = random.randint(-ROWS * 2, -1) * FONT_SIZE
        self.speed = random.uniform(1.5, 5.0)
        self.trail_len = random.randint(8, 25)
        self.chars = [random.choice(CHARS) for _ in range(self.trail_len)]
        self.tick = 0

    def update(self):
        self.y += self.speed * FONT_SIZE * 0.15
        self.tick += 1
        # Randomly mutate characters in trail
        if self.tick % 3 == 0:
            idx = random.randint(0, self.trail_len - 1)
            self.chars[idx] = random.choice(CHARS)
        if self.y - self.trail_len * FONT_SIZE > screen_h:
            self.reset()

drops = [Drop(c) for c in range(COLS)]

# Pre-create text items for performance - use a pool
text_pool = []
POOL_SIZE = COLS * 20  # enough for all visible chars

for i in range(POOL_SIZE):
    tid = canvas.create_text(0, 0, text='', fill='#00ff00',
                              font=('Consolas', FONT_SIZE - 2), anchor='nw')
    text_pool.append(tid)
    canvas.itemconfigure(tid, state='hidden')

pool_idx = [0]

def animate():
    pool_idx[0] = 0
    # Hide all
    for tid in text_pool:
        canvas.itemconfigure(tid, state='hidden')

    for drop in drops:
        drop.update()
        for i in range(drop.trail_len):
            cy = drop.y - i * FONT_SIZE
            if cy < -FONT_SIZE or cy > screen_h:
                continue
            if pool_idx[0] >= POOL_SIZE:
                break

            tid = text_pool[pool_idx[0]]
            pool_idx[0] += 1

            # Head character is white/bright, trail fades to dark green
            if i == 0:
                color = '#ffffff'
            elif i == 1:
                color = '#aaffaa'
            elif i < 4:
                color = '#00ff00'
            elif i < 8:
                color = '#00cc00'
            elif i < 12:
                color = '#008800'
            elif i < 16:
                color = '#005500'
            else:
                color = '#003300'

            canvas.coords(tid, drop.x, cy)
            canvas.itemconfigure(tid, text=drop.chars[i % len(drop.chars)],
                               fill=color, state='normal')

    root.after(50, animate)

def on_escape(e):
    root.destroy()

root.bind('<Escape>', on_escape)

print("Matrix Rain activated! Press Escape to stop.")
print(f"Screen: {screen_w}x{screen_h}, {COLS} columns, pool: {POOL_SIZE}")
animate()
root.mainloop()
