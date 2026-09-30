"""Iterative, sorted (repeatable scans), links and junctions not followed (no cycles). What stays
out is reported to the caller instead of vanishing; extensions are a product decision."""

import math
import os
import re
import stat
import sys
import time
from enum import StrEnum

FITS_EXTENSION_RE = re.compile(r"\.(fits|fit)$", re.IGNORECASE | re.ASCII)

# One constant, so tests can set it and exercise every branch on any machine.
PLATFORM = sys.platform

# An online-only placeholder downloads when opened. Windows, *File Attribute Constants* (Microsoft):
# RECALL_ON_OPEN shows only in a listing, so the flag is read from it, not from a separate stat.
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
SF_DATALESS = 0x40000000  # Mac, *TN3150* (Apple): in `st_flags`, per `bsd/sys/stat.h` in xnu
# Before macOS Sonoma iCloud left a hidden `.Name.fits.icloud` stub instead of a flag (The Eclectic
# Light Company, *How iCloud Drive works in macOS Sonoma*): recognised by name on any system.
ICLOUD_STUB_RE = re.compile(r"^\.(.+\.(?:fits|fit))\.icloud$", re.IGNORECASE | re.ASCII)

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
    intero = os.path.abspath(p)  # on Windows it also normalises forward slashes
    if intero.startswith("\\\\"):  # \\server\share -> \\?\UNC\server\share
        return "\\\\?\\UNC" + intero[1:]
    return "\\\\?\\" + intero


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
        attributi = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributi & stat.FILE_ATTRIBUTE_HIDDEN)


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
    """What the walk does with a listing entry: one decision for the walk and the folder picker."""

    LINKED = "linked"
    HIDDEN = "hidden"
    WALKED = "walked"
    FILE = "file"


def _kind(entry: os.DirEntry[str]) -> EntryKind:
    """A link or a Windows junction is not followed: for Python a junction is a plain folder, and
    only `is_junction` tells it apart. An entry that does not answer is looked at as a file."""
    try:
        if entry.is_junction() or (entry.is_symlink() and entry.is_dir()):
            return EntryKind.LINKED
        is_dir = entry.is_dir()  # not a link here: following it or not is the same
    except OSError:
        return EntryKind.FILE
    if not is_dir:
        return EntryKind.FILE
    return EntryKind.HIDDEN if _hidden(entry) else EntryKind.WALKED


def subfolders(path: str) -> list[str]:
    """The subfolders the walk would enter, sorted; a folder that does not open raises."""
    with os.scandir(long_path(path)) as scan:
        return sorted(e.name for e in scan if _kind(e) == EntryKind.WALKED)


def walk_dir(  # noqa: PLR0913
    root: str,
    found: list[str] | None = None,
    unreadable: list[str] | None = None,
    hidden: list[str] | None = None,
    online_only: list[str] | None = None,
    linked: list[str] | None = None,
    deadline: float = math.inf,
    unvisited: list[str] | None = None,
) -> list[str]:
    """A missing root gives an empty list: telling a vanished folder from an unplugged disk is the
    caller's check. Past `deadline` (`time.monotonic`) the folders not seen go in `unvisited`."""
    found, unreadable, hidden, online_only, linked, unvisited = (
        [] if items is None else items
        for items in (found, unreadable, hidden, online_only, linked, unvisited)
    )
    stack = [root]
    while stack:
        if time.monotonic() >= deadline:
            unvisited.extend(stack)
            break
        current = stack.pop()
        try:
            scan = os.scandir(long_path(current))
        except OSError:
            unreadable.append(current)
            continue
        subdirs, fits_here, stubs = [], set(), []
        folders_by_kind = {
            EntryKind.LINKED: linked,
            EntryKind.HIDDEN: hidden,
            EntryKind.WALKED: subdirs,
        }
        with scan:
            for entry in scan:
                full = os.path.join(current, entry.name)
                kind = _kind(entry)
                if kind != EntryKind.FILE:
                    folders_by_kind[kind].append(full)
                elif _apple_double(entry.name):
                    continue  # a placeholder's twin too: it is not one more file
                elif FITS_EXTENSION_RE.search(entry.name):
                    fits_here.add(entry.name.casefold())
                    (online_only if _online_only(entry) else found).append(full)
                elif stub := ICLOUD_STUB_RE.match(entry.name):
                    stubs.append(stub.group(1))
        # a placeholder beside its real file is not a second file: that one is on disk
        online_only.extend(
            os.path.join(current, name) for name in stubs if name.casefold() not in fits_here
        )
        stack.extend(subdirs)
    for items in (found, hidden, online_only, linked):
        items.sort()
    return found
