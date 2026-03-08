import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class BurstClicker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Burst Auto Clicker")
        self.root.geometry("320x200")
        self.running = False

        self.burst_var = tk.IntVar(value=25)
        self.pause_var = tk.DoubleVar(value=0.2)
        self.status_var = tk.StringVar(value="Status: STOP")

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, textvariable=self.status_var, font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Clicks per burst").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.burst_var).pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text="Pause between bursts (sec)").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.pause_var).pack(fill="x", pady=(0, 12))

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
            burst = max(1, int(self.burst_var.get()))
            pause = max(0.0, float(self.pause_var.get()))

            for _ in range(burst):
                if not self.running:
                    break
                mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(pause)

    def on_close(self) -> None:
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    BurstClicker(root)
    root.mainloop()
