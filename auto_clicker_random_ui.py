import ctypes
import random
import threading
import time
import tkinter as tk
from tkinter import ttk

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class RandomClicker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Random Interval Auto Clicker")
        self.root.geometry("340x220")
        self.running = False

        self.min_cps = tk.DoubleVar(value=8.0)
        self.max_cps = tk.DoubleVar(value=18.0)
        self.status_var = tk.StringVar(value="Status: STOP")

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, textvariable=self.status_var, font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Min CPS").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.min_cps).pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text="Max CPS").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.max_cps).pack(fill="x", pady=(0, 12))

        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Start", command=self.start).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ttk.Button(row, text="Stop", command=self.stop).pack(side="left", expand=True, fill="x", padx=(6, 0))

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.status_var.set("Status: START")
        threading.Thread(target=self.loop, daemon=True).start()

    def stop(self) -> None:
        self.running = False
        self.status_var.set("Status: STOP")

    def loop(self) -> None:
        user32 = ctypes.windll.user32
        mouse_event = user32.mouse_event

        while self.running:
            lo = max(0.1, float(self.min_cps.get()))
            hi = max(lo, float(self.max_cps.get()))
            cps = random.uniform(lo, hi)
            interval = 1.0 / cps

            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(interval)

    def on_close(self) -> None:
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    RandomClicker(root)
    root.mainloop()
