"""Il nome dell'intestazione della chiave e' scritto in piu' case: qui si tengono insieme.

Non viaggia nello schema OpenAPI, quindi **non si puo' generare**: il backend lo dichiara, il
client del frontend lo ripete, e `tools/dev.py` lo nomina a chi legge. Senza questa prova, chi
cambiasse quello del backend lascerebbe il frontend a mandare un'intestazione che nessuno guarda
piu' -- e il sintomo sarebbe un 401 su ogni richiesta, che somiglia a tutt'altro.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from astrolog.api.app import TOKEN_HEADER  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent
CASE = (
    RADICE / "frontend" / "src" / "api" / "client.ts",
    RADICE / "tools" / "dev.py",
)


def test_every_house_names_the_same_header():
    """Ogni casa nomina **esattamente** l'intestazione che il backend pretende."""
    mancanti = [
        os.path.relpath(f, RADICE)
        for f in CASE
        if f.is_file() and TOKEN_HEADER not in f.read_text(encoding="utf-8")
    ]
    assert not mancanti, f"non nominano {TOKEN_HEADER}: {mancanti}"
