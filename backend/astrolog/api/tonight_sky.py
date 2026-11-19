"""Tonight's sky written once, read by `tonight` (#96): over a second per read on a NAS. In `api/`,
not `spine/`: it stores the route's reply. Ephemerides imported eagerly: that disarms astropy."""

import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Literal, cast

from ..clock import midnight_of, night_date, night_window, now_iso, seconds_between
from ..db import config
from ..db.replace_table import replace_rows
from ..ephemeris import moon, planets, sun
from ..levels import Verdict, moon_level
from ..site_of import Site, home_site
from .models_tonight import (
    ChartOut,
    Compass,
    DarkStretchOut,
    MoonInDarkOut,
    MoonOut,
    MoonPointOut,
    PhaseKey,
    PlanetKey,
    PlanetOut,
    ShootingStretchOut,
    SkyBandOut,
    SkyKind,
    SkyPointOut,
    TonightOut,
)
from .models_weather import Level

log = logging.getLogger(__name__)

COLUMNS = ("site_id", "night_date", "latitude", "longitude", "timezone", "sky_json")


def _iso(instant: datetime | None) -> str | None:
    return instant.isoformat() if instant else None


def _sky_band(band: sun.SkyBand) -> SkyBandOut:
    return SkyBandOut(
        starts_at=band.starts_at.isoformat(),
        ends_at=band.ends_at.isoformat(),
        kind=cast(SkyKind, band.kind),
    )


def _sky_point(point: moon.TrackPoint) -> SkyPointOut:
    return SkyPointOut(at=point.at.isoformat(), altitude_deg=point.altitude_deg)


def _moon_in_dark(
    up: list[moon.Stretch], dark: list[moon.Stretch], word: Verdict
) -> MoonInDarkOut | None:
    if not up:
        return None
    return MoonInDarkOut(
        level=cast(Level, word),
        since=up[0][0].isoformat(),
        until=up[-1][1].isoformat(),
        from_start=up[0][0] == dark[0][0],
        to_end=up[-1][1] == dark[-1][1],
    )


def _planet(night: planets.PlanetNight, span: sun.ChartWindow | None) -> PlanetOut:
    track = [_sky_point(q) for q in night.track]
    out = PlanetOut(key=cast(PlanetKey, night.key.value), track=track)
    if span is None:
        return out
    inside = planets.within(night, span.starts_at, span.ends_at)
    out.rise, out.set = _iso(inside.rise), _iso(inside.set)
    out.highest = _sky_point(inside.highest)
    return out


def _highest_in(track: list[moon.TrackPoint], span: sun.ChartWindow | None) -> SkyPointOut | None:
    inside = [p for p in track if span and span.starts_at <= p.at <= span.ends_at]
    return _sky_point(max(inside, key=lambda p: p.altitude_deg)) if inside else None


def _highest_planet(out: list[PlanetOut]) -> PlanetKey | None:
    up = [p for p in out if p.highest and p.highest.altitude_deg > planets.PLANET_RISESET_DEG]
    if not up:
        return None
    return max(up, key=lambda p: p.highest.altitude_deg if p.highest else 0.0).key


def _shooting(spans: moon.DarkSpans, word: Verdict) -> list[ShootingStretchOut]:
    """Moonless and Moon-up stretches in time order, each with its band; neighbours of one band
    join, so a dim Moon rising adds no seam."""
    narrow = word == Verdict.NOGO
    marked = sorted(
        [(a, b, "broadband") for a, b in spans.moonless]
        + [(a, b, "narrowband" if narrow else "broadband") for a, b in spans.moon_up]
    )
    joined: list[tuple[datetime, datetime, str]] = []
    for a, b, band in marked:
        if joined and joined[-1][2] == band and joined[-1][1] == a:
            joined[-1] = (joined[-1][0], b, band)
        else:
            joined.append((a, b, band))
    return [
        ShootingStretchOut(
            band=cast(Literal["broadband", "narrowband"], band),
            starts_at=a.isoformat(),
            ends_at=b.isoformat(),
            seconds=round(seconds_between(a, b)),
        )
        for a, b, band in joined
    ]


