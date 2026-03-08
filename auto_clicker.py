import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class AutoClickerUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Auto Clicker")
        self.root.geometry("280x160")
        self.root.resizable(False, False)

        self._clicking = False
        self._thread: threading.Thread | None = None

        self.status_var = tk.StringVar(value="Status: STOP")
        self.interval_var = tk.DoubleVar(value=0.05)
        self.turbo_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        status_label = ttk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 12, "bold"),
            anchor="center",
        )
        status_label.pack(fill="x", pady=(0, 12))

        row = ttk.Frame(container)
        row.pack(fill="x", pady=(0, 12))

        ttk.Label(row, text="Interval (sec):").pack(side="left")
        ttk.Entry(row, textvariable=self.interval_var, width=8).pack(side="left", padx=(8, 0))

        ttk.Checkbutton(container, text="Turbo (max speed)", variable=self.turbo_var).pack(
            anchor="w", pady=(0, 10)
        )

        buttons = ttk.Frame(container)
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Start", command=self.start_clicking).pack(
            side="left", fill="x", expand=True, padx=(0, 6)
        )
        ttk.Button(buttons, text="Stop", command=self.stop_clicking).pack(
            side="left", fill="x", expand=True, padx=(6, 0)
        )

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_clicking(self) -> None:
        if self._clicking:
            return

        interval = max(0.0, float(self.interval_var.get()))
        self.interval_var.set(interval)

        self._clicking = True
        self.status_var.set("Status: START")
        self._thread = threading.Thread(target=self._click_loop, daemon=True)
        self._thread.start()

    def stop_clicking(self) -> None:
        self._clicking = False
        self.status_var.set("Status: STOP")

    def _click_loop(self) -> None:
        user32 = ctypes.windll.user32
        mouse_event = user32.mouse_event

        while self._clicking:
            if self.turbo_var.get():
                # Batch many clicks before checking state again for higher throughput.
                for _ in range(200):
                    if not self._clicking:
                        break
                    mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0)
                continue

            interval = self.interval_var.get()
            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if interval > 0:
                time.sleep(interval)

    def on_close(self) -> None:
        self.stop_clicking()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    AutoClickerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
