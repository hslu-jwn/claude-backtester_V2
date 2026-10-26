"""LibreHardwareMonitor CPU temperature and hysteresis guard."""

import http.client
import json
import math
import re
from dataclasses import dataclass
from urllib.request import urlopen

from backtester.jobs.config import DEFAULT_CONFIG


def parse_temperature(tree) -> float | None:
    readings = []

    def walk(node, cpu=False, temperatures=False):
        if not isinstance(node, dict):
            return
        name = str(node.get("Text", ""))
        icon = str(node.get("ImageURL", "")).lower()
        cpu = cpu or "cpu" in icon or name.lower() in ("cpu", "processor")
        temperatures = temperatures or name.lower() == "temperatures"
        if (
            cpu
            and temperatures
            and any(key in name.lower() for key in ("package", "tctl", "tdie", "core max"))
        ):
            value = str(node.get("Value", ""))
            match = re.search(r"(-?\d+(?:[.,]\d+)?)\s*°?\s*C", value, re.IGNORECASE)
            if match:
                number = float(match[1].replace(",", "."))
                if math.isfinite(number):
                    readings.append(number)
        for child in node.get("Children", []):
            walk(child, cpu, temperatures)

    walk(tree)
    return max(readings) if readings else None


def read_temperature(url: str, timeout: float = DEFAULT_CONFIG.sensor_timeout) -> float | None:
    try:
        with urlopen(url, timeout=timeout) as response:
            return parse_temperature(json.load(response))
    except (OSError, ValueError, TypeError, http.client.HTTPException):
        return None


@dataclass
class TemperatureGuard:
    maximum: float = DEFAULT_CONFIG.max_temp
    resume: float = DEFAULT_CONFIG.resume_temp
    paused: bool = False

    def __post_init__(self):
        if not math.isfinite(self.maximum) or not math.isfinite(self.resume):
            raise ValueError("Temperature thresholds must be finite")
        if self.resume >= self.maximum:
            raise ValueError("resume-temp must be below max-temp")

    def update(self, reading: float | None) -> bool:
        if reading is None or reading <= self.resume:
            self.paused = False
        elif reading >= self.maximum:
            self.paused = True
        return self.paused
