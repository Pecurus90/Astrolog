"""Where a solar-system body stands as seen from a site: shared by the Moon and the Sun, so the
most delicate computation exists once."""

import datetime as dt
from collections.abc import Sequence

from astropy.coordinates import (
    AltAz,
    BaseCoordinateFrame,
    EarthLocation,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time


def quando(istante: dt.datetime) -> Time:
    """Read as UTC, a naive instant would put a distant site's night half a day off."""
    if istante.tzinfo is None:
        raise ValueError(
            "un istante senza fuso non si indovina: sarebbe letto come UTC, e la notte di un"
            " sito lontano risulterebbe sbagliata di mezza giornata"
        )
    return Time(istante.astimezone(dt.UTC))


def convertito(corpo: SkyCoord, sistema: BaseCoordinateFrame) -> SkyCoord:
    """astropy declares the transform may return nothing: checked here, so callers get a
    `SkyCoord` and don't silence the stub one by one."""
    dentro = corpo.transform_to(sistema)
    if dentro is None:
        raise RuntimeError(f"astropy non ha convertito in {type(sistema).__name__}")
    return dentro


def altezze(
    corpo: str, istanti: Sequence[dt.datetime], latitude: float, longitude: float
) -> list[float]:
    """Topocentric (the Moon's parallax is nearly a degree) and geometric: refraction lives in
    `RISESET_DEG`, a threshold, not in the altitude. One astropy call for the whole grid."""
    dove = EarthLocation(lat=latitude, lon=longitude)
    momenti = Time([quando(i) for i in istanti])
    # get_sun is the cheaper path and agrees with get_body("sun"); the Moon needs the site.
    astro = get_sun(momenti) if corpo == "sun" else get_body(corpo, momenti, dove)
    sopra = convertito(astro, AltAz(obstime=momenti, location=dove))
    gradi = sopra.alt.deg  # pyright: ignore[reportOptionalMemberAccess]
    return [float(a) for a in gradi]  # pyright: ignore[reportArgumentType, reportOptionalIterable]
