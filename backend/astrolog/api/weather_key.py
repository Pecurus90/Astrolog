import sqlite3
from typing import Final, Literal, cast

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import config
from ..db.transaction import transaction
from ..spine.group_store import home_site
from ..weather import meteoblue, rounds
from ..weather.forecast import Outcome
from .deps import get_db

router = APIRouter(prefix="/api/v1", tags=["meteo"])

REMOVED: Final = "removed"
# Repeated rather than imported from `weather`, so the route contract does not change shape with
# an internal module.
KeyStatus = Literal["ok", "removed", "refused", "unreachable", "bad_answer"]


class MeteoblueKeyIn(BaseModel):
    key: str | None


class MeteoblueKeyOut(BaseModel):
    """How it went: saved (`ok`), removed (`removed`), or why not; and the hint of the key that is
    there now."""

    status: KeyStatus
    hint: str | None


@router.put("/weather/meteoblue-key", response_model=MeteoblueKeyOut)
def put_meteoblue_key(
    body: MeteoblueKeyIn, conn: sqlite3.Connection = Depends(get_db)
) -> MeteoblueKeyOut:
    """Tries the key on the account and saves it, or removes it when it is sent empty. A pasted key
    carries spaces and line breaks along: an invisible character at the end would give a refusal
    nobody can explain, so they are trimmed.

    **A key the account does not recognise is not saved**, and the hint stays the previous key's:
    saving it would mean finding out only at the next round, with seeing that does not arrive and
    no idea why. **A new key is used at once**: the previous seeing and the last attempt are
    forgotten, and the weather round starts now instead of after Meteoblue's minimum gap
    (`meteoblue.MIN_GAP_H`). Only the hint (`config.hint`) comes out, never the key."""
    chiave = (body.key or "").strip()
    if not chiave:
        with transaction(conn):
            config.write(conn, "meteoblue_key", None)
            meteoblue.forget(conn)
        return MeteoblueKeyOut(status=REMOVED, hint=None)
    esito = meteoblue.check_key(chiave)
    if esito != Outcome.OK:
        return MeteoblueKeyOut(
            status=cast(KeyStatus, esito), hint=config.hint(config.read(conn).meteoblue_key)
        )
    with transaction(conn):
        config.write(conn, "meteoblue_key", chiave)
        meteoblue.forget(conn)
    sito = home_site(conn)
    if sito is not None:
        rounds.refresh(conn, dict(sito))
    return MeteoblueKeyOut(status=cast(KeyStatus, esito), hint=config.hint(chiave))
