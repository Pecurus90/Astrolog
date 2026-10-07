"""The read does not compute: each night is read as `weather.view` wrote it, with the sources
joined, every measure judged and the models' agreement counted."""

import json
import sqlite3
from dataclasses import asdict
from typing import Final, cast

from fastapi import APIRouter, Depends

from ..clock import night_date, now_iso
from ..db import config
from ..db.transaction import transaction
from ..spine.group_store import home_site
from ..weather import forecast, judge, meteoblue, openmeteo, rounds, sky, view
from .deps import get_db
from .models_weather import (
    JudgedCode,
    KeyStatus,
    MeteoblueKeyIn,
    MeteoblueKeyOut,
    RefreshStatus,
    WeatherBriefOut,
    WeatherNightOut,
    WeatherOut,
    WeatherRefreshOut,
    WeatherScaleOut,
    WeatherSeeingOut,
    WeatherSourceOut,
    WeatherStepOut,
)

router = APIRouter(prefix="/api/v1", tags=["weather"])

_NIGHTS = (
    "SELECT night_date, hours_json, summary_json FROM weather_view"
    " WHERE site_id = ? AND model = ? AND night_date >= ? ORDER BY night_date"
)
_LAST_FETCHED = (
    "SELECT MAX(fetched_at) FROM weather_nights WHERE site_id = ? AND kind = ? AND source LIKE ?"
)
_SKY_SOURCES = ", ".join("?" * len(sky.ALL_SOURCES))  # segnaposto-ok: the sources, constants
_ARRIVED = (
    "SELECT source, MAX(fetched_at) AS fetched_at FROM weather_nights"  # noqa: S608
    f" WHERE site_id = ? AND kind = ? AND source IN ({_SKY_SOURCES}) AND night_date >= ?"
    " GROUP BY source ORDER BY source"
)

# A product choice, not a threshold: no source found says from which day an hourly forecast stops
# being worth reading.
FULL_NIGHTS = 3
# the current night and the six after: the service sometimes brings one more, which is not shown
MAX_NIGHTS = 7

SCALES = [
    WeatherScaleOut(
        code=cast(JudgedCode, s.code),
        steps=[WeatherStepOut(**asdict(x)) for x in s.steps],
        lower_is_worse=s.lower_is_worse,
    )
    for s in judge.scales()
]


def _night(row: sqlite3.Row, rank: int) -> WeatherNightOut:
    summary = json.loads(row["summary_json"])
    if rank >= FULL_NIGHTS:
        # the trend carries nothing read from the hours
        summary.update(
            measures=[],
            usable_hours=None,
            usable_since=None,
            usable_until=None,
            wind_700hpa_kmh=None,
            wind_700hpa_tenths=None,
        )
        return WeatherNightOut(night=row["night_date"], trend=True, hours=[], **summary)
    return WeatherNightOut(
        night=row["night_date"], trend=False, hours=json.loads(row["hours_json"]), **summary
    )


def _seeing(conn: sqlite3.Connection, site_id: int, arrived: dict[str, str]) -> WeatherSeeingOut:
    """Meteoblue's last attempt only with a key: it is what lets the page say why there is no
    seeing."""
    seeing_source = "meteoblue" if "meteoblue" in arrived else None
    key = bool(config.read(conn).meteoblue_key)
    last = meteoblue.last_attempt(conn, site_id) if key else None
    return WeatherSeeingOut(
        key=key, source=seeing_source, meteoblue=last["status"] if last else None
    )


@router.get("/weather", response_model=WeatherOut)
def weather(conn: sqlite3.Connection = Depends(get_db)) -> WeatherOut:
    """The coming nights of the home site, from the model chosen in the preferences, as the
    forecast wrote them: changing model is reading another row.

    Without a home site `site` is `null` and there are no nights; with a site whose time zone is
    missing or unknown, `missing` is `no_timezone`.

    **Three full nights, then a trend**: from the fourth (`trend`) only the verdict, the clouds,
    the dark hours and the agreement, without usable hours, measures, hours or upper wind. Seeing
    comes only from Meteoblue: an hour it does not cover stays empty. `scales` are the thresholds
    the judgement used, for the page to draw."""
    chosen = config.read(conn).weather_model
    empty = WeatherOut(
        site=None,
        missing=None,
        model=chosen,
        models=list(openmeteo.MODELS),
        fetched_at=None,
        full_nights=FULL_NIGHTS,
        seeing=WeatherSeeingOut(
            key=bool(config.read(conn).meteoblue_key), source=None, meteoblue=None
        ),
        sources=[],
        scales=SCALES,
        nights=[],
    )
    home = home_site(conn)
    if home is None:
        return empty
    current = night_date(now_iso(), home["timezone"]) if home["timezone"] else None
    if current is None:
        return empty.model_copy(
            update={"site": home["name"], "missing": forecast.Outcome.NO_TIMEZONE}
        )
    rows = conn.execute(_NIGHTS, (home["id"], chosen, current)).fetchall()
    arrived = {
        r["source"]: r["fetched_at"]
        for r in conn.execute(_ARRIVED, (home["id"], forecast.KIND, *sky.ALL_SOURCES, current))
    }
    return empty.model_copy(
        update={
            "site": home["name"],
            "fetched_at": conn.execute(
                _LAST_FETCHED, (home["id"], forecast.KIND, forecast.source_of("%"))
            ).fetchone()[0],
            "nights": [_night(r, i) for i, r in enumerate(rows[:MAX_NIGHTS])],
            "seeing": _seeing(conn, home["id"], arrived),
            "sources": [WeatherSourceOut(source=f, fetched_at=q) for f, q in arrived.items()],
        }
    )


@router.post("/weather/refresh", response_model=WeatherRefreshOut)
def refresh(conn: sqlite3.Connection = Depends(get_db)) -> WeatherRefreshOut:
    """Asks for the forecast now. If the service is silent the previous one stays, and the reply
    says why."""
    home = home_site(conn)
    status = rounds.refresh(conn, dict(home) if home else None)
    return WeatherRefreshOut(status=cast(RefreshStatus, status))


def brief_of(conn: sqlite3.Connection, site_id: int, night: str) -> WeatherBriefOut | None:
    """One night's summary from the chosen model, as written; Tonight reads it."""
    chosen = config.read(conn).weather_model
    row = conn.execute(_NIGHTS + " LIMIT 1", (site_id, chosen, night)).fetchone()
    if row is None or row["night_date"] != night:
        return None
    return WeatherBriefOut(**json.loads(row["summary_json"]))


REMOVED: Final = "removed"


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
    trimmed = (body.key or "").strip()
    if not trimmed:
        with transaction(conn):
            config.write(conn, "meteoblue_key", None)
            meteoblue.forget(conn)
            home = home_site(conn)
            if home is not None:
                view.rebuild(conn, dict(home))
        return MeteoblueKeyOut(status=REMOVED, hint=None)
    outcome = meteoblue.check_key(trimmed)
    if outcome != forecast.Outcome.OK:
        return MeteoblueKeyOut(
            status=cast(KeyStatus, outcome), hint=config.hint(config.read(conn).meteoblue_key)
        )
    with transaction(conn):
        config.write(conn, "meteoblue_key", trimmed)
        meteoblue.forget(conn)
    home = home_site(conn)
    if home is not None:
        rounds.refresh(conn, dict(home))
    return MeteoblueKeyOut(status=cast(KeyStatus, outcome), hint=config.hint(trimmed))
