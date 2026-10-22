"""Iterative, sorted: repeatable scans. Links followed, each real folder walked once: no cycles.
What stays out is reported, not dropped."""

# Ported from fits/walk.py (ADR 0030): shared parts live twice until old pipeline goes.
# jscpd:ignore-start  # noqa: ERA001
import os
import re
import stat
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

# SBIG convention extensions, plus tile-compressed `.fz` (fpack)
FITS_EXTENSION_RE = re.compile(r"\.(fits|fit|fts)(\.fz)?$", re.IGNORECASE | re.ASCII)

# Tests set it to exercise every branch on any machine.
PLATFORM = sys.platform

# Online-only placeholder downloads when opened. Windows, *File Attribute Constants* (Microsoft):
# RECALL_ON_OPEN shows only in listing: flag read from it, not from separate stat.
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
SF_DATALESS = 0x40000000  # Mac, *TN3150* (Apple): in `st_flags`, per `bsd/sys/stat.h` in xnu
# Before macOS Sonoma iCloud left hidden `.Name.fits.icloud` stub, no flag (The Eclectic Light
# Company, *How iCloud Drive works in macOS Sonoma*): matched by name on any system.
ICLOUD_STUB_RE = re.compile(
    r"^\.(.+\.(?:fits|fit|fts)(?:\.fz)?)\.icloud$", re.IGNORECASE | re.ASCII
)

# Per system: stat field, bits meaning "not on disk". Linux has none.
_NOT_ON_DISK = {
    "win32": (
        "st_file_attributes",
        FILE_ATTRIBUTE_RECALL_ON_OPEN
        | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
        | stat.FILE_ATTRIBUTE_OFFLINE,
    ),
    "darwin": ("st_flags", SF_DATALESS),
}

# Windows limit: 260 chars. Past margin: `\\?\` form; shorter stays plain, readable in logs.
LONG_PATH_THRESHOLD = 240


def long_path(path: str | os.PathLike[str]) -> str:
    """Network folder needs `\\\\?\\UNC\\server\\share\\...`, not `\\\\?\\\\\\server\\share`; with
    prefix, forward slashes aren't separators (Windows, *Maximum Path Length Limitation*)."""
    p = str(path)
    if os.name != "nt" or p.startswith("\\\\?\\"):
        return p
    if len(p) <= LONG_PATH_THRESHOLD and not _trailing_dot_or_space(p):
        return p
    full = absolute(p)
    if full.startswith("\\\\"):  # \\server\share -> \\?\UNC\server\share
        return "\\\\?\\UNC" + full[1:]
    return "\\\\?\\" + full


def absolute(path: str) -> str:
    """abspath (GetFullPathName) strips trailing dots and spaces: there normpath keeps them."""
    if _trailing_dot_or_space(path):
        return os.path.normpath(os.path.join(os.getcwd(), path))
    return os.path.abspath(path)


def _trailing_dot_or_space(path: str) -> bool:
    """'night.' made on Mac or Linux: Win32 strips the dot and opens 'night' (Naming Files)."""
    return any(
        part.endswith((".", " ")) and part not in (".", "..") for part in re.split(r"[\\/]", path)
    )


def _apple_double(name: str) -> bool:
    """`._M42.fits` twin macOS writes beside each file on stick or NAS: Finder metadata, not FITS.
    Without this, every frame passed through a Mac counts unread."""
    return name.startswith("._")


# Bins and snapshots that carry no dot nor attribute (NAS over Docker, Windows disk on Linux):
# by documented name, owner's exception to ADR 0031. Bin holds deleted frames, snapshot copies.
SERVICE_FOLDERS = frozenset({
    "#recycle",  # Synology KB, How do I recover files deleted from Synology NAS
    "#snapshot",  # Synology KB, Snapshot Replication: '#snapshot folders of the shared folder'
    "@recycle",  # QNAP QTS docs, Network Recycle Bin
    "@recently-snapshot",  # QNAP FAQ, How to Hide the @Recently-Snapshot Folder
    "lost+found",  # e2fsprogs mklost+found(8): root of each ext2/3/4 file system
    "$recycle.bin",  # Microsoft Learn, Recycle Bin is corrupted: root of each drive
})  # fmt: skip


