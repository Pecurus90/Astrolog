"""Iterative and sorted (repeatable scans); linked folders followed, each real folder walked once
(no cycles). What stays out is reported to the caller instead of vanishing."""

# Ported from fits/walk.py (ADR 0030): the shared parts live twice until the old pipeline goes.
# jscpd:ignore-start  # noqa: ERA001
import os
import re
import stat
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

# .fits, .fit, .fts (SBIG convention extensions) and their tile-compressed form `.fz` (fpack)
FITS_EXTENSION_RE = re.compile(r"\.(fits|fit|fts)(\.fz)?$", re.IGNORECASE | re.ASCII)

# One constant, so tests can set it and exercise every branch on any machine.
PLATFORM = sys.platform

# An online-only placeholder downloads when opened. Windows, *File Attribute Constants* (Microsoft):
# RECALL_ON_OPEN shows only in a listing, so the flag is read from it, not from a separate stat.
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
SF_DATALESS = 0x40000000  # Mac, *TN3150* (Apple): in `st_flags`, per `bsd/sys/stat.h` in xnu
# Before macOS Sonoma iCloud left a hidden `.Name.fits.icloud` stub instead of a flag (The Eclectic
# Light Company, *How iCloud Drive works in macOS Sonoma*): recognised by name on any system.
ICLOUD_STUB_RE = re.compile(
    r"^\.(.+\.(?:fits|fit|fts)(?:\.fz)?)\.icloud$", re.IGNORECASE | re.ASCII
)

# Per system: the stat field, and the bits that mean "not on disk". Linux has no such flag.
_NOT_ON_DISK = {
    "win32": (
        "st_file_attributes",
        FILE_ATTRIBUTE_RECALL_ON_OPEN
        | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
        | stat.FILE_ATTRIBUTE_OFFLINE,
    ),
    "darwin": ("st_flags", SF_DATALESS),
}

# Windows' limit is 260 characters; past this margin the unlimited `\\?\` form is used, while
# shorter paths keep the plain form, readable in messages and logs.
LONG_PATH_THRESHOLD = 240


def long_path(path: str | os.PathLike[str]) -> str:
    """A network folder needs `\\\\?\\UNC\\server\\share\\...`, not `\\\\?\\\\\\server\\share`; with
    the prefix, forward slashes are not separators (Windows, *Maximum Path Length Limitation*)."""
    p = str(path)
    if os.name != "nt" or len(p) <= LONG_PATH_THRESHOLD or p.startswith("\\\\?\\"):
        return p
    absolute = os.path.abspath(p)  # on Windows it also normalises forward slashes
    if absolute.startswith("\\\\"):  # \\server\share -> \\?\UNC\server\share
        return "\\\\?\\UNC" + absolute[1:]
    return "\\\\?\\" + absolute


def _apple_double(name: str) -> bool:
    """The `._M42.fits` twin macOS writes beside every file on a stick or a NAS: Finder metadata,
    not a FITS, and without this every frame passed through a Mac would count as unread."""
    return name.startswith("._")


def _hidden(entry: os.DirEntry[str]) -> bool:
    """Trash and service folders are hidden on all three systems, and a trash holds frames the user
    DELETED. The property, not a name list; the root the user picks never passes here."""
    if entry.name.startswith("."):
        return True
    if PLATFORM != "win32":  # the attribute exists only there: elsewhere it is an lstat per folder
        return False
    try:
        attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_HIDDEN)


def _online_only(entry: os.DirEntry[str]) -> bool:
    """The flag comes with the listing (free on Windows, an lstat on the Mac); where the system has
    none it is not asked, and an unreadable flag means on disk."""
    sign = _NOT_ON_DISK.get(PLATFORM)
    if sign is None:
        return False
    field, mask = sign
    try:
        return bool(getattr(entry.stat(follow_symlinks=False), field, 0) & mask)
    except OSError:
        return False


class EntryKind(StrEnum):
    """What the walk does with a listing entry."""

    HIDDEN = "hidden"
    WALKED = "walked"
    FILE = "file"


def _kind(entry: os.DirEntry[str]) -> EntryKind:
    """A linked folder (symlink, Windows junction) is walked like any folder: `is_dir` follows it.
    An entry that does not answer is looked at as a file."""
    try:
        is_dir = entry.is_dir()
    except OSError:
        return EntryKind.FILE
    if not is_dir:
        return EntryKind.FILE
    return EntryKind.HIDDEN if _hidden(entry) else EntryKind.WALKED


def _dangling(entry: os.DirEntry[str], full: str) -> bool:
    """A symlink whose target is gone (an unplugged disk): `is_dir` says False for it (Python,
    `os.DirEntry.is_dir`), while a junction still says True and fails at `scandir`."""
    try:
        return entry.is_symlink() and not os.path.exists(long_path(full))
    except OSError:
        return False


@dataclass
class Walk:
    """What a walk saw: FITS files on disk, and what it left out, each list sorted. `unreadable`
    holds folders that do not open and links whose target is gone (file or folder, unknowable)."""

    found: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)
    online_only: list[str] = field(default_factory=list)


def _real(path: str) -> str:
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
            continue  # a placeholder's twin too: it is not one more file
        elif FITS_EXTENSION_RE.search(entry.name):
            fits_here.add(entry.name.casefold())
            (result.online_only if _online_only(entry) else result.found).append(full)
        elif stub := ICLOUD_STUB_RE.match(entry.name):
            stubs.append(stub.group(1))
        elif _dangling(entry, full):
            result.unreadable.append(full)
    # a placeholder beside its real file is not a second file: that one is on disk
    result.online_only.extend(
        os.path.join(current, name) for name in stubs if name.casefold() not in fits_here
    )
    return subdirs


def walk_dir(root: str) -> Walk:
    """A missing root gives nothing found: telling a vanished folder from an unplugged disk is the
    caller's check. A folder reached again through a link is not walked twice."""
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
        real = _real(current)
        if real in seen:
            scan.close()
            continue
        seen.add(real)
        with scan:
            stack.extend(_list_folder(current, scan, result))
    for items in (result.found, result.unreadable, result.hidden, result.online_only):
        items.sort()
    return result


# jscpd:ignore-end  # noqa: ERA001
