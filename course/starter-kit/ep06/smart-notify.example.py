#!/usr/bin/env python3
"""Розумні сповіщення Claude Code (Starter Kit — Серія 06): чотири сита, як у claude-notifier.

Один скрипт на три події — UserPromptSubmit, Stop і PermissionRequest
(глобальний ~/.claude/settings.json, приклад — у settings.hooks.example.json):
    {"type": "command", "command": "python3 \"$HOME/.claude/hooks/smart-notify.py\""}

Сита:
  1. stop_hook_active — Stop, який уже продовжив роботу агента, не дзеленчить удруге.
  2. agent_id — події субагентів мовчать; сповіщаємо лише про головного агента.
  3. поріг тривалості — UserPromptSubmit ставить мітку старту; швидкі відповіді тихі.
  4. фокус — якщо термінал чи редактор зараз попереду, ви й так усе бачите.
Сповіщення: macOS — osascript, Linux — notify-send. Завжди exit 0: нотифікатор нічого не блокує.
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MIN_SECONDS = 15
FOCUS_APPS = {"Terminal", "iTerm2", "Ghostty", "WezTerm", "Code", "Cursor", "kitty", "Alacritty"}


def mark(session: str) -> Path:
    return Path(tempfile.gettempdir()) / f"claude-notify-{session or 'x'}"


def frontmost_app() -> str:
    if platform.system() != "Darwin":
        return ""
    script = (
        'tell application "System Events" to get name of first application process '
        "whose frontmost is true"
    )
    try:
        return subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=2
        ).stdout.strip()
    except Exception:
        return ""


def notify(title: str, text: str) -> None:
    if platform.system() == "Darwin":
        subprocess.run(
            [
                "osascript",
                "-e",
                f"display notification {json.dumps(text)} with title {json.dumps(title)} "
                'sound name "Glass"',
            ],
            timeout=5,
        )
    else:
        subprocess.run(["notify-send", title, text], timeout=5)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    event = data.get("hook_event_name", "")
    session = data.get("session_id", "")

    if event == "UserPromptSubmit":
        mark(session).write_text(str(time.time()))
        return
    if data.get("stop_hook_active"):  # сито 1
        return
    if data.get("agent_id"):  # сито 2
        return
    if event == "PermissionRequest" and data.get("tool_name") == "AskUserQuestion":
        return  # питання ловить окремий PreToolUse-хук
    try:  # сито 3
        if time.time() - float(mark(session).read_text()) < MIN_SECONDS:
            return
    except (OSError, ValueError):
        pass
    if frontmost_app() in FOCUS_APPS:  # сито 4
        return

    project = os.path.basename(data.get("cwd") or os.getcwd())
    if event == "Stop":
        notify(f"Claude · {project}", "Готово — агент чекає на вас")
    elif event == "PermissionRequest":
        notify(f"Claude · {project}", f"Потрібен дозвіл: {data.get('tool_name', 'інструмент')}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
