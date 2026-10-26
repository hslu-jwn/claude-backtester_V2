"""Persistent heavy-job queue. Spec: research-runner.md > Job queue."""

import logging
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
import warnings
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from backtester.filelock import file_lock
from backtester.jobs.config import DEFAULT_CONFIG, QueueConfig
from backtester.jobs.processes import process_identity, terminate_tree
from backtester.jobs.storage import atomic_json, read_json
from backtester.jobs.temperature import TemperatureGuard, read_temperature
from backtester.paths import HOME_DIR, RESULTS_DIR
from backtester.tools.lanes import resolve_cwd

LOGGER = logging.getLogger(__name__)

STATES = ("pending", "running", "done", "failed", "cancelled")


def utc_now():
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class Job:
    id: str
    name: str
    argv: list[str]
    priority: int = 0
    state: str = "pending"
    attempts: int = 0
    max_attempts: int = DEFAULT_CONFIG.max_attempts
    pid: int | None = None
    started: str | None = None
    ended: str | None = None
    exit_code: int | None = None
    log: str = ""
    process_started: float | None = None
    starting: str | None = None
    cwd: str | None = None  # None = the V2 root; else the path of a registered lane (tools/lanes)


class RunnerLock:
    def __init__(self, root: Path):
        self.root = root

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.guard = file_lock(self.root / "runner.guard", timeout=0)
        try:
            self.guard.__enter__()
        except TimeoutError as exc:
            raise RuntimeError("A queue runner is already running") from exc
        self.path = self.root / "runner.lock"
        try:
            try:
                self.last_release = read_json(self.root / "runner.release.json")["released_ns"]
            except (FileNotFoundError, ValueError, TypeError, KeyError):
                self.last_release = 0
            self.path.write_text(str(os.getpid()), encoding="ascii")
        except BaseException:
            self.guard.__exit__(*sys.exc_info())
            raise
        return self

    def __exit__(self, *exc):
        try:
            atomic_json(self.root / "runner.release.json", {"released_ns": time.time_ns()})
            self.path.unlink(missing_ok=True)
        finally:
            self.guard.__exit__(*exc)


