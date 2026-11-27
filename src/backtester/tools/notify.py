"""Send one Telegram message with the saved live-bot credentials (Windows Credential Manager).

    python -m backtester.tools.notify "text"      # e.g. a very promising strategy (CLAUDE.md)
    python -m backtester.tools.notify --hook      # Claude Code Notification hook: JSON on stdin
    python -m backtester.tools.notify --clear     # UserPromptSubmit / PostToolUse hook: user is back

`--hook` does not send at once: it marks the alert pending and starts a detached waiter that
sends only if nothing cleared it within DELAY_S (the user is away). Hooks cost no model tokens.
Never raises and never prints the configuration: a failed message must not stop a session.
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DELAY_S = 300
# shortcut: one pending file for all sessions, so activity in any session cancels every alert;
# upgrade to one file per session_id if several sessions wait at once.
PENDING = Path(tempfile.gettempdir()) / "claude-notify.pending"


def telegram_sender(text: str) -> None:
    from backtester.jobs.queue import (
        telegram_sender as send,  # lazy: --clear runs on every tool call
    )

    send(text)


def hook_text(payload: dict) -> str:
    """'Claude waiting (<folder>): <message>' from a Claude Code hook payload."""
    folder = Path(payload.get("cwd") or "?").name
    return f"Claude waiting ({folder}): {payload.get('message') or 'needs your input'}"


def start_waiter(token: str) -> None:
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    subprocess.Popen(
        [sys.executable, "-m", "backtester.tools.notify", "--later", token],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def send_if_still_pending(token: str, delay_s: float = DELAY_S) -> None:
    time.sleep(delay_s)
    try:
        data = json.loads(PENDING.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return  # cleared: the user came back
    if data.get("token") == token:
        PENDING.unlink(missing_ok=True)
        telegram_sender(data["text"])


def main(argv: list[str]) -> int:
    try:
        if argv[:1] != ["--clear"]:  # trace which hooks the app actually fires (no message text)
            with PENDING.with_suffix(".log").open("a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {argv[:1]}\n")
        if argv == ["--clear"]:
            PENDING.unlink(missing_ok=True)
        elif argv == ["--hook"]:
            token = str(time.time_ns())
            PENDING.write_text(
                json.dumps({"token": token, "text": hook_text(json.load(sys.stdin))}),
                encoding="utf-8",
            )
            start_waiter(token)
        elif argv[:1] == ["--later"]:
            send_if_still_pending(argv[1])
        elif " ".join(argv).strip():
            telegram_sender(" ".join(argv))
    except Exception as e:  # noqa: BLE001 - a notification never breaks the caller
        print(f"notify: {type(e).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
