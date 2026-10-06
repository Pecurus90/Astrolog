"""Environment variables are the only deploy configuration (`ASTROLOG_DATA_DIR=/data` in the
container), `platformdirs` the default. `ASTROLOG_DATA_ROOT` confines the FITS folders."""

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "AstroLog"


def data_dir() -> Path:
    override = os.environ.get("ASTROLOG_DATA_DIR")
    base = Path(override) if override else Path(user_data_dir(APP_NAME, appauthor=False))
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path() -> Path:
    return data_dir() / "astrolog.db"


def _subdir(name: str) -> Path:
    d = data_dir() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir() -> Path:
    return _subdir("cache")


def log_dir() -> Path:
    return _subdir("log")


def data_root() -> str | None:
    """The canonical root the FITS folders must live under (the mounted volume on a NAS);
    None means no confinement, as on a desktop."""
    raw = os.environ.get("ASTROLOG_DATA_ROOT")
    if not raw:
        return None
    return os.path.realpath(os.path.normpath(raw))
