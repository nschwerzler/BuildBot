#!/usr/bin/env python3
"""Desktop Share Preview (consent-based).

Shows a live preview of the local desktop and only saves frames when the user
explicitly clicks "Share Frame".
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from PIL import ImageGrab, ImageTk


BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "shared_frames"
LOG_FILE = BASE_DIR / "session_log.jsonl"


class DesktopSharePreviewApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Desktop Share Preview (Consent)")
        self.root.geometry("980x700")

        OUT_DIR.mkdir(parents=True, exist_ok=True)

        self.preview_label = tk.Label(root, text="Starting preview...", bg="#222", fg="#fff")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        controls = tk.Frame(root)
        controls.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="Preview running. Nothing shared yet.")
        status = tk.Label(root, textvariable=self.status_var, anchor="w")
        status.pack(fill=tk.X, padx=10, pady=(0, 8))

        tk.Button(controls, text="Share Frame", command=self.share_frame).pack(side=tk.LEFT)
        tk.Button(controls, text="Open Shared Folder", command=self.open_shared_folder).pack(side=tk.LEFT, padx=8)
        tk.Button(controls, text="Pause Preview", command=self.toggle_preview).pack(side=tk.LEFT)

        self.preview_running = True
        self.current_image = None
        self.current_photo = None

        self.root.after(200, self.update_preview)

    def log_event(self, event: str, payload: dict) -> None:
        row = {
            "time": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "payload": payload,
        }
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def update_preview(self) -> None:
        if self.preview_running:
            try:
                img = ImageGrab.grab(all_screens=True)
                self.current_image = img

                display = img.copy()
                display.thumbnail((940, 560))

                self.current_photo = ImageTk.PhotoImage(display)
                self.preview_label.configure(image=self.current_photo, text="")
            except Exception as exc:
                self.preview_label.configure(text=f"Preview error: {exc}")

        self.root.after(350, self.update_preview)

    def share_frame(self) -> None:
        if self.current_image is None:
            messagebox.showwarning("No frame", "No frame available yet.")
            return

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUT_DIR / f"desktop_share_{stamp}.png"
        self.current_image.save(path)

        self.status_var.set(f"Shared frame saved: {path.name}")
        self.log_event("share_frame", {"file": str(path)})

    def open_shared_folder(self) -> None:
        path = str(OUT_DIR)
        self.root.after(10, lambda: self.root.tk.call("tk", "messageBox", "-message", f"Shared folder:\n{path}", "-type", "ok"))

    def toggle_preview(self) -> None:
        self.preview_running = not self.preview_running
        state = "running" if self.preview_running else "paused"
        self.status_var.set(f"Preview {state}. Manual sharing only.")
        self.log_event("toggle_preview", {"state": state})


def main() -> None:
    root = tk.Tk()
    DesktopSharePreviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
