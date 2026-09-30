"""Dove stanno i dati dell'app sui tre bersagli, in un posto solo.

Vincolo non ovvio: una sola fonte di configurazione per il deploy -- le variabili d'ambiente
-- e per il resto `platformdirs`: Windows `%LOCALAPPDATA%\\AstroLog`, Mac `~/Library/
Application Support/AstroLog`, Linux `~/.local/share/AstroLog`; nel container si imposta
`ASTROLOG_DATA_DIR=/data`. `ASTROLOG_DATA_ROOT` confina le cartelle FITS registrabili.
"""

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "AstroLog"


def data_dir():
    """La cartella dei dati dell'app (creata se manca)."""
    override = os.environ.get("ASTROLOG_DATA_DIR")
    base = Path(override) if override else Path(user_data_dir(APP_NAME, appauthor=False))
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path():
    return data_dir() / "astrolog.db"


def cache_dir():
    d = data_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_dir():
    d = data_dir() / "log"
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_root():
    """La radice sotto cui devono stare le cartelle FITS, in forma canonica; None = nessun
    confinamento (desktop). Sul NAS si imposta al volume montato."""
    raw = os.environ.get("ASTROLOG_DATA_ROOT")
    if not raw:
        return None
    return os.path.realpath(os.path.normpath(raw))
