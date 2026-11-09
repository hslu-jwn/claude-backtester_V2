"""Send one Telegram message with the saved live-bot credentials (Windows Credential Manager).

    python -m backtester.tools.notify "text"      # e.g. a very promising strategy (CLAUDE.md)
    python -m backtester.tools.notify --hook      # Claude Code Notification hook: JSON on stdin

Never raises and never prints the configuration: a failed message must not stop a session.
"""

import json
import sys
from pathlib import Path

from backtester.jobs.queue import telegram_sender


def hook_text(payload: dict) -> str:
    """'Claude waiting (<folder>): <message>' from a Claude Code hook payload."""
    folder = Path(payload.get("cwd") or "?").name
    return f"Claude waiting ({folder}): {payload.get('message') or 'needs your input'}"


def main(argv: list[str]) -> int:
    try:
        text = hook_text(json.load(sys.stdin)) if argv == ["--hook"] else " ".join(argv)
        if text.strip():
            telegram_sender(text)
    except Exception as e:  # noqa: BLE001 - a notification never breaks the caller
        print(f"notify: {type(e).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
