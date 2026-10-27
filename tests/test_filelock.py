import multiprocessing as mp
from pathlib import Path

from backtester.filelock import file_lock

WORKERS = 8
ROUNDS = 40


def race_worker(root, barrier):
    # Every round all workers hit the same brand-new lock file at once.
    for i in range(ROUNDS):
        barrier.wait(60)
        counter = Path(root) / f"count{i}.txt"
        with file_lock(Path(root) / f"new{i}.lock"):
            value = int(counter.read_text()) if counter.exists() else 0
            counter.write_text(str(value + 1))


def test_concurrent_first_use_of_a_new_lock_file(tmp_path):
    ctx = mp.get_context("spawn")
    barrier = ctx.Barrier(WORKERS)
    processes = [ctx.Process(target=race_worker, args=(str(tmp_path), barrier)) for _ in range(WORKERS)]
    try:
        for p in processes:
            p.start()
        for p in processes:
            p.join(180)
        assert [p.exitcode for p in processes] == [0] * WORKERS  # None = still running
        assert all((tmp_path / f"count{i}.txt").read_text() == str(WORKERS) for i in range(ROUNDS))
    finally:
        for p in processes:
            if p.is_alive():
                p.terminate()
