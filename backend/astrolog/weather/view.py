"""A site's forecast nights as the page reads them: each model's hours joined with the sky sources
and the Moon, every measure judged, the agreement counted. The writer calls it, never the reader."""

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from ..db import config
from ..db.replace_table import replace_rows
from ..ephemeris import RISESET_DEG, moon, planets, sun
from ..ephemeris.sun import Sky
from ..levels import MoonRule
from ..site_of import Site
from . import events, judge, openmeteo, position, score, setups, verdict
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


def _moon_by_hour(site: Site, instants: Sequence[str], floor_deg: float) -> dict[str, int | None]:
    """The Moon's lit percentage for the hours it counts (above the rule's floor), else `None`."""
    times = [datetime.fromisoformat(a) for a in instants]
    alts = moon.altitudes(times, site.latitude, site.longitude)
    lit = moon.phases(times)
    return {
        a: p.illumination_pct if alt > floor_deg else None
        for a, alt, p in zip(instants, alts, lit, strict=True)
    }


def _skies(
    site: Site, summaries: Sequence[verdict.Summary]
) -> dict[tuple[str, str], events.NightSky]:
    """Each drawn window sampled once; the Moon of all windows in one ephemeris call."""
    windows = sorted(
        {
            (s.shown_from, s.shown_until)
            for s in summaries
            if s.shown_from is not None and s.shown_until is not None
        }
    )
    starts = [datetime.fromisoformat(a) for a, _ in windows]
    hours = [
        (datetime.fromisoformat(b) - start).total_seconds() / 3600
        for start, (_, b) in zip(starts, windows, strict=True)
    ]
    lat, lon = site.latitude, site.longitude
    moons = moon.night_tracks(list(zip(starts, hours, strict=True)), lat, lon) if windows else []
    return {
        w: events.NightSky(
            bands=sun.night_bands(start, lat, lon, h),
            moon_night=m,
            planet_nights=planets.night_tracks(start, lat, lon, h),
            lit_at_rise=None if m.rise is None else moon.phase(m.rise).illumination_pct,
        )
        for w, start, h, m in zip(windows, starts, hours, moons, strict=True)
    }


_NO_SKY = {"moon_event": None, "moon_event_at": None, "moon_track": [], "sky_bands": []}


def _sky_fields(w: _Night, sky: events.NightSky | None, rule: MoonRule) -> dict[str, Any]:
    """The Moon, the twilight bands and the night's events (step 13.1) as the summary has them."""
    if sky is None or sky.moon_night is None:
        return {**_NO_SKY, "events": []}
    found = events.night_events(w.hours, sky, rule)
    return {
        **_moon_night(sky.moon_night),
        "sky_bands": [
            {
                "starts_at": b.starts_at.isoformat(),
                "ends_at": b.ends_at.isoformat(),
                "kind": b.kind.value,
            }
            for b in sky.bands
        ],
        "events": [asdict(e) for e in found],
    }


def _moon_night(night: moon.MoonNight) -> dict[str, Any]:
    """The Moon over the drawn hours, every quarter hour, and its first crossing: up at the start
    it sets or stays (`up`), down it rises or stays (`down`)."""
    up = night.grid[0].altitude_deg > RISESET_DEG
    at = night.set if up else night.rise
    track = [
        {"at": p.at.isoformat(timespec="minutes"), "altitude_deg": p.altitude_deg}
        for p in night.track
    ]
    if at is None:
        return {"moon_event": "up" if up else "down", "moon_event_at": None, "moon_track": track}
    return {
        "moon_event": "set" if up else "rise",
        "moon_event_at": at.isoformat(timespec="minutes"),
        "moon_track": track,
    }


def _tenths(value: float | None) -> float | None:
    return None if value is None else round(value, 1)


def _agreement(said: Sequence[verdict.Verdict | None], total: int) -> dict[str, int]:
    """How many models say go, marginal, nogo or do not know; a model that wrote nothing that
    night does not know, it is not one model fewer."""
    counts: dict[str, int] = {**dict.fromkeys(verdict.Verdict, 0), "unknown": 0}
    for v in [*said, *[None] * (total - len(said))]:
        counts[v or "unknown"] += 1
    return {**counts, "total": total}


