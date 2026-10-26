"""How many ASTAP at once (D7, ADR 0033): half the physical cores, never past a quarter of the RAM.
Read from the system with the standard library only, one way per platform."""

import ctypes
import os
import sys
from pathlib import Path

ASTAP_RAM_BYTES = 160 * 2**20  # [P ADR 0033, D7: measured per process on 26 MP]
RAM_SHARE = 4  # [P ADR 0033, D7]
CORE_SHARE = 2  # [P ADR 0033, D7]
THREADS_PER_CORE = 2  # [T] unknown physical cores: SMT's two threads, the safe guess
_CGROUP = Path("/sys/fs/cgroup")


def workers(cores: int | None, ram: int | None, logical: int | None) -> int:
    """At least one. Unknown cores: the logical ones halved; unknown RAM: cores alone."""
    if cores is None and logical is not None:
        cores = logical // THREADS_PER_CORE
    by_cores = (cores or 1) // CORE_SHARE
    by_ram = by_cores if ram is None else ram // RAM_SHARE // ASTAP_RAM_BYTES
    return max(1, min(by_cores, by_ram))


def capacity() -> int:
    return workers(physical_cores(), total_ram(), os.cpu_count())


def physical_cores() -> int | None:
    """None when the system does not say."""
    if sys.platform == "win32":
        return _windows_cores()
    if sys.platform == "darwin":
        return _sysctl("hw.physicalcpu")
    return _linux_cores()


def total_ram() -> int | None:
    """Bytes; on Linux the container's limit when lower (Docker on a NAS)."""
    if sys.platform == "win32":
        return _windows_ram()
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError):
        return None
    limit = cgroup_memory()
    return ram if limit is None else min(ram, limit)


def _linux_cores() -> int | None:
    """Distinct cores among the CPUs this process may use (a container's cpuset)."""
    if sys.platform != "linux":
        return None
    cores = set()
    for cpu in os.sched_getaffinity(0):
        siblings = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list")
        try:
            cores.add(siblings.read_text(encoding="ascii").strip())
        except OSError:
            return None
    limit = cgroup_cpus()  # Docker's --cpus: fewer cores than the host has
    if not cores:
        return None
    return len(cores) if limit is None else min(len(cores), limit)


def cgroup_memory(root: Path = _CGROUP) -> int | None:
    """The container's `--memory`: cgroup v2, else v1 (older NAS kernels). None: no limit."""
    for name in ("memory.max", "memory/memory.limit_in_bytes"):
        text = _read(root / name)
        if text is not None:
            return int(text) if text.isdigit() else None  # "max": no limit
    return None


def cgroup_cpus(root: Path = _CGROUP) -> int | None:
    """The container's `--cpus`, rounded up: v2 `quota period`, else v1's two files."""
    v2 = _read(root / "cpu.max")
    if v2 is not None:
        allowed, _, period = v2.partition(" ")
    else:
        allowed = _read(root / "cpu/cpu.cfs_quota_us") or ""
        period = _read(root / "cpu/cpu.cfs_period_us") or ""
    if not (allowed.isdigit() and period.isdigit()) or int(period) == 0:
        return None  # "max" or -1: no limit
    return -(-int(allowed) // int(period))


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="ascii").strip()
    except OSError:
        return None


def _sysctl(name: str) -> int | None:
    if sys.platform != "darwin":
        return None
    value = ctypes.c_uint64(0)
    size = ctypes.c_size_t(ctypes.sizeof(value))
    libc = ctypes.CDLL(None)
    if libc.sysctlbyname(name.encode(), ctypes.byref(value), ctypes.byref(size), None, 0):
        return None
    return int(value.value) or None


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint32),
        ("load", ctypes.c_uint32),
        ("total_phys", ctypes.c_uint64),
        ("avail_phys", ctypes.c_uint64),
        ("total_page", ctypes.c_uint64),
        ("avail_page", ctypes.c_uint64),
        ("total_virtual", ctypes.c_uint64),
        ("avail_virtual", ctypes.c_uint64),
        ("avail_extended", ctypes.c_uint64),
    ]


def _windows_ram() -> int | None:
    if sys.platform != "win32":
        return None
    status = _MemoryStatus()
    status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return int(status.total_phys)


def _windows_cores() -> int | None:
    """One record per physical core (RelationProcessorCore = 0), each with its own size."""
    if sys.platform != "win32":
        return None
    get = ctypes.windll.kernel32.GetLogicalProcessorInformationEx
    length = ctypes.c_uint32(0)
    get(0, None, ctypes.byref(length))
    buffer = ctypes.create_string_buffer(length.value)
    if not length.value or not get(0, buffer, ctypes.byref(length)):
        return None
    count, offset = 0, 0
    while offset < length.value:
        size = int.from_bytes(buffer.raw[offset + 4 : offset + 8], "little")
        if size == 0:
            return None
        count, offset = count + 1, offset + size
    return count or None
