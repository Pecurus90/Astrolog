"""The start-up token. Out of `__main__.py`, which coverage excludes, so its rules have tests; the
data folder comes from the caller, so a test can give an empty one."""

import os
import secrets
from pathlib import Path

CASA = ("127.0.0.1", "localhost")
MODO_SOLO_UTENTE = 0o600


def token_for(host: str, data_dir: Path) -> str | None:
    # On the NAS the home network is trusted by choice: a token on a shared disk would be one
    # more secret without one less defect.
    if host not in CASA:
        return None
    # `tools/dev.py` imposes it so backend and Vite share it; otherwise every request gets 401.
    token = os.environ.get("ASTROLOG_TOKEN") or secrets.token_urlsafe(32)
    # The default 0644 would give it to every account on the machine, such as a family Mac.
    fd = os.open(data_dir / "token", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, MODO_SOLO_UTENTE)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(token)
    return token