def _hours_json(hours: Sequence[verdict.Hour], summary: verdict.Summary, rule: MoonRule) -> str:
    """Each hour with its words, whether the page draws it and whether it is one of the clear hours
    of the night, the same the usable hours count."""
    shown = {h.at for h in judge.shown_hours(hours, summary)}
    night, _ = verdict.window(hours)
    judged = {h.at for h in night}
    exposure = score.hourly_exposure(hours)
    return json.dumps(
        [
            {
                **h.row(),
                **judge.shown_values({**h.values, "dew_spread_c": judge.spread(h)}),
                "levels": judge.hour_levels(h, rule),
                "transparency": _tenths(score.transparency(h)),
                "exposure_hours": exposure.get(h.at),
                "shown": h.at in shown,
                "clear": summary.usable_hours is not None
                and h.at in judged
                and verdict.is_clear(h),
            }
            for h in hours
        ]
    )


def _rows(
    site: Site,
    written: Sequence[_Night],
    usual: list[float] | None,
    rule: MoonRule,
    rigs: Sequence[setups.Rig],
) -> list[tuple[Any, ...]]:
    rows = []
    summaries = [w.summary for w in written]
    skies = _skies(site, summaries)
    for w in written:
        sky = skies.get((w.summary.shown_from or "", w.summary.shown_until or ""))
        said = [x.summary.verdict for x in written if x.night == w.night]
        wind = w.summary.wind_700hpa_kmh
        summary = {
            **asdict(w.summary),
            "wind_700hpa_tenths": position.tenths_below(usual, wind)
            if usual and wind is not None
            else None,
            "agreement": _agreement(said, len(openmeteo.MODELS)),
            "sky_word": verdict.sky_word(w.summary.cloud_total_pct),
            # the dark with the Moon below the rule's floor: the hours good for broadband
            "moonless_dark_hours": sum(
                1 for h in w.hours if h.sky == Sky.DARK and h.values.get("moon_pct") is None
            ),
            "measures": [asdict(m) for m in judge.measures(w.hours, w.summary, rule)],
            **_sky_fields(w, sky, rule),
        }
        summary["setups"] = setups.judged(setups.seeing_of(summary["measures"]), rigs)
        rows.append(
            (
                site.id,
                w.night,
                w.model,
                w.fetched_at,
                _hours_json(w.hours, w.summary, rule),
                json.dumps(summary),
            )
        )
    return rows


# The keys of a written hour that are not its quantities.
_NOT_VALUES = ("at", "sky", "dark", "nautical", "down")


def rebuild(conn: sqlite3.Connection, site: Site) -> None:
    """All of the site's nights or none; other sites stay."""
    sky = _sky_by_hour(conn, site.id)
    models = conn.execute(_MODEL_ROWS, (site.id, KIND, *_MODEL_SOURCES)).fetchall()
    series = {(r["night_date"], r["source"]): json.loads(r["hourly_json"]) for r in models}
    instants = sorted({o["at"] for hours in series.values() for o in hours})
    rule = config.moon_rule(config.read(conn))
    lit = _moon_by_hour(site, instants, rule.floor_deg) if instants else {}
    written = []
    for r in models:
        hours = [
            verdict.Hour(
                at=o["at"],
                sky=o["sky"],
                dark=o.get("dark"),
                down=o.get("down"),
                nautical=o.get("nautical"),
                values={
                    **{k: v for k, v in o.items() if k not in _NOT_VALUES},
                    **dict.fromkeys(SKY_FIELDS),
                    **sky.get(o["at"], {}),
                    "moon_pct": lit[o["at"]],
                },
            )
            for o in series[r["night_date"], r["source"]]
        ]
        model = r["source"].removeprefix("open-meteo/")
        summary = score.assess(hours, rule)
        written.append(_Night(r["night_date"], model, r["fetched_at"], hours, summary))
    replace_rows(
        conn,
        "weather_view",
        COLUMNS,
        _rows(site, written, position.percentiles(conn, site), rule, setups.rigs(conn)),
        where="site_id = ?",
        args=(site.id,),
    )
