"""Where a fixed point of the sky stood from a site: erfa, as pipeline/sky.py (ADR 0030).
Geometric: the refraction is airmass.apparent_altitude's."""

import datetime as dt
import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass

import erfa
import numpy as np
from erfa import ErfaWarning


@dataclass(frozen=True, slots=True)
class Observed:
    altitude_deg: float
    azimuth_deg: float  # from North towards East, [0, 360)
    hour_angle_h: float  # [-12, +12): negative before the transit (Image Analysis par. 2.1.1)


def observed(
    skies: Sequence[tuple[float, float]],
    instants: Sequence[dt.datetime],
    sites: Sequence[tuple[float, float]],
) -> list[Observed]:
    """Per point (RA, Dec J2000), UTC instant, site (lat, lon East +); one erfa call, place of date.
    No pressure: no refraction. UT1 as UTC: under a second, a hundredth of a degree."""
    if not skies:
        return []
    days = [_utc_days(i) for i in instants]
    ra, dec = (np.radians([s[k] for s in skies]) for k in (0, 1))
    lat, lon = (np.radians([s[k] for s in sites]) for k in (0, 1))
    zeros = np.zeros(len(skies))
    with warnings.catch_warnings():  # year past leap-second table: 'dubious year', fine here
        warnings.simplefilter("ignore", ErfaWarning)
        azimuth, zenith, hour, *_ = erfa.atco13(
            ra, dec, zeros, zeros, zeros, zeros, np.array([d[0] for d in days]),
            np.array([d[1] for d in days]), zeros, lon, lat, zeros, zeros, zeros, zeros, zeros,
            zeros, zeros + 0.55,
        )  # fmt: skip
    return [
        Observed(90.0 - math.degrees(float(z)), math.degrees(float(a)) % 360.0,
                 (math.degrees(float(h)) / 15.0 + 12.0) % 24.0 - 12.0)
        for a, z, h in zip(azimuth, zenith, hour, strict=True)
    ]  # fmt: skip


def _utc_days(instant: dt.datetime) -> tuple[float, float]:
    if instant.tzinfo is None:
        raise ValueError("istante senza fuso")
    t = instant.astimezone(dt.UTC)
    seconds = t.second + t.microsecond / 1e6
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ErfaWarning)
        return erfa.dtf2d("UTC", t.year, t.month, t.day, t.hour, t.minute, seconds)
