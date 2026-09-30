"""La chiave Meteoblue: si prova sul conto prima di salvarla, e si toglie mandandola vuota.

Vincoli non ovvi:

* **Una chiave che il conto non riconosce non si salva**: salvarla vorrebbe dire scoprirlo solo al
  prossimo giro, con un seeing che non arriva e nessuna idea del perche'.
* **Una chiave nuova si usa subito**: il seeing di prima e l'ultimo tentativo si dimenticano, e il
  giro del meteo parte adesso invece che fra dodici ore.
* Fuori esce solo il suggerimento (`config.hint`), mai la chiave.
"""

import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import config
from ..db.transaction import transaction
from ..spine.group_store import home_site
from ..weather import meteoblue, rounds
from .deps import get_db

router = APIRouter(prefix="/api/v1", tags=["meteo"])

REMOVED = "removed"


class MeteoblueKeyIn(BaseModel):
    key: str | None


class MeteoblueKeyOut(BaseModel):
    """Com'e' andata: salvata (`ok`), tolta (`removed`), o perche' no; e il suggerimento della
    chiave che adesso c'e'."""

    status: Literal["ok", "removed", "refused", "unreachable", "bad_answer"]
    hint: str | None


@router.put("/weather/meteoblue-key", response_model=MeteoblueKeyOut)
def put_meteoblue_key(body: MeteoblueKeyIn, conn: sqlite3.Connection = Depends(get_db)):
    """Prova la chiave e la salva, o la toglie. Una chiave incollata si porta dietro spazi e ritorni
    a capo: un carattere invisibile in fondo darebbe un rifiuto che nessuno sa spiegarsi."""
    chiave = (body.key or "").strip()
    if not chiave:
        with transaction(conn):
            config.write(conn, "meteoblue_key", None)
            meteoblue.forget(conn)
        return MeteoblueKeyOut(status=REMOVED, hint=None)
    esito = meteoblue.check_key(chiave)
    if esito != meteoblue.OK:
        return MeteoblueKeyOut(status=esito, hint=config.hint(config.read(conn)["meteoblue_key"]))
    with transaction(conn):
        config.write(conn, "meteoblue_key", chiave)
        meteoblue.forget(conn)
    sito = home_site(conn)
    if sito is not None:
        rounds.refresh(conn, dict(sito))
    return MeteoblueKeyOut(status=esito, hint=config.hint(chiave))
