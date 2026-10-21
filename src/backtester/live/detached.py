"""Start a command as a detached background process that outlives its parent (the bot's
cache update, ROADMAP 7.8). Same approach as the Live page's bot launcher (13.4b).

Windows: a short-lived launcher starts the command, so it has no living parent, with
CREATE_BREAKAWAY_FROM_JOB so a job object that kills its tree does not take it along. No
DETACHED_PROCESS: the venv's python.exe is a launcher whose real Python would open a console.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_LAUNCHER = """
import subprocess, sys
log, cmd = sys.argv[1], sys.argv[2:]
flags = 0x00000200 | 0x08000000 | 0x01000000  # new group | no window | breakaway
with open(log, 'ab') as out:
    for f in (flags, flags & ~0x01000000):  # a job may forbid breakaway
        try:
            subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out,
                             stderr=subprocess.STDOUT, creationflags=f)
            break
        except OSError:
            if f == flags & ~0x01000000:
                raise
"""


def spawn_detached(command: list[str], log_file: Path) -> object:
    """Run `command` detached, its output appended to `log_file`."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        launch = [sys.executable, "-c", _LAUNCHER, str(log_file), *command]
        base = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        try:
            return _popen_quiet(launch, base | subprocess.CREATE_BREAKAWAY_FROM_JOB)
        except OSError:  # the parent's job forbids breakaway: still better than not starting
            return _popen_quiet(launch, base)
    with log_file.open("ab") as out:
        return subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
            start_new_session=True,
        )  # fmt: skip


def _popen_quiet(command: list[str], flags: int) -> object:
    return subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
    )  # fmt: skip
