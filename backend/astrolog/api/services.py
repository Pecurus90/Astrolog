"""Impostazioni > Servizi: the sky service's key, tried before it is saved, as Meteoblue's
(`PUT /weather/meteoblue-key`)."""

import sqlite3

from fastapi import APIRouter, Depends

from .. import place
from ..db import config
from ..db.transaction import transaction
from .deps import get_db
from .models_site import SkyKeyIn, SkyKeyOut

router = APIRouter(prefix="/api/v1", tags=["settings"])


@router.put("/services/sky-key", response_model=SkyKeyOut)
def put_sky_key(body: SkyKeyIn, conn: sqlite3.Connection = Depends(get_db)) -> SkyKeyOut:
    """Tries the key on the sky service (lightpollutionmap.info) and saves it, or removes it when
    sent empty. Spaces and line breaks of a paste are trimmed.

    **A key the service refuses is not saved**, and the hint stays the previous key's. Only the
    hint (`config.hint`) comes out, never the key."""
    trimmed = (body.key or "").strip()
    if not trimmed:
        with transaction(conn):
            config.write(conn, "sky_service_key", None)
        return SkyKeyOut(status="removed", hint=None)
    outcome = place.check_sky_key(trimmed)
    if outcome != place.SkyKeyCheck.OK:
        return SkyKeyOut(status=outcome.value, hint=config.hint(config.read(conn).sky_service_key))
    with transaction(conn):
        config.write(conn, "sky_service_key", trimmed)
    return SkyKeyOut(status="ok", hint=config.hint(trimmed))
