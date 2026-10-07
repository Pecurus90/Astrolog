"""A site's forecast nights as the page reads them: each model's hours joined with the sky sources
and the Moon, every measure judged, the agreement counted. The writer calls it, never the reader."""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from ..db.replace_table import replace_rows
from ..ephemeris import RISESET_DEG, moon
from . import judge, openmeteo, position, verdict
from .fetches import Source

KIND = "forecast"
SKY_SOURCES = (Source.CAMS, Source.METEOBLUE)
# What the sky sources may bring: every hour carries them, `None` where no source gave a value.
SKY_FIELDS = ("seeing_arcsec", "aerosol_optical_depth", "dust_ugm3")
COLUMNS = ("site_id", "night_date", "model", "fetched_at", "hours_json", "summary_json")

_MODEL_SOURCES = tuple(f"open-meteo/{m}" for m in openmeteo.MODELS)
_IN_MODELS = ", ".join("?" * len(_MODEL_SOURCES))  # segnaposto-ok: the models, constants
_IN_SKY = ", ".join("?" * len(SKY_SOURCES))  # segnaposto-ok: the sources, constants
_MODEL_ROWS = (
    "SELECT night_date, source, fetched_at, hourly_json FROM weather_nights"  # noqa: S608
    f" WHERE site_id = ? AND kind = ? AND source IN ({_IN_MODELS})"
)
_SKY_ROWS = (
    "SELECT hourly_json FROM weather_nights"  # noqa: S608
    f" WHERE site_id = ? AND kind = ? AND source IN ({_IN_SKY})"
)


@dataclass(frozen=True, slots=True)
class _Night:
    night: str
    model: str
    fetched_at: str
    hours: list[verdict.Hour]
    summary: verdict.Summary


def _sky_by_hour(conn: sqlite3.Connection, site_id: int) -> dict[str, dict[str, Any]]:
    """Every sky source's known values by local instant; an hour a source does not give is
    absent, never filled in."""
    by_hour: dict[str, dict[str, Any]] = {}
    for r in conn.execute(_SKY_ROWS, (site_id, KIND, *SKY_SOURCES)):
        for o in json.loads(r["hourly_json"]):
            by_hour.setdefault(o["at"], {}).update(
                {k: v for k, v in o.items() if k != "at" and v is not None}
            )
    return by_hour


def _moon_by_hour(site: Mapping[str, Any], instants: Sequence[str]) -> dict[str, int | None]:
    """The Moon's lit percentage for the hours it is above the horizon, else `None`."""
    times = [datetime.fromisoformat(a) for a in instants]
    alts = moon.altitudes(times, site["latitude"], site["longitude"])
    lit = moon.phases(times)
    return {
        a: p.illumination_pct if alt > RISESET_DEG else None
        for a, alt, p in zip(instants, alts, lit, strict=True)
    }


def _agreement(said: Sequence[verdict.Verdict | None], total: int) -> dict[str, int]:
    """How many models say go, marginal, nogo or do not know; a model that wrote nothing that
    night does not know, it is not one model fewer."""
    counts: dict[str, int] = {**dict.fromkeys(verdict.Verdict, 0), "unknown": 0}
    for v in [*said, *[None] * (total - len(said))]:
        counts[v or "unknown"] += 1
    return {**counts, "total": total}


def _hours_json(hours: Sequence[verdict.Hour]) -> str:
    return json.dumps([{**h.row(), "levels": judge.hour_levels(h)} for h in hours])


def _rows(
    site: Mapping[str, Any], written: Sequence[_Night], usual: list[float] | None
) -> list[tuple[Any, ...]]:
    rows = []
    for w in written:
        said = [x.summary.verdict for x in written if x.night == w.night]
        wind = w.summary.wind_700hpa_kmh
        summary = {
            **asdict(w.summary),
            "wind_700hpa_tenths": position.tenths_below(usual, wind)
            if usual and wind is not None
            else None,
            "agreement": _agreement(said, len(openmeteo.MODELS)),
            "measures": [asdict(m) for m in judge.measures(w.hours, w.summary)],
        }
        rows.append(
            (site["id"], w.night, w.model, w.fetched_at, _hours_json(w.hours), json.dumps(summary))
        )
    return rows


def rebuild(conn: sqlite3.Connection, site: Mapping[str, Any]) -> None:
    """All of the site's nights or none; other sites stay."""
    sky = _sky_by_hour(conn, site["id"])
    models = conn.execute(_MODEL_ROWS, (site["id"], KIND, *_MODEL_SOURCES)).fetchall()
    series = {(r["night_date"], r["source"]): json.loads(r["hourly_json"]) for r in models}
    instants = sorted({o["at"] for hours in series.values() for o in hours})
    lit = _moon_by_hour(site, instants) if instants else {}
    written = []
    for r in models:
        hours = [
            verdict.Hour(
                at=o["at"],
                sky=o["sky"],
                values={
                    **{k: v for k, v in o.items() if k not in ("at", "sky")},
                    **dict.fromkeys(SKY_FIELDS),
                    **sky.get(o["at"], {}),
                    "moon_pct": lit[o["at"]],
                },
            )
            for o in series[r["night_date"], r["source"]]
        ]
        model = r["source"].removeprefix("open-meteo/")
        written.append(
            _Night(r["night_date"], model, r["fetched_at"], hours, verdict.assess(hours))
        )
    replace_rows(
        conn,
        "weather_view",
        COLUMNS,
        _rows(site, written, position.percentiles(conn, site)),
        where="site_id = ?",
        args=(site["id"],),
    )
