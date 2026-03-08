"""
h4x3r Avatar Overlay v1.0
A desktop overlay that shows h4x3r's avatar with a speech bubble
displaying what the AI is currently doing.

Controlled via h4x3r_status.json:
{
    "say": "Text to display in speech bubble",
    "mood": "normal|happy|thinking|working|sleeping",
    "x": 3300,  (optional - position override)
    "y": 1300,  (optional - position override)
    "id": "unique_id"
}
"""

import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import ctypes
import json
import os
import time
import math

# DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)

AVATAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "h4x3r_avatar.png")
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "h4x3r_status.json")

# Win32 constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x80  # Hide from taskbar

# Mood-based eye colors (will pulse)
MOOD_COLORS = {
    "normal": "#00FF64",
    "happy": "#00FF96",
    "thinking": "#FFD700",
    "working": "#00BFFF",
    "sleeping": "#4444AA",
}


class H4x3rAvatar:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "magenta")
        self.root.configure(bg="magenta")

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # Default position: bottom-right corner
        self.pos_x = self.screen_w - 120
        self.pos_y = self.screen_h - 140

        # State
        self.current_say = ""
        self.current_mood = "normal"
        self.last_id = ""
        self.bubble_timer = 0
        self.bob_phase = 0.0
        self.eye_pulse = 0.0

        # Window size (avatar + bubble space)
        self.win_w = 400
        self.win_h = 180
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.pos_x - self.win_w + 80}+{self.pos_y - self.win_h + 80}")

        # Canvas for drawing everything
        self.canvas = tk.Canvas(
            self.root, width=self.win_w, height=self.win_h,
            bg="magenta", highlightthickness=0, borderwidth=0
        )
        self.canvas.pack()

        # Load avatar image
        self.load_avatar()

        # Make click-through
        self.make_click_through()

        # Draw initial state
        self.draw_frame()

        # Start update loop
        self.update()

        print("h4x3r avatar is alive! Reading status from h4x3r_status.json")
        self.root.mainloop()

    def load_avatar(self):
        img = Image.open(AVATAR_PATH).convert("RGBA")
        # Scale up 2x for visibility
        self.avatar_size = 80
        img = img.resize((self.avatar_size, self.avatar_size), Image.NEAREST)
        bg = Image.new("RGBA", img.size, (255, 0, 255, 255))
        composite = Image.alpha_composite(bg, img)
        self.avatar_photo = ImageTk.PhotoImage(composite)

    def make_click_through(self):
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        )

    def read_status(self):
        try:
            if os.path.exists(STATUS_FILE):
                mtime = os.path.getmtime(STATUS_FILE)
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                cmd_id = data.get("id", "")
                if cmd_id and cmd_id != self.last_id:
                    self.last_id = cmd_id

                    if "say" in data:
                        self.current_say = data["say"]
                        self.bubble_timer = max(180, len(self.current_say) * 6)

                    if "mood" in data:
                        self.current_mood = data.get("mood", "normal")

                    if "x" in data:
                        self.pos_x = data["x"]
                    if "y" in data:
                        self.pos_y = data["y"]
        except (json.JSONDecodeError, OSError):
            pass

    def draw_frame(self):
        self.canvas.delete("all")

        # Avatar position on canvas (bottom-right of canvas)
        avatar_cx = self.win_w - 50
        avatar_cy = self.win_h - 50

        # Gentle bobbing animation
        bob_offset = int(math.sin(self.bob_phase) * 3)

        # Draw avatar
        self.canvas.create_image(
            avatar_cx, avatar_cy + bob_offset,
            image=self.avatar_photo, anchor="center"
        )

        # Eye glow pulse overlay
        self.eye_pulse += 0.08
        pulse = 0.5 + 0.5 * math.sin(self.eye_pulse)
        mood_color = MOOD_COLORS.get(self.current_mood, "#00FF64")

        # Small glow circles where the eyes are (relative to avatar center)
        eye_y = avatar_cy + bob_offset - 14
        glow_size = int(3 + pulse * 2)
        # Left eye glow
        self.canvas.create_oval(
            avatar_cx - 13 - glow_size, eye_y - glow_size,
            avatar_cx - 13 + glow_size, eye_y + glow_size,
            fill=mood_color, outline="", stipple="gray50"
        )
        # Right eye glow
        self.canvas.create_oval(
            avatar_cx + 5 - glow_size, eye_y - glow_size,
            avatar_cx + 5 + glow_size, eye_y + glow_size,
            fill=mood_color, outline="", stipple="gray50"
        )

        # Sleeping Z's
        if self.current_mood == "sleeping":
            z_offset = int(math.sin(self.bob_phase * 2) * 5)
            for i, size in enumerate([8, 11, 14]):
                self.canvas.create_text(
                    avatar_cx + 20 + i * 12,
                    avatar_cy - 30 - i * 15 + z_offset,
                    text="Z", fill="#6666CC",
                    font=("Consolas", size, "bold")
                )

        # Speech bubble
        if self.current_say and self.bubble_timer > 0:
            self.draw_speech_bubble(avatar_cx, avatar_cy + bob_offset)

    def draw_speech_bubble(self, avatar_cx, avatar_cy):
        text = self.current_say
        # Wrap text to fit
        max_chars = 30
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line = (current_line + " " + word).strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        if not lines:
            return

        # Calculate bubble size
        line_height = 16
        padding = 10
        bubble_w = min(max(len(max(lines, key=len)) * 8 + padding * 2, 80), 320)
        bubble_h = len(lines) * line_height + padding * 2

        # Bubble position (to the left of avatar)
        bx = avatar_cx - 50 - bubble_w
        by = avatar_cy - bubble_h // 2 - 20

        # Clamp to screen
        if bx < 5:
            bx = 5

        # Fade effect
        alpha_factor = min(1.0, self.bubble_timer / 30.0)

        # Bubble background (rounded rectangle)
        r = 12
        self.rounded_rect(bx, by, bx + bubble_w, by + bubble_h, r,
                          fill="#1a1a2e", outline="#00FF64", width=2)

        # Bubble tail (triangle pointing to avatar)
        tail_x = bx + bubble_w
        tail_y = by + bubble_h // 2
        self.canvas.create_polygon(
            tail_x, tail_y - 6,
            tail_x + 15, tail_y,
            tail_x, tail_y + 6,
            fill="#1a1a2e", outline="#00FF64", width=1
        )

        # Text
        for i, line in enumerate(lines):
            self.canvas.create_text(
                bx + padding, by + padding + i * line_height,
                text=line, fill="#00FF96",
                font=("Consolas", 10), anchor="nw"
            )

    def rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        self.canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", **kwargs)
        self.canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", **kwargs)
        self.canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", **kwargs)
        self.canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
        self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)

    def update(self):
        # Read status file
        self.read_status()

        # Animation
        self.bob_phase += 0.05

        # Countdown bubble display
        if self.bubble_timer > 0:
            self.bubble_timer -= 1

        # Update window position
        win_x = self.pos_x - self.win_w + 80
        win_y = self.pos_y - self.win_h + 80
        # Clamp to screen
        win_x = max(0, min(self.screen_w - self.win_w, win_x))
        win_y = max(0, min(self.screen_h - self.win_h, win_y))
        self.root.geometry(f"{self.win_w}x{self.win_h}+{win_x}+{win_y}")

        # Redraw
        self.draw_frame()

        # ~30fps
        self.root.after(33, self.update)


if __name__ == "__main__":
    H4x3rAvatar()
