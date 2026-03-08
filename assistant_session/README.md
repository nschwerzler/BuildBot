# Guest Mode Toolkit (Consent-Based)

This folder gives you all three workflows together:

1. Shared task board (`tasks.md`)
2. Explicit user-entered logger (`consent_tracker.py`)
3. Screen-share workflow checklist

Default playback speed is set to `2.0x` in `current_task.json`.

## Run

```powershell
D:/BuildBot/.venv/Scripts/python.exe D:/BuildBot/assistant_session/consent_tracker.py
```

## Desktop Preview App

Use this to see exactly what would be shared from your desktop.

```powershell
D:/BuildBot/.venv/Scripts/python.exe D:/BuildBot/assistant_session/desktop_share_preview.py
```

- Live preview shows your desktop view.
- `Share Frame` saves a single image into `assistant_session/shared_frames/`.
- `Auto-share (sec)` + `Start Auto Share` saves frames repeatedly at your chosen interval.
- Minimum auto-share interval is `0.5` seconds.
- `Enable OCR` reads text from each shared frame.
- OCR output is appended to `assistant_session/live_text.log`.

## What This Does

- Stores only what you type in.
- Tracks task/status/notes and playback speed.
- Writes current state to `current_task.json`.
- Appends event history to `session_log.jsonl`.

## Screen-share Checklist (Option 3)

1. Start your call app (Discord/Meet/Teams).
2. Share the app/window you want help on.
3. Keep `tasks.md` updated with your current assignment.
4. Keep playback at `2x` when that helps your review flow.