class Queue:
    def __init__(self, root: Path = RESULTS_DIR / "queue", home: Path = HOME_DIR):
        self.root = Path(root).resolve()
        self.home = Path(home).resolve()  # the V2 root: default cwd, holds lanes.json
        self.broken = []
        self._warned_broken = set()
        (self.root / "jobs").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(exist_ok=True)

    def path(self, job_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", job_id):
            raise ValueError("Invalid job ID")
        return self.root / "jobs" / f"{job_id}.json"

    @contextmanager
    def locked(self, job_id):
        with file_lock(self.path(job_id).with_suffix(".lock")):
            yield

    def get(self, job_id):
        path = self.path(job_id)
        try:
            job = Job(**read_json(path))
            if job.id != job_id or job.state not in STATES:
                raise ValueError("Invalid job identity or state")
            return replace(job, log=str(self.root.parent / job.log))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Broken job file: {path.name}") from exc

    def save(self, job):
        """Caller must hold the job lock when updating an existing record."""
        data = asdict(job)
        data["log"] = (
            (self.root / "logs" / f"{job.id}.log").relative_to(self.root.parent).as_posix()
        )
        atomic_json(self.path(job.id), data)

    def update(self, job_id, change):
        with self.locked(job_id):
            job = change(self.get(job_id))
            self.save(job)
            return job

    def jobs(self):
        jobs = []
        self.broken = []
        for path in sorted((self.root / "jobs").glob("*.json")):
            try:
                jobs.append(self.get(path.stem))
            except FileNotFoundError:  # clean may have removed it
                pass
            except ValueError:
                self.broken.append(path.name)
                if path.name not in self._warned_broken:
                    LOGGER.warning("Skipping broken job file: %s", path.name)
                    self._warned_broken.add(path.name)
        return jobs

    def pending(self):
        return sorted(
            (j for j in self.jobs() if j.state == "pending"), key=lambda j: (-j.priority, j.id)
        )

    def add(
        self, argv, *, name=None, priority=0, max_attempts=DEFAULT_CONFIG.max_attempts, cwd=None
    ):
        argv = list(argv)
        if (
            not argv
            or not all(isinstance(a, str) for a in argv)
            or not re.fullmatch(r"backtester\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", argv[0])
        ):
            raise ValueError("Only modules under backtester. are accepted")
        if max_attempts < 1:
            raise ValueError("max-attempts must be at least 1")
        cwd = resolve_cwd(cwd, self.home)  # the V2 root (None) or a registered lane, else refused
        with file_lock(self.root / "add.lock"):
            if any(
                j.argv == argv and j.cwd == cwd and j.state in ("pending", "running")
                for j in self.jobs()
            ):
                warnings.warn("A pending/running job has the same argv", stacklevel=2)
            job_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ_") + uuid.uuid4().hex[:8]
            job = Job(
                job_id,
                name or argv[0].rsplit(".", 1)[-1],
                argv,
                priority=priority,
                max_attempts=max_attempts,
                log=str(self.root / "logs" / f"{job_id}.log"),
                cwd=cwd,
            )
            self.save(job)
            return job

    def cancel(self, job_id, terminate=terminate_tree):
        def change(j):
            if j.state not in ("pending", "running"):
                raise ValueError("Only pending/running jobs can be cancelled")
            if (
                j.state == "running"
                and j.process_started is not None
                and process_identity(j.pid) == j.process_started
            ):
                terminate(j.pid)
            return replace(j, state="cancelled", ended=utc_now())

        return self.update(job_id, change)

    def retry(self, job_id):
        def change(j):
            if j.state not in ("failed", "cancelled"):
                raise ValueError("Only failed/cancelled jobs can be retried")
            if (
                j.state == "cancelled"
                and j.process_started is not None
                and process_identity(j.pid) == j.process_started
            ):
                raise ValueError("Cancelled child is still exiting; retry shortly")
            return replace(
                j,
                state="pending",
                attempts=0,
                pid=None,
                started=None,
                ended=None,
                exit_code=None,
                process_started=None,
                starting=None,
            )

        return self.update(job_id, change)

    def stop(self):
        (self.root / "stop").touch()

    def clean(self, days):
        if not math.isfinite(days) or days < 0:
            raise ValueError("days must be finite and nonnegative")
        cutoff = datetime.now(UTC) - timedelta(days=days)
        count = 0
        for j in self.jobs():
            with self.locked(j.id):
                try:
                    j = self.get(j.id)
                except FileNotFoundError:
                    continue
                if j.state == "done" and j.ended and datetime.fromisoformat(j.ended) < cutoff:
                    self.path(j.id).unlink()
                    (self.root / "logs" / f"{j.id}.log").unlink(missing_ok=True)
                    count += 1
            if not self.path(j.id).exists():
                self.path(j.id).with_suffix(".lock").unlink(missing_ok=True)
        return count


def telegram_sender(text):
    # Import the existing integration only; never inspect or log its configuration.
    from backtester.live.telegram import TelegramClient, load_telegram

    config = load_telegram()
    if config is not None:
        TelegramClient(config).send(text)


class Runner:
    def __init__(
        self,
        queue=None,
        *,
        workers=DEFAULT_CONFIG.workers,
        max_temp=DEFAULT_CONFIG.max_temp,
        resume_temp=DEFAULT_CONFIG.resume_temp,
        poll=DEFAULT_CONFIG.poll,
        sensor_url=DEFAULT_CONFIG.sensor_url,
        sensor_timeout=DEFAULT_CONFIG.sensor_timeout,
        sensor=None,
        sender=None,
        popen=subprocess.Popen,
        clock=time.monotonic,
        identity=process_identity,
    ):
        if workers < 1 or not math.isfinite(poll) or poll <= 0:
            raise ValueError("workers and poll must be positive")
        self.queue = queue if queue is not None else Queue()
        self.config = QueueConfig(
            workers=workers,
            max_temp=max_temp,
            resume_temp=resume_temp,
            poll=poll,
            sensor_url=sensor_url,
            sensor_timeout=sensor_timeout,
        )
        self.workers, self.poll = workers, poll
        self.sensor = (
            sensor
            if sensor is not None
            else lambda: read_temperature(self.config.sensor_url, self.config.sensor_timeout)
        )
        self.sender = sender if sender is not None else telegram_sender
        self.popen, self.clock, self.identity = popen, clock, identity
        self.guard = TemperatureGuard(max_temp, resume_temp)
        self.active = {}  # id -> (Popen or None for recovered child, log stream)
        self.stopping = False
        self.temperature = None
        self.warning = None
        self.pause_since = None
        self.pause_notified = False

    def log(self, text):
        with (self.queue.root / "runner.log").open("a", encoding="utf-8") as stream:
            stream.write(f"{utc_now()} {text}\n")

    def notify(self, text):
        try:
            self.sender(text)
        except Exception:  # noqa: BLE001 -- sender errors must never abort the queue
            # Sender exceptions can contain URLs with secrets; never log their text.
            self.log("Telegram send failed")

    def failed(self, j):
        if j.state == "failed":
            name = re.sub(r"[^\w .-]", "", j.name)[:80]
            self.notify(f"Queue: job {name} failed (exit {j.exit_code}, {j.attempts} attempts)")

    def launch_target(self, j):
        """(cwd, env) of a job. The default is the V2 root with the runner's environment
        (env None). A lane job runs in its worktree with BACKTESTER_HOME = the V2 root (data and
        results stay shared) and the lane's `src` first on PYTHONPATH (its code, not V2's).
        Raises ValueError when the lane is no longer registered."""
        lane = resolve_cwd(j.cwd, self.queue.home)
        if lane is None:
            return self.queue.home, None
        env = dict(os.environ)
        env["BACKTESTER_HOME"] = str(self.queue.home)
        old = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(Path(lane) / "src") + (os.pathsep + old if old else "")
        return Path(lane), env

    def identity_matches(self, j):
        return j.process_started is not None and self.identity(j.pid) == j.process_started

    def finish(self, j, exit_code):
        return replace(
            j,
            state=(
                "done"
                if exit_code == 0
                else "failed"
                if j.attempts >= j.max_attempts
                else "pending"
            ),
            ended=utc_now(),
            exit_code=exit_code,
        )

    def recover(self):
        for j in self.queue.jobs():
            with self.queue.locked(j.id):
                j = self.queue.get(j.id)
                if j.state != "running":
                    continue
                if self.identity_matches(j):
                    self.active[j.id] = (None, None)
                else:
                    j = self.finish(j, None)
                    self.queue.save(j)
                    self.failed(j)

    def tick(self):
        if (self.queue.root / "stop").exists():
            self.stopping = True
        for job_id, (child, stream) in list(self.active.items()):
            with self.queue.locked(job_id):
                j = self.queue.get(job_id)
                code = child.poll() if child is not None else None
                alive = code is None if child is not None else self.identity_matches(j)
                if alive:
                    continue
                if stream is not None:
                    stream.close()
                del self.active[job_id]
                if j.state == "running":
                    j = self.finish(j, code)
                    self.queue.save(j)
                    self.failed(j)
        self.temperature = self.sensor()
        if self.temperature is None:
            if self.warning is None:
                self.log("CPU temperature unavailable; continuing work")
            self.warning = "CPU temperature unavailable; continuing work"
        else:
            self.warning = None
        self.guard.update(self.temperature)
        pending = self.queue.pending()
        held = self.guard.paused and bool(pending) and not self.stopping
        if held:
            if self.pause_since is None:
                self.pause_since = self.clock()
            if (
                self.clock() - self.pause_since > self.config.pause_seconds
                and not self.pause_notified
            ):
                self.notify(f"Queue: paused 30 min, CPU {self.temperature:g} °C")
                self.pause_notified = True
        else:
            self.pause_since = None
            if not self.guard.paused:
                self.pause_notified = False
        if not self.stopping and not self.guard.paused:
            for j in pending:
                if (
                    self.stopping
                    or (self.queue.root / "stop").exists()
                    or len(self.active) >= self.workers
                ):
                    break
                with self.queue.locked(j.id):
                    j = self.queue.get(j.id)
                    if j.state != "pending" or j.id in self.active:
                        continue
                    j = replace(
                        j,
                        state="running",
                        attempts=j.attempts + 1,
                        pid=None,
                        starting=utc_now(),
                        started=None,
                        ended=None,
                        exit_code=None,
                        process_started=None,
                    )
                    self.queue.save(j)
                    try:
                        cwd, env = self.launch_target(j)
                    except ValueError as exc:  # the lane was removed after the job was queued
                        with Path(j.log).open("ab") as stream:
                            stream.write(f"{utc_now()} not started: {exc}\n".encode())
                        j = replace(j, state="failed", ended=utc_now(), exit_code=-1)
                        self.queue.save(j)
                        self.failed(j)
                        continue
                    try:
                        with Path(j.log).open("ab") as stream:
                            options = {
                                "cwd": cwd,
                                "stdout": stream,
                                "stderr": subprocess.STDOUT,
                            }
                            if env is not None:
                                options["env"] = env
                            if os.name == "nt":
                                options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                            else:
                                options["start_new_session"] = True
                            child = self.popen([sys.executable, "-m", *j.argv], **options)
                    except OSError:
                        j = self.finish(j, -1)
                        self.queue.save(j)
                        self.failed(j)
                        continue
                    try:
                        self.queue.save(
                            replace(
                                j,
                                pid=child.pid,
                                started=utc_now(),
                                process_started=self.identity(child.pid),
                            )
                        )
                    except BaseException:
                        # A failed PID write must not leave an untracked child behind.
                        terminate_tree(child.pid)
                        child.wait(timeout=10)
                        raise
                    self.active[j.id] = (child, None)
        atomic_json(self.queue.root / "status.json", self.status())

    def status(self):
        jobs = self.queue.jobs()
        counts = Counter(j.state for j in jobs)
        running = []
        for j in jobs:
            if j.state == "running":
                elapsed = (
                    (datetime.now(UTC) - datetime.fromisoformat(j.started)).total_seconds()
                    if j.started
                    else 0
                )
                running.append({"id": j.id, "name": j.name, "pid": j.pid, "elapsed": elapsed})
        return {
            "pid": os.getpid(),
            "updated": utc_now(),
            "counts": {s: counts[s] for s in STATES},
            "broken": self.queue.broken.copy(),
            "running": running,
            "temperature": self.temperature,
            "warning": self.warning,
            "paused": self.guard.paused,
            "stopping": self.stopping,
        }

    def run(self, *, drain=False):
        with RunnerLock(self.queue.root) as lock:
            stop = self.queue.root / "stop"
            if stop.exists():
                if stop.stat().st_mtime_ns < lock.last_release:
                    stop.unlink(missing_ok=True)
                else:
                    self.stopping = True
                    self.log("Stop request present at startup; draining without new launches")
            old_handler = None
            if threading.current_thread() is threading.main_thread():
                old_handler = signal.signal(
                    signal.SIGINT, lambda *_: setattr(self, "stopping", True)
                )
            try:
                self.recover()
                while True:
                    self.tick()
                    if not self.active and (self.stopping or (drain and not self.queue.pending())):
                        break
                    time.sleep(self.poll)
            except Exception:
                self.notify("Queue: runner crashed")
                self.log("Queue runner crashed; restart to recover jobs")
                raise
            finally:
                if old_handler is not None:
                    signal.signal(signal.SIGINT, old_handler)
                for _, stream in self.active.values():
                    if stream is not None:
                        stream.close()


def queue_status(queue):
    """Probe the guard; stale sensor readings are explicitly historical."""
    current = Runner(queue, sender=lambda _: None).status()
    try:
        with file_lock(queue.root / "runner.guard", timeout=0):
            alive = False
    except TimeoutError:
        alive = True
    try:
        saved = read_json(queue.root / "status.json")
        if not isinstance(saved, dict):
            saved = {}
    except (FileNotFoundError, ValueError):
        saved = {}
    if alive:
        for key in ("pid", "updated", "temperature", "warning", "paused", "stopping"):
            if key in saved:
                current[key] = saved[key]
    else:
        current["pid"] = None
        current["updated"] = None
    current["runner_alive"] = alive
    current["last_seen"] = saved if not alive and saved else None
    return current