def sky_of(conn: sqlite3.Connection, home: Site, the_night: str) -> TonightOut | None:
    """The route's reply minus what it reads (site, weather, next phases); phase at midnight, not
    noon. `None` when the zone composes no midnight: the computation would raise."""
    # Midnight as `clock` composes it, the instant the Nights page uses too: otherwise two screens
    # would ask the same night at two different moments.
    midnight = midnight_of(the_night, home.timezone)
    if midnight is None:
        return None
    window_start, window_hours = night_window(the_night, home.timezone)
    moon_phase = moon.phase(midnight)
    moon_night = moon.night_track(window_start, home.latitude, home.longitude, hours=window_hours)
    bands = sun.night_bands(window_start, home.latitude, home.longitude, hours=window_hours)
    dark = [(b.starts_at, b.ends_at) for b in bands if b.kind == sun.Sky.DARK]
    rule = config.moon_rule(config.read(conn))
    word = moon_level(moon_phase.illumination_pct, rule)
    moonless_left = moon.moonless_dark_left_s(moon_night, dark, rule.floor_deg)
    spans = moon.dark_spans(moon_night, dark, rule.floor_deg)
    tracks = planets.night_tracks(window_start, home.latitude, home.longitude, hours=window_hours)
    span = sun.chart_window(bands)
    shooting = _shooting(spans, word)
    planets_out = [_planet(p, span) for p in tracks]
    dark_s = round(sum(seconds_between(a, b) for a, b in dark))
    return TonightOut(
        dark_returns=None if dark_s else sun.dark_returns(the_night, home.latitude, home.longitude),
        highest_planet=_highest_planet(planets_out),
        shooting=shooting,
        broadband_dark_s=sum(s.seconds for s in shooting if s.band == "broadband"),
        narrowband_dark_s=sum(s.seconds for s in shooting if s.band == "narrowband"),
        chart=ChartOut(
            starts_at=span.starts_at.isoformat(),
            ends_at=span.ends_at.isoformat(),
            dark_from=_iso(span.dark_from),
            dark_until=_iso(span.dark_until),
        )
        if span
        else None,
        planets=planets_out,
        night=the_night,
        site=None,
        # in UTC: added on the wall clock, a clock-change night would end an hour off
        night_ends_at=(window_start.astimezone(UTC) + timedelta(hours=window_hours)).isoformat(),
        sky_bands=[_sky_band(f) for f in bands],
        dark_s=dark_s,
        moonless_dark=[
            DarkStretchOut(starts_at=a.isoformat(), ends_at=b.isoformat())
            for a, b in spans.moonless
        ],
        moon_in_dark=_moon_in_dark(spans.moon_up, dark, word),
        moon=MoonOut(
            phase_key=cast(PhaseKey, moon_phase.phase_key),
            illumination_pct=moon_phase.illumination_pct,
            rise=_iso(moon_night.rise),
            set=_iso(moon_night.set),
            rise_compass=cast(
                Compass,
                moon.compass(moon.azimuth_deg(moon_night.rise, home.latitude, home.longitude)),
            )
            if moon_night.rise
            else None,
            age_days=round(moon.age_days(midnight)),
            distance_km=int(round(moon.distance_km(midnight), -2)),
            highest=_sky_point(moon_night.highest),
            highest_in_chart=_highest_in(moon_night.track, span),
            track=[
                MoonPointOut(
                    at=p.at.isoformat(), altitude_deg=p.altitude_deg, moonless_dark_left_s=s
                )
                for p, s in zip(moon_night.track, moonless_left, strict=True)
            ],
            ceiling_deg=moon.sky_ceiling(home.latitude),
            lit_side=moon.lit_side(moon_phase.phase_key, home.latitude),
        ),
    )


def _nights(site: Site, now: str) -> list[str]:
    """Tonight and the next: at the site's noon the next is already written."""
    tonight = night_date(now, site.timezone)
    if tonight is None:
        return []
    following = datetime.fromisoformat(tonight) + timedelta(days=1)
    return [tonight, following.date().isoformat()]


def _written(conn: sqlite3.Connection, site: Site) -> set[str]:
    return {
        r[0]
        for r in conn.execute(
            "SELECT night_date FROM tonight_sky WHERE site_id = ? AND latitude = ?"
            " AND longitude = ? AND timezone = ?",
            (site.id, site.latitude, site.longitude, site.timezone),
        )
    }


def step(conn: sqlite3.Connection, site: Site | None, now: str | None = None) -> bool:
    """Rewrites only when tonight or the next night is missing for where the site is now; True
    when it did. Without a site or a zone there is no sky to compute."""
    if site is None or not site.timezone:
        return False
    wanted = _nights(site, now or now_iso())
    if not wanted or set(wanted) <= _written(conn, site):
        return False
    rebuild(conn, site, now)
    return True


def follows(conn: sqlite3.Connection) -> None:
    """After the sites changed, outside their transaction: a sky that fails is logged and left to
    the round, it does not undo the saved site."""
    try:
        step(conn, home_site(conn))
    except Exception:
        log.exception("stanotte: il cielo non si e' riscritto dopo i siti")


def rebuild(conn: sqlite3.Connection, site: Site | None, now: str | None = None) -> None:
    """The same two nights again, at once: what the Moon rule judged moves with it. Only this
    site's rows stay, so a former home site leaves nothing behind."""
    if site is None or not site.timezone:
        conn.execute("DELETE FROM tonight_sky")
        return
    rows = []
    for night in _nights(site, now or now_iso()):
        sky = sky_of(conn, site, night)
        if sky is not None:
            row = (site.id, night, site.latitude, site.longitude, site.timezone)
            rows.append((*row, sky.model_dump_json()))
    replace_rows(conn, "tonight_sky", COLUMNS, rows)
