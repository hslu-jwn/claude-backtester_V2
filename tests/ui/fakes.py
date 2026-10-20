"""A fake subprocess for the job tests (no process is started)."""

from __future__ import annotations

import threading


class FakeProcess:
    """`Popen` stand-in: stdout yields `lines`, then ends; `poll()` is None until `finish`."""

    def __init__(self, lines=(), returncode=None):
        self._lines = list(lines)
        self.returncode = returncode
        self.pid = 4242
        self.killed = False
        self._gate = threading.Event()
        if returncode is not None:
            self._gate.set()
        self.stdout = self._read()

    def _read(self):
        yield from self._lines
        self._gate.wait(2)

    def poll(self):
        return self.returncode

    def finish(self, code=0):
        self.returncode = code
        self._gate.set()

    def kill_tree(self):
        self.killed = True
        self.finish(1)


class Spawner:
    """Records the calls; returns the next prepared FakeProcess (or a new running one)."""

    def __init__(self, *processes):
        self.processes = list(processes)
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        return self.processes.pop(0) if self.processes else FakeProcess()
