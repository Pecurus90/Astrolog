"""Score v4 (ADR 0034): hourly Transparency, mean weighted by minutes of dark, verdict, exposure
hours. Lost light multiplies, as DES effective time (Neilsen et al. 2019, arXiv 1912.06254)."""

import math
from collections.abc import Sequence

from ..levels import Verdict
from . import judge
from .judge import Measure
from .verdict import Hour, Summary, is_clear, mean_of, shown, weighted, when, window

# The rules that zero an hour: their "no" is the judge's, one home for the thresholds.
_BLOCKING = (Measure.RAIN, Measure.VISIBILITY, Measure.CLOUD, Measure.WIND, Measure.GUST)

GOOD_FROM = 70.0  # [P ADR 0034]
UNCERTAIN_FROM = 40.0  # [P ADR 0034]
# The aerosol scale's "clear" step: the haze starts where its word stops.
CLEAR_AOD = judge.SCALES[Measure.AEROSOL].steps[-1].bound
AOD_FACTOR = 2.0  # [P ADR 0034] e^(-2 (AOD - 0.1)), 550 nm at the zenith


def transparency(h: Hour) -> float | None:
    """0-100: zero when a rule blocks the hour, else the light the clouds and the aerosol leave."""
    clouds = h.values.get("cloud_total_pct")
    if clouds is None:
        return None
    scales = [judge.SCALES[m] for m in _BLOCKING]
    if any(judge.level(s, s.read(h)) == Verdict.NOGO for s in scales):
        return 0.0
    aod = h.values.get("aerosol_optical_depth")
    haze = 1.0 if aod is None else min(1.0, math.exp(-AOD_FACTOR * (aod - CLEAR_AOD)))
    return 100.0 * (1 - clouds / 100) * haze


def _verdict(value: float | None) -> Verdict | None:
    if value is None:
        return None
    if value >= GOOD_FROM:
        return Verdict.GO
    return Verdict.MARGINAL if value >= UNCERTAIN_FROM else Verdict.NOGO


def assess(hours: Sequence[Hour]) -> Summary:
    """Verdict, Transparency and exposure are `None` unless every window hour has its clouds. The
    clear hours (`usable_*`) stay the clouds' own, for the pages not yet on score v4."""
    night, span = window(hours)
    after = {h.at: n.at for h, n in zip(hours, hours[1:], strict=False)}
    shares, _ = weighted(hours)
    lights = [transparency(h) for h, _ in shares]
    complete = bool(shares) and None not in lights
    dark = sum(w for _, w in shares)
    kept = sum(t * w for t, (_, w) in zip(lights, shares, strict=True) if t is not None)
    clarity = round(kept / dark, 1) if complete and dark else None
    cover = [h.values.get("cloud_total_pct") for h in night]
    clouds_known = bool(night) and None not in cover
    since, until, clear = when(night, is_clear, after)
    shown_from, shown_until = shown(hours)
    return Summary(
        verdict=_verdict(clarity),
        cloud_total_pct=mean_of(night, "cloud_total_pct") if clouds_known else None,
        usable_hours=clear if clouds_known else None,
        usable_since=since if clouds_known else None,
        usable_until=until if clouds_known else None,
        window=span,
        window_hours=len(night),
        shown_from=shown_from,
        shown_until=shown_until,
        wind_700hpa_kmh=mean_of(night, "wind_700hpa_kmh"),
        transparency=clarity,
        exposure_hours=round(kept / 100, 1) if clarity is not None else None,
        dark_hours=round(dark, 1),
        without_aerosol=any(h.values.get("aerosol_optical_depth") is None for h, _ in shares),
    )
