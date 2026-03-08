import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class TimerClicker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Timer Auto Clicker")
        self.root.geometry("340x250")
        self.running = False

        self.delay_var = tk.DoubleVar(value=3.0)
        self.duration_var = tk.DoubleVar(value=10.0)
        self.interval_var = tk.DoubleVar(value=0.01)
        self.status_var = tk.StringVar(value="Status: STOP")

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, textvariable=self.status_var, font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Start delay (sec)").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.delay_var).pack(fill="x", pady=(0, 6))
        ttk.Label(frame, text="Run duration (sec)").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.duration_var).pack(fill="x", pady=(0, 6))
        ttk.Label(frame, text="Click interval (sec)").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.interval_var).pack(fill="x", pady=(0, 12))

        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Start", command=self.start).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ttk.Button(row, text="Stop", command=self.stop).pack(side="left", expand=True, fill="x", padx=(6, 0))

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.status_var.set("Status: WAITING")
        threading.Thread(target=self.loop, daemon=True).start()

    def stop(self) -> None:
        self.running = False
        self.status_var.set("Status: STOP")

    def loop(self) -> None:
        delay = max(0.0, float(self.delay_var.get()))
        duration = max(0.0, float(self.duration_var.get()))
        interval = max(0.0, float(self.interval_var.get()))

        user32 = ctypes.windll.user32
        mouse_event = user32.mouse_event

        start_wait = time.time()
        while self.running and time.time() - start_wait < delay:
            time.sleep(0.01)

        if not self.running:
            return

        self.status_var.set("Status: START")
        end_time = time.time() + duration
        while self.running and time.time() < end_time:
            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if interval > 0:
                time.sleep(interval)

        self.stop()

    def on_close(self) -> None:
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    TimerClicker(root)
    root.mainloop()
