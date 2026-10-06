"""The ephemerides are imported at the top, not lazily: their import is what disarms astropy's
downloads, so a lazy import would leave the process online until this route first ran."""

import sqlite3
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends

from ..clock import midnight_of, night_date, night_window, now_iso
from ..ephemeris import moon, sun
from ..spine.group_store import home_site
from ..units import bortle_of
from . import weather
from .deps import get_db
from .models_tonight import (
    MoonOut,
    PhaseKey,
    SiteSkyOut,
    SkyBandOut,
    SkyKind,
    SkyPointOut,
    TonightOut,
)

router = APIRouter(prefix="/api/v1", tags=["stanotte"])


def _iso(istante: datetime | None) -> str | None:
    return istante.isoformat() if istante else None


def _sito(riga: dict[str, Any]) -> SiteSkyOut:
    # The class comes from `units`, which the site card uses too: two conversions would drift.
    return SiteSkyOut(name=riga["name"], sky_sqm=riga["sky_sqm"], bortle=bortle_of(riga["sky_sqm"]))


def _sky_band(band: sun.SkyBand) -> SkyBandOut:
    return SkyBandOut(
        starts_at=band.starts_at.isoformat(),
        ends_at=band.ends_at.isoformat(),
        kind=cast(SkyKind, band.kind),
    )


def _sky_point(point: moon.TrackPoint) -> SkyPointOut:
    return SkyPointOut(at=point.at.isoformat(), altitude_deg=point.altitude_deg)


@router.get("/tonight", response_model=TonightOut)
def tonight(conn: sqlite3.Connection = Depends(get_db)) -> TonightOut:
    """Tonight's Moon from the home site, with the night's sky bands and its forecast summary.

    **The night is the app's**, noon to noon in the site's time zone (`clock.night_date`), not a
    calendar day: whoever looks at two in the morning is still in last night, and wants last
    night's Moon. The window is measured **between the two true noons**, not at a fixed
    twenty-four hours: the clock-change night lasts 23 or 25. **The phase is asked at midnight**,
    not at noon: asked at the window's start, whoever looks at the bar at eleven in the evening
    would read the number of twelve hours earlier.

    **Without a home site there is nothing to say**, and it says so: `night`, `site` and `moon`
    are `null`. A Moon computed on an invented place would be a number that looks true. The site,
    when there is one, **travels with its sky**: the bar's footer writes the place and its class in
    one line, and asking two routes for them would leave a moment when the page is half done. A
    site whose time zone is missing or no longer known still comes out, without its night and its
    Moon (`night` and `moon` `null`): falling back to Greenwich would give another place's Moon
    without anyone noticing.

    **The computation is costly**, because it samples a night of sky twice, once per body. The
    reply carries the night it refers to, so whoever shows it knows when it has expired without
    asking again at every breath."""
    riga = home_site(conn)
    if riga is None:
        return TonightOut(night=None, site=None, moon=None)
    sito = dict(riga)

    notte = night_date(now_iso(), sito["timezone"])
    # Midnight as `clock` composes it, the instant the Nights page uses too: otherwise two screens
    # would ask the same night at two different moments.
    mezzanotte = midnight_of(notte, sito["timezone"]) if notte else None
    if notte is None or mezzanotte is None:
        # A moment later the computation would raise and the route would become a 500.
        return TonightOut(night=None, site=_sito(sito), moon=None)
    comincia, quante_ore = night_window(notte, sito["timezone"])

    fase = moon.phase(mezzanotte)
    cielo = moon.night_track(comincia, sito["latitude"], sito["longitude"], hours=quante_ore)
    return TonightOut(
        night=notte,
        site=_sito(sito),
        weather=weather.brief_of(conn, sito["id"], notte),
        sky_bands=[
            _sky_band(f)
            for f in sun.night_bands(
                comincia, sito["latitude"], sito["longitude"], hours=quante_ore
            )
        ],
        moon=MoonOut(
            phase_key=cast(PhaseKey, fase.phase_key),
            illumination_pct=fase.illumination_pct,
            rise=_iso(cielo.rise),
            set=_iso(cielo.set),
            highest=_sky_point(cielo.highest),
            track=[_sky_point(p) for p in cielo.track],
            ceiling_deg=moon.sky_ceiling(sito["latitude"]),
            lit_side=moon.lit_side(fase.phase_key, sito["latitude"]),
        ),
    )
