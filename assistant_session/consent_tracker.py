#!/usr/bin/env python3
"""Consent-based session tracker.

This tool only logs what the user explicitly enters.
It does not read screens, keystrokes, or private app data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CURRENT_FILE = BASE_DIR / "current_task.json"
LOG_FILE = BASE_DIR / "session_log.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SessionState:
    task: str = ""
    assigned_by: str = "d0g3"
    status: str = "todo"
    priority: str = "normal"
    needed_context: str = ""
    playback_speed: float = 2.0
    updated_at: str = ""


def load_state() -> SessionState:
    if not CURRENT_FILE.exists():
        state = SessionState(updated_at=utc_now())
        save_state(state)
        return state
    raw = json.loads(CURRENT_FILE.read_text(encoding="utf-8"))
    return SessionState(**raw)


def save_state(state: SessionState) -> None:
    state.updated_at = utc_now()
    CURRENT_FILE.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def append_log(event_type: str, payload: dict[str, Any]) -> None:
    row = {
        "time": utc_now(),
        "event": event_type,
        "payload": payload,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def show_state(state: SessionState) -> None:
    print("\nCurrent Session")
    print(f"- task: {state.task}")
    print(f"- assigned_by: {state.assigned_by}")
    print(f"- status: {state.status}")
    print(f"- priority: {state.priority}")
    print(f"- needed_context: {state.needed_context}")
    print(f"- playback_speed: {state.playback_speed}x")
    print(f"- updated_at: {state.updated_at}")


def set_task(state: SessionState) -> None:
    state.task = prompt("Task", state.task)
    state.assigned_by = prompt("Assigned by", state.assigned_by)
    state.priority = prompt("Priority (low/normal/high)", state.priority)
    state.status = prompt("Status (todo/in-progress/done)", state.status)
    state.needed_context = prompt("Needed context", state.needed_context)
    speed_raw = prompt("Playback speed", str(state.playback_speed))
    try:
        state.playback_speed = float(speed_raw)
    except ValueError:
        pass
    save_state(state)
    append_log("set_task", asdict(state))
    print("Saved current task.")


def set_status(state: SessionState) -> None:
    state.status = prompt("New status", state.status)
    save_state(state)
    append_log("set_status", {"status": state.status})
    print("Status updated.")


def add_note() -> None:
    note = prompt("Note")
    if not note:
        print("Skipped empty note.")
        return
    append_log("note", {"text": note})
    print("Note added.")


def main() -> None:
    state = load_state()
    while True:
        print("\n=== Consent Tracker ===")
        print("1) Show current task")
        print("2) Set/update task")
        print("3) Update status")
        print("4) Add note")
        print("5) Set playback speed")
        print("6) Exit")
        try:
            choice = input("Choose: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if choice == "1":
            show_state(state)
        elif choice == "2":
            set_task(state)
        elif choice == "3":
            set_status(state)
        elif choice == "4":
            add_note()
        elif choice == "5":
            speed_raw = prompt("Playback speed", str(state.playback_speed))
            try:
                state.playback_speed = float(speed_raw)
                save_state(state)
                append_log("set_playback_speed", {"playback_speed": state.playback_speed})
                print(f"Playback speed set to {state.playback_speed}x")
            except ValueError:
                print("Invalid number.")
        elif choice == "6":
            print("Bye.")
            return
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
