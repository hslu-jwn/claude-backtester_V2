"""Parallel runs must let the process exit (found 2026-10-23: golden --check printed every
result, then hung with idle workers). Workers report progress through a multiprocessing queue;
a worker that exits with unflushed progress items waits for the reader, the main process waits
for the worker at exit: deadlock. Progress items are informational, so workers drop them on
exit instead of waiting."""

from __future__ import annotations

from backtester import runner


class FakeQueue:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel_join_thread(self) -> None:
        self.cancelled = True


def test_worker_never_waits_for_its_progress_queue_at_exit():
    queue = FakeQueue()
    runner._init_worker(queue)
    assert queue.cancelled
    assert runner._worker_queue is queue
