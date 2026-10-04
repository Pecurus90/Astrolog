"""The first start is a stamp, not a guess: "looks empty" would turn true again after a reset and
reopen the wizard. Key types and defaults live in `db/config.py`; here a refusal becomes a reply."""

import sqlite3
from typing import cast

from fastapi import APIRouter, Depends, HTTPException

from ..clock import now_iso
from ..db import config
from ..db.transaction import transaction
from ..spine.group import NO_ACTIVE_SITE
from ..spine.solve import (
    NO_SOLVER,
    NO_STAR_DATABASE,
    databases_next_to,
    solver_found,
    solver_path,
    solver_where,
)
from .deps import get_db
from .models_site import Missing, SettingsOut, SettingsPatch, SolverOut, SolverSource

router = APIRouter(prefix="/api/v1", tags=["impostazioni"])


def _missing(conn: sqlite3.Connection) -> list[Missing]:
    """Codes, not sentences. A home site is never elected silently: nights need one, and a site
    nobody declared is invented data."""
    manca: list[Missing] = []
    if conn.execute("SELECT 1 FROM sites WHERE is_default = 1").fetchone() is None:
        manca.append(NO_ACTIVE_SITE)
    percorso = solver_path(conn)
    if percorso is None:
        manca.append(NO_SOLVER)
    elif not databases_next_to(percorso):
        # Named only to who has ASTAP, and with the path already in hand: two alarms for one
        # problem send the user after two things, and two searches could disagree.
        manca.append(NO_STAR_DATABASE)
    return manca


def _out(conn: sqlite3.Connection) -> SettingsOut:
    values = config.read(conn)
    values = {k: config.hint(v) if k in config.SECRETS else v for k, v in values.items()}
    return SettingsOut(
        values=values,
        wizard_done=values["onboarding_done_at"] is not None,
        missing=_missing(conn),
    )


@router.get("/settings", response_model=SettingsOut)
def read_settings(conn: sqlite3.Connection = Depends(get_db)) -> SettingsOut:
    return _out(conn)


@router.patch("/settings", response_model=SettingsOut)
def write_settings(body: SettingsPatch, conn: sqlite3.Connection = Depends(get_db)) -> SettingsOut:
    """Writes the given keys and returns the settings as they now are. Either all pass or nothing
    does: half the preferences written would be worse than none, and whoever got one key wrong
    must not guess which ones went in.

    422 `unknown_setting` with the unknown `keys`; 422 `tried_elsewhere` with the `keys` that are
    tried by their own route before being stored; 422 `wrong_type` if a value has the wrong type
    or is not one of the key's allowed choices."""
    unknown = sorted(k for k in body.values if k not in config.KEYS)
    if unknown:
        raise HTTPException(status_code=422, detail={"code": "unknown_setting", "keys": unknown})
    provate = sorted(k for k in body.values if k in config.TRIED_ELSEWHERE)
    if provate:
        raise HTTPException(status_code=422, detail={"code": "tried_elsewhere", "keys": provate})
    try:
        with transaction(conn):
            for key, value in body.values.items():
                config.write(conn, key, value)
    except ValueError as err:
        raise HTTPException(status_code=422, detail={"code": "wrong_type"}) from err
    return _out(conn)


def _solver(conn: sqlite3.Connection, dove: tuple[str | None, str | None]) -> SolverOut:
    return SolverOut(
        path=dove[0],
        # `astap.where_exe` returns a channel of `astap.SOURCES`, typed as plain `str`.
        source=cast("SolverSource | None", dove[1]),
        declared=config.read(conn).get("astap_path"),
        databases=list(databases_next_to(dove[0])),
    )


@router.get("/solver", response_model=SolverOut)
def read_solver(conn: sqlite3.Connection = Depends(get_db)) -> SolverOut:
    """Where the app takes the solver from, and through which channel.

    The **declared** path always comes out, even when it leads nowhere: it is the only thing that
    can be corrected, and hiding it would leave a section saying "not found" without saying why."""
    return _solver(conn, solver_where(conn))


@router.post("/solver/search", response_model=SolverOut)
def search_solver(conn: sqlite3.Connection = Depends(get_db)) -> SolverOut:
    """*Find it for me*: what the app would find **ignoring the preference**.

    A POST because it looks at the machine's disk and PATH, not because it writes: **it writes
    nothing**. Adopting the proposal is the user's gesture -- silently overwriting a hand-written
    path would remove the only way out when this search picks the wrong program."""
    return _solver(conn, solver_found())


@router.post("/settings/wizard-done", response_model=SettingsOut)
def stamp_wizard(conn: sqlite3.Connection = Depends(get_db)) -> SettingsOut:
    """The first start is over: completing or skipping the wizard is the same stamp. Reopening the
    wizard from Settings does not rewrite it: the stamp keeps the first time.
    Returns the settings."""
    if config.read(conn)["onboarding_done_at"] is None:
        with transaction(conn):
            config.write(conn, "onboarding_done_at", now_iso())
    return _out(conn)
