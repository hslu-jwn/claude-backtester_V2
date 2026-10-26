"""Queue tuning defaults. Spec: research-runner.md > Job queue."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QueueConfig:
    workers: int = 8
    max_temp: float = 85
    resume_temp: float = 80
    poll: float = 10
    sensor_url: str = "http://localhost:8085/data.json"
    sensor_timeout: float = 2
    pause_seconds: float = 1800
    max_attempts: int = 2
    io_timeout: float = 5
    io_poll: float = 0.05
    lock_timeout: float = 30
    lock_poll: float = 0.05


DEFAULT_CONFIG = QueueConfig()
