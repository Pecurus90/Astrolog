"""Time in the database's form, in one place: two forms would be two orders. `DATE-OBS` is UTC
(FITS standard, <https://fits.gsfc.nasa.gov/year2000.html>, 4.4), never fixed by `DATE-LOC`."""

import zoneinfo
from datetime import UTC, date, datetime, time, timedelta


def iso_z(instant: datetime) -> str:
    """UTC, to the millisecond, with the Z."""
    return instant.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_iso() -> str:
    return iso_z(datetime.now(UTC))


def parse_iso(instant_iso: object) -> datetime | None:
    if not instant_iso:
        return None
    try:
        return datetime.fromisoformat(str(instant_iso).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def elapsed_s(started_iso: object, ended_iso: object) -> float | None:
    """Seconds: a test read lasts three seconds, and zero minutes would say nothing happened.
    `None` for a run still open or an end before the start: a negative is worse than a blank."""
    start, end = parse_iso(started_iso), parse_iso(ended_iso)
    if start is None or end is None:
        return None
    seconds = (end - start).total_seconds()
    return seconds if seconds >= 0 else None


# The frame's night in SQL, for a `GROUP BY`: the column `scan` writes with `night_date` in the
# site's zone.
NIGHT_SQL = "f.local_night"


def night_date(instant_iso: object, tz_name: str | None = None) -> str | None:
    """Noon to noon in the given zone, because the same instant falls on two nights in Rome and in
    Arizona. Without a zone it is read in UTC, the only zone the file knows."""
    moment = _in_zone(instant_iso, tz_name)
    return None if moment is None else night_of(moment)


def night_of(moment: datetime) -> str:
    """`night_date` of an instant already in the site's zone, which cannot fail."""
    # Subtracting on an aware instant works on the wall clock, which is what is needed: local
    # noon, not UTC noon shifted.
    return (moment - timedelta(hours=12)).date().isoformat()


def night_instant(date_obs: str | None, mtime: float) -> str:
    """Without `DATE-OBS`, the instant the file was written."""
    return date_obs or datetime.fromtimestamp(mtime, UTC).isoformat()


def local_iso(instant_iso: object, tz_name: str | None = None) -> str | None:
    """ISO with its offset, in UTC without a zone: the page only cuts it, the writer picks the
    zone."""
    moment = _in_zone(instant_iso, tz_name or "UTC")
    return None if moment is None else moment.isoformat(timespec="seconds")


def _in_zone(instant_iso: object, tz_name: str | None) -> datetime | None:
    """Without an offset it is UTC, as the standard says of `DATE-OBS`."""
    moment = parse_iso(instant_iso)
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    if not tz_name:
        return moment
    try:
        return moment.astimezone(zoneinfo.ZoneInfo(tz_name))
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return None


def midnight_of(night_date_str: str, tz_name: str | None) -> datetime | None:
    """Midnight the day after the night's name, since the Moon moves through it; `None` without
    a zone, because UTC would be another place's sky."""
    if not tz_name:
        return None
    try:
        day = _day_of(night_date_str)
        zone = zoneinfo.ZoneInfo(tz_name)
    except (TypeError, ValueError, zoneinfo.ZoneInfoNotFoundError):
        return None
    # Where the clock changes at midnight (Santiago, Havana) that local hour does not exist:
    # `zoneinfo` resolves it with the earlier offset, an instant of that night all the same.
    return datetime.combine(day + timedelta(days=1), time(0), tzinfo=zone)


def _day_of(night_date_str: str) -> date:
    # DTZ007: a date, not an instant.
    return datetime.strptime(night_date_str, "%Y-%m-%d").date()  # noqa: DTZ007


# A night is looked at from noon of its day, in the site's zone.
_START_HOUR = 12


def night_window(night_date_str: str, tz_name: str | None) -> tuple[datetime, float]:
    """(start, true hours): a clock-change night lasts 23 or 25. The difference is taken in UTC,
    since subtracting two aware instants in a real zone gives wall-clock hours."""
    zone = zoneinfo.ZoneInfo(tz_name) if tz_name else UTC
    day = _day_of(night_date_str)
    starts = datetime.combine(day, time(_START_HOUR), tzinfo=zone)
    ends = datetime.combine(day + timedelta(days=1), time(_START_HOUR), tzinfo=zone)
    hours = (ends.astimezone(UTC) - starts.astimezone(UTC)).total_seconds() / 3600
    return starts, hours
