"""The Moon of the Dashboard's detail and calendar: age, distance, the direction it rises from, the
main phases, and the dark hours without it. Checked on published instants, offline."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from astrolog.clock import night_date, night_window
from astrolog.ephemeris import moon

ROME = ZoneInfo("Europe/Rome")
CASA = (45.4906, 11.5222)
UTC = dt.UTC


def test_the_main_phases_fall_on_the_published_instants():
    """New Moon 2024-12-30 22:27 UTC, full Moon 2025-01-13 22:27 UTC, new Moon 2025-01-29 12:36 UTC
    (USNO, https://aa.usno.navy.mil/data/MoonPhases)."""
    events = moon.main_phases(
        dt.datetime(2024, 12, 25, tzinfo=UTC), dt.datetime(2025, 2, 1, tzinfo=UTC)
    )
    expected = [
        ("new", dt.datetime(2024, 12, 30, 22, 27, tzinfo=UTC)),
        ("full", dt.datetime(2025, 1, 13, 22, 27, tzinfo=UTC)),
        ("new", dt.datetime(2025, 1, 29, 12, 36, tzinfo=UTC)),
    ]
    assert [e.kind for e in events] == [k for k, _ in expected]
    for event, (_, at) in zip(events, expected, strict=True):
        assert abs(event.at - at) < dt.timedelta(minutes=20)


def test_the_age_counts_days_since_new_moon():
    assert moon.age_days(dt.datetime(2024, 12, 30, 22, 27, tzinfo=UTC)) == pytest.approx(0, abs=0.3)
    assert moon.age_days(dt.datetime(2025, 1, 13, 22, 27, tzinfo=UTC)) == pytest.approx(
        14.8, abs=0.6
    )


def test_the_distance_is_centre_to_centre_like_the_published_perigee():
    """Perigee of 2024-10-17, about 00:50 UTC: 357,175 km between the centres."""
    assert moon.distance_km(dt.datetime(2024, 10, 17, 0, 50, tzinfo=UTC)) == pytest.approx(
        357175, abs=300
    )


@pytest.mark.parametrize(
    ("azimuth", "point"),
    [
        (0, "N"),
        (11.2, "N"),
        (11.3, "NNE"),
        (67.5, "ENE"),
        (90, "E"),
        (191, "S"),
        (350, "N"),
        (292.5, "WNW"),
    ],
)
def test_sixteen_points_of_the_compass(azimuth, point):
    assert moon.compass(azimuth) == point


def test_the_moon_rises_in_the_east_and_the_direction_is_told():
    night = moon.night_track(*_window("2025-01-13"), *CASA)
    assert night.rise is not None
    assert moon.compass(moon.azimuth_deg(night.rise, *CASA)) in {"ENE", "NE", "E"}


def _window(date: str) -> tuple[dt.datetime, float]:
    start, hours = night_window(date, "Europe/Rome")
    return start, hours


@pytest.mark.parametrize(
    ("zone", "place"), [("Asia/Tokyo", (35.68, 139.69)), ("America/Los_Angeles", (34.05, -118.24))]
)
def test_the_calendar_names_the_night_of_the_site_not_of_utc(zone, place):
    """Il nome principale va alla notte del sito che contiene l'istante: lontano da UTC una notte
    misurata da mezzogiorno UTC sposta la piena o la nuova di un giorno."""
    dates = [(dt.date(2026, 1, 1) + dt.timedelta(days=g)).isoformat() for g in range(59)]
    nights = moon.calendar_nights([(d, *night_window(d, zone)) for d in dates], *place)
    start, _ = night_window(dates[0], zone)
    end, _ = night_window(dates[-1], zone)
    events = moon.main_phases(start, end + dt.timedelta(days=1))
    for kind in ("new", "full"):
        expected = {night_date(e.at.isoformat(), zone) for e in events if e.kind == kind}
        assert {n.night for n in nights if n.phase_key == kind} == expected, kind


def test_without_the_moon_the_whole_dark_is_moonless_and_with_the_full_moon_none():
    nights = moon.calendar_nights([(d, *_window(d)) for d in ("2024-12-30", "2025-01-13")], *CASA)
    new, full = nights
    assert new.night == "2024-12-30" and full.night == "2025-01-13"
    assert new.dark_s > 0
    assert abs(new.moonless_dark_s - new.dark_s) <= 15 * 60
    assert full.moonless_dark_s <= 15 * 60
    assert new.illumination_pct <= 1 and full.illumination_pct >= 99