def _hidden(entry: os.DirEntry[str]) -> bool:
    """Trash and service folders hidden on all three systems; trash holds frames user DELETED.
    Property first; NAS ones by documented name. Root user picks never passes here."""
    if entry.name.startswith(".") or entry.name.casefold() in SERVICE_FOLDERS:
        return True
    if PLATFORM != "win32":  # attribute exists only there; elsewhere it costs an lstat per folder
        return False
    try:
        attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_HIDDEN)


def _online_only(entry: os.DirEntry[str]) -> bool:
    """Flag comes with listing (free on Windows, lstat on Mac); system without one: not asked.
    Unreadable flag: on disk."""
    sign = _NOT_ON_DISK.get(PLATFORM)
    if sign is None:
        return False
    field, mask = sign
    try:
        return bool(getattr(entry.stat(follow_symlinks=False), field, 0) & mask)
    except OSError:
        return False


class EntryKind(StrEnum):
    """What walk does with listing entry."""

    HIDDEN = "hidden"
    WALKED = "walked"
    FILE = "file"


def _kind(entry: os.DirEntry[str]) -> EntryKind:
    """Linked folder (symlink, Windows junction) walked like any folder: `is_dir` follows it.
    Entry not answering: looked at as file."""
    try:
        is_dir = entry.is_dir()
    except OSError:
        return EntryKind.FILE
    if not is_dir:
        return EntryKind.FILE
    return EntryKind.HIDDEN if _hidden(entry) else EntryKind.WALKED


def _dangling(entry: os.DirEntry[str], full: str) -> bool:
    """Symlink with target gone (unplugged disk): `is_dir` False (Python, `os.DirEntry.is_dir`);
    junction still True, fails at `scandir`."""
    try:
        return entry.is_symlink() and not os.path.exists(long_path(full))
    except OSError:
        return False


@dataclass
class Walk:
    """What walk saw: FITS on disk and what it left out, each sorted. `unreadable`: folders not
    opening, links with target gone (file or folder: unknowable)."""

    found: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)
    online_only: list[str] = field(default_factory=list)


def real_key(path: str) -> str:
    return os.path.normcase(os.path.realpath(long_path(path)))


def _list_folder(current: str, scan: Iterable[os.DirEntry[str]], result: Walk) -> list[str]:
    """Sorts one folder's entries into `result`; returns the subfolders to walk."""
    subdirs, fits_here, stubs = [], set(), []
    folders_by_kind = {EntryKind.HIDDEN: result.hidden, EntryKind.WALKED: subdirs}
    for entry in scan:
        full = os.path.join(current, entry.name)
        kind = _kind(entry)
        if kind != EntryKind.FILE:
            folders_by_kind[kind].append(full)
        elif _apple_double(entry.name):
            continue  # placeholder's twin too: not one more file
        elif FITS_EXTENSION_RE.search(entry.name):
            fits_here.add(entry.name.casefold())
            (result.online_only if _online_only(entry) else result.found).append(full)
        elif stub := ICLOUD_STUB_RE.match(entry.name):
            stubs.append(stub.group(1))
        elif _dangling(entry, full):
            result.unreadable.append(full)
    # placeholder beside its real file: not second file, that one is on disk
    result.online_only.extend(
        os.path.join(current, name) for name in stubs if name.casefold() not in fits_here
    )
    return subdirs


def walk_dir(root: str) -> Walk:
    """Missing root: nothing found; vanished vs unplugged is caller's check.
    Folder reached again via link: walked once."""
    result = Walk()
    seen: set[str] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            scan = os.scandir(long_path(current))
        except OSError:
            result.unreadable.append(current)
            continue
        real = real_key(current)
        if real in seen:
            scan.close()
            continue
        seen.add(real)
        try:  # listing can break midway (NAS gone): folder not answering, files under it not judged
            with scan:
                stack.extend(_list_folder(current, scan, result))
        except OSError:
            result.unreadable.append(current)
    for items in (result.found, result.unreadable, result.hidden, result.online_only):
        items.sort()
    return result


# jscpd:ignore-end  # noqa: ERA001
