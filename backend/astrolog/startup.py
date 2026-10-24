"""The start-up token. Out of `__main__.py`, which coverage excludes, so its rules have tests; the
data folder comes from the caller, so a test can give an empty one."""

import os
import secrets
import sys
from pathlib import Path
from typing import IO

LOCAL_HOSTS = ("127.0.0.1", "localhost")
OWNER_ONLY = 0o600  # [C POSIX sys/stat.h: S_IRUSR | S_IWUSR]


class AlreadyRunningError(RuntimeError):
    """Another copy holds the data folder: two would scan over each other."""


def single_instance(data_dir: Path) -> IO[bytes]:
    """OS lock on a file in the data folder, held while the returned file stays open; a dead
    process frees it. Taken: AlreadyRunningError."""
    holder = (data_dir / "astrolog.lock").open("a+b")
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(holder.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as taken:
        holder.close()
        raise AlreadyRunningError from taken
    return holder


def token_for(host: str, data_dir: Path) -> str | None:
    # On the NAS the home network is trusted by choice: a token on a shared disk would be one
    # more secret without one less defect.
    if host not in LOCAL_HOSTS:
        return None
    # `tools/dev.py` imposes it so backend and Vite share it; otherwise every request gets 401.
    token = os.environ.get("ASTROLOG_TOKEN") or secrets.token_urlsafe(32)
    # The default 0644 would give it to every account on the machine, such as a family Mac.
    fd = os.open(data_dir / "token", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, OWNER_ONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(token)
    return token
