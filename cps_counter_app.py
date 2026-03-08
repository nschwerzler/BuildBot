import ctypes
import threading
import time
import tkinter as tk
import winsound
from tkinter import ttk

VK_LBUTTON = 0x01


class CPSCounterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CPS Counter")
        self.root.geometry("320x170")
        self.root.resizable(False, False)

        self.start_time = time.perf_counter()
        self.total_clicks = 0
        self.running = True

        self.total_var = tk.StringVar(value="Total Clicks: 0")
        self.cps_var = tk.StringVar(value="Overall CPS: 0.00")

        self._build_ui()
        threading.Thread(target=self._poll_clicks, daemon=True).start()
        self._refresh_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=14)
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="Low-Lag Click Counter", font=("Segoe UI", 12, "bold"))
        title.pack(pady=(0, 10))

        total_label = ttk.Label(frame, textvariable=self.total_var, font=("Segoe UI", 11))
        total_label.pack(pady=(0, 8))

        cps_label = ttk.Label(frame, textvariable=self.cps_var, font=("Segoe UI", 11))
        cps_label.pack()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _poll_clicks(self) -> None:
        # Track only button-down edges to avoid double-counting while held.
        user32 = ctypes.windll.user32
        prev_down = False

        while self.running:
            down = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
            if down and not prev_down:
                self.total_clicks += 1
                self._play_click_beep()
            prev_down = down
            time.sleep(0.001)

    def _play_click_beep(self) -> None:
        # Async alias beep keeps feedback snappy without blocking click polling.
        winsound.PlaySound(
            "SystemAsterisk",
            winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_NOSTOP,
        )

    def _refresh_ui(self) -> None:
        elapsed = max(1e-9, time.perf_counter() - self.start_time)
        overall_cps = self.total_clicks / elapsed

        self.total_var.set(f"Total Clicks: {self.total_clicks}")
        self.cps_var.set(f"Overall CPS: {overall_cps:.2f}")

        if self.running:
            self.root.after(16, self._refresh_ui)

    def _on_close(self) -> None:
        self.running = False
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    CPSCounterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
