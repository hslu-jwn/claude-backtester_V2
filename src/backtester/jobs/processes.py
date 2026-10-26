"""PID identity checks and termination of an entire job process tree."""

import os
import signal
import subprocess
from pathlib import Path


def process_identity(pid: int | None) -> float | None:
    """Creation timestamp; unknown identity is deliberately treated as dead.

    Uses existing psutil when present, native Windows APIs otherwise, or Linux /proc.
    A liveness-only fallback cannot safely distinguish a reused PID.
    """
    if not pid or pid <= 0:
        return None
    try:
        import psutil
    except ImportError:
        pass
    else:
        try:
            p = psutil.Process(pid)
            return None if p.status() == psutil.STATUS_ZOMBIE else p.create_time()
        except psutil.Error:
            return None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [
            ctypes.POINTER(wintypes.FILETIME)
        ] * 4
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:
                return None
            times = [wintypes.FILETIME() for _ in range(4)]
            if kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
                return ticks / 10_000_000 - 11644473600
        finally:
            kernel.CloseHandle(handle)
        return None
    try:
        # Linux start ticks, anchored to boot time. Avoid parsing spaces in comm.
        stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        if stat[0] == "Z":
            return None
        boot = next(
            float(line.split()[1])
            for line in Path("/proc/stat").read_text().splitlines()
            if line.startswith("btime ")
        )
        return boot + int(stat[19]) / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError, StopIteration):
        return None


def terminate_tree(pid: int):
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
