"""Checks run on the resolved path, so a symlink outside the confined root does not bypass it;
system zones are also checked as written, since on Mac `/etc` resolves to `/private/etc`."""

import os
import re
from types import ModuleType
from typing import NoReturn

from fastapi import HTTPException

BLOCKLIST_POSIX = ("/", "/etc", "/sys", "/proc", "/dev", "/var", "/boot", "/root")

# Device paths `\\?\` and `\\.\` (Microsoft, *File path formats on Windows systems*): the first
# also skips normalisation, and `realpath` does not strip it.
DEVICE_PATH_RE = re.compile(r"^[\\/]{2}[?.][\\/]")
# Characters no file name may hold (Microsoft, *Naming Files, Paths, and Namespaces*): with `?`
# it is a system namespace name (`\??\C:\Windows`), not a folder.
RESERVED_NT_RE = re.compile(r'[<>"|?*]')
# Shares Windows creates by itself (Microsoft, *Remove administrative shares*): `\\name` may be
# this machine, so they are refused on every PC. `C$.` and `C$ ` reach no disk, so they pass.
ADMIN_SHARE_RE = re.compile(
    r"^[\\/]{2}[^\\/]+[\\/](?:[a-z]|admin|ipc|print|fax)\$(?:[\\/]|$)", re.IGNORECASE | re.ASCII
)


def blocklist_nt() -> tuple[str, ...]:
    env = os.environ
    drive = env.get("SystemDrive", "C:") + "\\"
    return tuple(
        p
        for p in (
            drive,
            env.get("SystemRoot", drive + "Windows"),
            env.get("ProgramFiles", drive + "Program Files"),
            env.get("ProgramFiles(x86)", drive + "Program Files (x86)"),
            env.get("ProgramData", drive + "ProgramData"),
        )
        if p
    )


def same_folder(a: str, b: str) -> bool:
    return os.path.normcase(a) == os.path.normcase(b)


def is_under(child: str, parent: str) -> bool:
    """Compares names only and resolves nothing: the caller decides which form it passes."""
    # A drive root (`C:\`) blocks only itself, not everything it holds.
    return same_folder(child, parent) or os.path.normcase(child).startswith(
        os.path.normcase(parent) + os.sep
    )


def is_blocked_system_path(path: str) -> bool:
    blocklist = blocklist_nt() if os.name == "nt" else BLOCKLIST_POSIX
    return any(is_under(path, bad) for bad in blocklist)


def stored_form(written: str, resolved: str, rules: ModuleType = os.path) -> str:
    """The resolved form, unless resolving changes drive: a mapped network drive resolves to its
    share (bpo-37993), and the user who chose `Z:` must find `Z:` again."""
    drive, tail = rules.splitdrive(written)
    resolved_drive, resolved_tail = rules.splitdrive(resolved)
    if rules.normcase(drive) == rules.normcase(resolved_drive):
        return resolved
    names = [n for n in re.split(r"[\\/]", tail) if n]
    known = [n for n in re.split(r"[\\/]", resolved_tail) if n]
    # Names take the system's casing where they match: `Z:\foto` and `z:\FOTO\` are one row.
    for i in range(1, min(len(names), len(known)) + 1):
        if names[-i].casefold() == known[-i].casefold():
            names[-i] = known[-i]
    return rules.join(drive[:1].upper() + drive[1:] + rules.sep, *names)


def _refuse(code: str, path: str, **more: str) -> NoReturn:
    raise HTTPException(status_code=422, detail={"code": code, "path": path, **more})


def validate_root(raw: str, data_root: str | None) -> str:  # noqa: C901
    """The path to store, or HTTPException 422 with the reason as a code. Network folders are
    accepted: why, and their risk, are in the domain contract."""
    if not raw or not os.path.isabs(raw):
        _refuse("path_not_absolute", raw)
    if "\x00" in raw:  # NUL is in no name on any system
        _refuse("path_invalid", raw)
    written = os.path.abspath(raw)
    if DEVICE_PATH_RE.match(raw) or DEVICE_PATH_RE.match(written):
        _refuse("path_device", raw)  # also `C:\folder\NUL`, which abspath turns into `\\.\NUL`
    if os.name == "nt" and RESERVED_NT_RE.search(raw):
        _refuse("path_invalid", raw)
    try:
        canonical = os.path.realpath(written)
    except OSError:
        # An unreachable share is checked as written and accepted like an unplugged disk.
        canonical = written
    if not os.path.isabs(canonical):
        _refuse("path_not_absolute", canonical)
    if ADMIN_SHARE_RE.match(canonical):
        _refuse("path_admin_share", canonical)
    if data_root is not None:
        if not is_under(canonical, data_root):
            _refuse("path_outside_data_root", canonical, data_root=data_root)
    elif is_blocked_system_path(canonical):
        _refuse("path_is_system", canonical)
    elif is_blocked_system_path(written):
        _refuse("path_is_system", written)
    return stored_form(written, canonical)
