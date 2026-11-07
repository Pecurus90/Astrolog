"""The site's sky from its frames (docs/domini/sito.md, ADR 0039): good frames, night medians, the
annual level under the season. Written by who changes frames, bias, filters or sites."""

import datetime as dt
import math
import sqlite3
import statistics
from dataclasses import dataclass

import numpy as np

from ..clock import night_date
from ..db.replace_table import replace_rows
from ..site_of import Site, known_sites, site_at
from ..sqm_shots import SQM_SHOTS
from ..twilight import ASTRO_DEG
from ..units import hundredths
from .frame_rules import LOW_EXTENDED_DEG

# "No-Sun no-Moon": "Sun below -18 deg and Moon below -5 deg" (Sun: astronomical night,
# `twilight.ASTRO_DEG`); Moon light still reaches the sky just under the horizon
MOON_BELOW_DEG = -5.0  # [C Bara et al. 2021, arXiv 2104.10616]
WINDOW_MONTHS = 12  # [D ADR 0039]
# Enough to separate the level from the season [D ADR 0039: "6 months" skews up to 0.13 mag]
MIN_MONTHS = 4
MAX_HOLE_MONTHS = 3  # [D ADR 0039]
# One wave a year, "m0 + A sin[2 pi (t - t0)]" without the trend
YEAR_DAYS = 365.25  # [C Shah et al. 2025, arXiv 2507.11343 App. F]

# Frames that count: sky brightness with the bias, dark sky, not low (the sky is extended), the
# shots SQM is for. Card of the measured file: the one that gave Sun and Moon.
GOOD = (  # SQM_SHOTS is a constant: nothing from outside in the text
    "SELECT k.mid_utc, q.sqm, c.site_lat_deg, c.site_lon_deg"  # noqa: S608
    " FROM pipeline_sqm AS q JOIN pipeline_sky AS k ON k.frame_id = q.frame_id"
    " JOIN pipeline_measures AS m ON m.frame_id = q.frame_id"
    " JOIN pipeline_cards AS c ON c.file_id = m.file_id"
    " LEFT JOIN pipeline_filter_spellings AS p ON p.written = c.filter"
    " WHERE q.sqm IS NOT NULL AND q.bias_adu IS NOT NULL"
    " AND k.sun_altitude_deg < :sun AND k.moon_altitude_deg < :moon AND k.altitude_deg > :low"
    f" AND {SQM_SHOTS}"
)

COLUMNS = ("site_id", "nights", "months", "sqm", "first_night", "last_night", "computed_at")


@dataclass(frozen=True, slots=True)
class SkyLevel:
    nights: int
    months: int
    sqm: float | None  # None: too few months, or a hole too long
    first_night: str
    last_night: str


def level_of(nights: dict[str, float]) -> SkyLevel:
    """Night date -> its median. The 12 calendar months up to the last night: an old archive
    counts as well (sito.md)."""
    last = dt.date.fromisoformat(max(nights))
    start = _month_index(last) - WINDOW_MONTHS + 1
    kept = {d: v for d, v in nights.items() if _month_index(dt.date.fromisoformat(d)) >= start}
    covered = {_month_index(dt.date.fromisoformat(d)) - start for d in kept}
    enough = len(covered) >= MIN_MONTHS and _longest_hole(covered) <= MAX_HOLE_MONTHS
    return SkyLevel(
        nights=len(kept), months=len(covered), sqm=_annual(kept) if enough else None,
        first_night=min(kept), last_night=max(kept),
    )  # fmt: skip


def _month_index(day: dt.date) -> int:
    return day.year * 12 + day.month - 1


def _longest_hole(covered: set[int]) -> int:
    """Empty months in a row, around the circle: the fit is periodic, December touches January."""
    ordered = sorted(covered)
    gaps = [b - a - 1 for a, b in zip(ordered, ordered[1:], strict=False)]
    return max([*gaps, ordered[0] + WINDOW_MONTHS - ordered[-1] - 1])


def _annual(nights: dict[str, float]) -> float | None:
    """Least squares of level + one yearly wave, then the median of the nights without the wave
    (sito.md: the median of the nights; a cloudy night over town does not move it)."""
    days = [dt.date.fromisoformat(d).toordinal() for d in nights]
    phase = 2 * math.pi * np.array(days) / YEAR_DAYS
    y = np.array(list(nights.values()))
    design = np.column_stack([np.ones_like(phase), np.cos(phase), np.sin(phase)])
    (_, a, b), *_ = np.linalg.lstsq(design, y, rcond=None)
    return hundredths(statistics.median((y - a * np.cos(phase) - b * np.sin(phase)).tolist()))


def rebuild(conn: sqlite3.Connection, now: str) -> None:
    """All sites at once, in the caller's transaction."""
    rows = []
    for site_id, nights in _nights_per_site(conn).items():
        level = level_of({d: statistics.median(v) for d, v in nights.items()})
        rows.append((site_id, level.nights, level.months, level.sqm, level.first_night,
                     level.last_night, now))  # fmt: skip
    replace_rows(conn, "site_sky_measures", COLUMNS, rows)


def _nights_per_site(conn: sqlite3.Connection) -> dict[int, dict[str, list[float]]]:
    """Frames go where their nights go (`site_of.site_at`); a site without a zone has no nights."""
    known = known_sites(conn)
    places: dict[tuple[float, float], Site | None] = {}
    per_site: dict[int, dict[str, list[float]]] = {}
    limits = {"sun": ASTRO_DEG, "moon": MOON_BELOW_DEG, "low": LOW_EXTENDED_DEG}
    for row in conn.execute(GOOD, limits):
        point = (row["site_lat_deg"], row["site_lon_deg"])
        if point not in places:
            found = site_at(conn, *point, known)
            places[point] = found[0] if isinstance(found, tuple) else None
        site = places[point]
        if site is None or not site.timezone:
            continue
        night = night_date(row["mid_utc"], site.timezone)
        if night is not None:
            per_site.setdefault(site.id, {}).setdefault(night, []).append(row["sqm"])
    return per_site
