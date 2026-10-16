"""The planets of the night chart: their altitude through the night, offline, from the builtin
ephemeris. Checked on facts one can look up, not only on shape."""

import datetime as dt
from zoneinfo import ZoneInfo

from astrolog.ephemeris import TRACK_STEP_MIN, planets

ROME = ZoneInfo("Europe/Rome")
CASA = (45.4906, 11.5222)
# December 2024: Jupiter near opposition, declination about +21.
NOON = dt.datetime(2024, 12, 15, 12, 0, tzinfo=ROME)


def test_the_four_planets_of_the_chart_in_their_order():
    tracks = planets.night_tracks(NOON, *CASA, hours=24)
    assert [p.key for p in tracks] == ["saturn", "jupiter", "mars", "venus"]


def test_jupiter_near_opposition_culminates_high_in_the_night():
    """Declination +21 from latitude 45.5 culminates near 66 degrees, around local midnight."""
    jupiter = next(p for p in planets.night_tracks(NOON, *CASA, hours=24) if p.key == "jupiter")
    top = max(jupiter.track, key=lambda p: p.altitude_deg)
    assert 60 <= top.altitude_deg <= 72
    assert top.at.astimezone(ROME).hour in (23, 0, 1)


def test_venus_in_december_2024_is_an_evening_planet():
    """Venus was at greatest eastern elongation in January 2025: up after sunset, down by night."""
    venus = next(p for p in planets.night_tracks(NOON, *CASA, hours=24) if p.key == "venus")
    at = {p.at.astimezone(ROME).strftime("%H:%M"): p.altitude_deg for p in venus.track}
    assert at["17:00"] > 15
    assert at["23:00"] < 0


def test_a_track_is_drawn_every_track_step_in_the_site_zone():
    saturn = planets.night_tracks(NOON, *CASA, hours=24)[0]
    assert len(saturn.track) == 24 * 60 // TRACK_STEP_MIN + 1
    assert saturn.track[1].at - saturn.track[0].at == dt.timedelta(minutes=TRACK_STEP_MIN)
    assert saturn.track[0].at.tzinfo == ROME
