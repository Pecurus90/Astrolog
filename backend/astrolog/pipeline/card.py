"""File card: facts read from one header alone, pure (mappa, passo 4). One function per fact."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from .fingerprint import frame_size
from .scanner import Program, Value
from .sky import PointingSource, pointing
from .values import as_celsius, as_count, as_name, as_number, as_percent, as_positive

# DATE-OBS as both programs write it: start of exposure, UTC, no zone (FITS 4.0 sec. 9.1.1).
# fromisoformat alone takes date only (midnight), week dates, compact forms.
_DATE_OBS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?")


class FrameType(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    FLAT = "flat"
    BIAS = "bias"
    SNAPSHOT = "snapshot"  # N.I.N.A. test shot: never in hours
    UNKNOWN = "unknown"  # missing, other word, or IMAGETYP and OBJECT disagree: asked later


# What N.I.N.A. and ASIAIR write, casefolded. DARKFLAT: N.I.N.A. < 3.0, "really just DARKs".
_WRITTEN = {
    "light": FrameType.LIGHT,
    "dark": FrameType.DARK,
    "flat": FrameType.FLAT,
    "bias": FrameType.BIAS,
    "darkflat": FrameType.DARK,
}
_SNAPSHOT_NAME = "snapshot"  # N.I.N.A. default target of a snapshot (AnchorableSnapshotVM.cs)
# N.I.N.A. default names, fixed not translated: SimpleSequenceVM.cs, FlatWizardVM.cs. No object.
_PLACEHOLDERS = frozenset({_SNAPSHOT_NAME, "target", "flatwizard"})


def _word(value: Value | None) -> str | None:
    return value.strip().casefold() if isinstance(value, str) else None


def frame_type(program: Program, values: dict[str, Value]) -> FrameType:
    """N.I.N.A. writes SNAPSHOT as LIGHT (CFitsioFITS.cs): known by its default name only."""
    kind = _WRITTEN.get(_word(values.get("IMAGETYP")) or "", FrameType.UNKNOWN)
    if kind is not FrameType.LIGHT:
        return kind
    name = _word(values.get("OBJECT"))
    if program is Program.NINA and name == _SNAPSHOT_NAME:
        return FrameType.SNAPSHOT
    calibration = _WRITTEN.get(name or "", FrameType.LIGHT) is not FrameType.LIGHT
    return FrameType.UNKNOWN if calibration else kind


def start_utc(values: dict[str, Value]) -> datetime | None:
    """No fallback (MJD-OBS, DATE-AVG, file time): no file lacks DATE-OBS. Past 6 decimals cut."""
    written = _strict_time(values.get("DATE-OBS"))
    return written.replace(tzinfo=UTC) if written else None


def _strict_time(written: Value | None) -> datetime | None:
    """Both programs' form, no zone; else None."""
    if not isinstance(written, str) or not _DATE_OBS.fullmatch(written):
        return None
    try:
        return datetime.fromisoformat(written)
    except ValueError:  # impossible date or time
        return None


def clock_offset_min(values: dict[str, Value]) -> int | None:
    """DATE-LOC minus DATE-OBS: PC clock zone (CFitsioFITS.cs ToLocalTime), not site's.
    Zones are whole quarters, -12 h to +14 h: else not same instant."""
    local, utc = _strict_time(values.get("DATE-LOC")), _strict_time(values.get("DATE-OBS"))
    if local is None or utc is None:
        return None
    seconds = (local - utc).total_seconds()
    if seconds % 900 or not -720 <= seconds / 60 <= 840:  # noqa: PLR2004
        return None
    return int(seconds // 60)


def site(values: dict[str, Value]) -> tuple[float, float] | None:
    """SITELAT/SITELONG degrees, East positive (archive). 0/0: N.I.N.A. factory profile
    (AstrometrySettings.cs), only sea there. Longitude 180 is -180."""
    lat, lon = as_number(values.get("SITELAT")), as_number(values.get("SITELONG"))
    if lat is None or lon is None or abs(lat) > 90 or abs(lon) > 180 or lat == lon == 0:  # noqa: PLR2004
        return None
    return lat, -180.0 if lon == 180 else lon  # noqa: PLR2004


def exposure_s(values: dict[str, Value]) -> float | None:
    """EXPTIME only: EXPOSURE always equal."""
    return as_number(values.get("EXPTIME"), at_least=0)


def camera(values: dict[str, Value]) -> str | None:
    """INSTRUME as written. CAMERAID no: USB path, changes with port."""
    return as_name(values.get("INSTRUME"))


def optics(program: Program, values: dict[str, Value]) -> str | None:
    """TELESCOP as written (SBIG). ASIAIR writes mount there: not known."""
    return None if program is Program.ASIAIR else as_name(values.get("TELESCOP"))


def object_name(program: Program, values: dict[str, Value]) -> str | None:
    """OBJECT as written, every frame type. Mosaic panel kept whole: grouped by sky later."""
    name = as_name(values.get("OBJECT"))
    if program is Program.NINA and _word(name) in _PLACEHOLDERS:
        return None
    return name


def mount(program: Program, values: dict[str, Value]) -> str | None:
    """ASIAIR writes mount in TELESCOP; N.I.N.A. never names it."""
    return as_name(values.get("TELESCOP")) if program is Program.ASIAIR else None


def focuser_position(values: dict[str, Value]) -> int | None:
    """[step]; N.I.N.A. writes FOCPOS and FOCUSPOS equal, ASIAIR FOCUSPOS only."""
    position = values.get("FOCPOS", values.get("FOCUSPOS"))
    return as_count(position, 0)


def focuser_temp_c(values: dict[str, Value]) -> float | None:
    return as_celsius(values.get("FOCTEMP", values.get("FOCUSTEM")))


def focal_mm(values: dict[str, Value]) -> float | None:
    """Hint on both: N.I.N.A. from profile, ASIAIR from its solve (varies by 1-3 mm)."""
    return as_positive(values.get("FOCALLEN"))


def pixel_um(values: dict[str, Value]) -> float | None:
    """XPIXSZ as written, binning included: physical pixel is XPIXSZ / XBINNING."""
    return as_positive(values.get("XPIXSZ"))


def bayer(program: Program, values: dict[str, Value]) -> bool | None:
    """Raw frame is Bayer mosaic. N.I.N.A. omits BAYERPAT only for mono or pattern None
    (CFitsioFITS.cs); ASIAIR without it: no case, not known."""
    if "BAYERPAT" not in values:
        return False if program is Program.NINA else None
    written = values["BAYERPAT"]
    return True if isinstance(written, str) and written.strip() else None


def iso(values: dict[str, Value]) -> int | None:
    """ASIAIR with DSLR writes ISO as string: '800'."""
    written = values.get("ISO")
    if isinstance(written, str):
        digits = written.strip()
        written = int(digits) if digits.isascii() and digits.isdigit() else None
    return as_count(written, 1)


@dataclass(frozen=True, slots=True)
class Card:
    """Fields named and ordered as pipeline_cards columns. None: not known."""

    frame_type: FrameType
    start_utc: datetime | None
    exposure_s: float | None
    camera: str | None
    width: int | None  # frame, after binning and crop
    height: int | None
    bin_x: int | None
    bin_y: int | None
    pixel_um: float | None  # with binning (SBIG; CFitsioFITS.cs; ASIAIR "with binning")
    bayer: bool | None
    gain: int | None
    iso: int | None
    offset: int | None
    ccd_temp_c: float | None
    set_temp_c: float | None
    optics: str | None
    focal_mm: float | None
    filter: str | None  # as written; what it is: filters.resolve
    pointing_ra_deg: float | None  # J2000, every frame type: user filters by type
    pointing_dec_deg: float | None
    pointing_source: PointingSource | None
    object_name: str | None  # hint: sky and catalogue confirm
    site_lat_deg: float | None
    site_lon_deg: float | None
    clock_offset_min: int | None
    filter_wheel: str | None
    focuser: str | None
    guide_camera: str | None
    mount: str | None
    focuser_position: int | None  # with focuser_temp_c: focus metric with measure
    focuser_temp_c: float | None


@dataclass(frozen=True, slots=True)
class Conditions:
    """N.I.N.A. weather source at capture; units CFitsioFITS.cs. Named as pipeline_conditions."""

    ambient_temp_c: float | None
    humidity_pct: float | None
    dew_point_c: float | None
    pressure_hpa: float | None
    cloud_cover_pct: float | None
    wind_kmh: float | None  # N.I.N.A. writes m/s * 3.6
    wind_gust_kmh: float | None
    wind_dir_deg: float | None  # from North, clockwise; 0 also when no wind (ASCOM)
    sky_quality_mpsas: float | None
    sky_temp_c: float | None
    sky_brightness_lux: float | None
    star_fwhm_arcsec: float | None


def _wind_direction(written: Value | None) -> float | None:
    number = as_number(written, at_least=0)
    if number is None or number > 360:  # noqa: PLR2004
        return None
    return number % 360


def read_conditions(values: dict[str, Value]) -> Conditions | None:
    """None when header writes none: most files."""
    conditions = Conditions(
        ambient_temp_c=as_celsius(values.get("AMBTEMP")),
        humidity_pct=as_percent(values.get("HUMIDITY")),
        dew_point_c=as_celsius(values.get("DEWPOINT")),
        pressure_hpa=as_positive(values.get("PRESSURE")),
        cloud_cover_pct=as_percent(values.get("CLOUDCVR")),
        wind_kmh=as_number(values.get("WINDSPD"), at_least=0),
        wind_gust_kmh=as_number(values.get("WINDGUST"), at_least=0),
        wind_dir_deg=_wind_direction(values.get("WINDDIR")),
        sky_quality_mpsas=as_number(values.get("MPSAS")),
        sky_temp_c=as_celsius(values.get("SKYTEMP")),
        sky_brightness_lux=as_number(values.get("SKYBRGHT"), at_least=0),
        star_fwhm_arcsec=as_positive(values.get("STARFWHM")),
    )
    return None if all(getattr(conditions, f) is None for f in conditions.__slots__) else conditions


def read_card(program: Program, values: dict[str, Value]) -> Card:
    width, height = frame_size(values)
    start = start_utc(values)
    ra, dec, source = pointing(program, values, start) or (None, None, None)
    lat, lon = site(values) or (None, None)
    return Card(
        frame_type=frame_type(program, values),
        start_utc=start,
        exposure_s=exposure_s(values),
        camera=camera(values),
        width=as_count(width, 1),
        height=as_count(height, 1),
        bin_x=as_count(values.get("XBINNING"), 1),
        bin_y=as_count(values.get("YBINNING"), 1),
        pixel_um=pixel_um(values),
        bayer=bayer(program, values),
        gain=as_count(values.get("GAIN"), 0),
        iso=iso(values),
        offset=as_count(values.get("OFFSET"), 0),
        ccd_temp_c=as_celsius(values.get("CCD-TEMP")),
        set_temp_c=as_celsius(values.get("SET-TEMP")),
        optics=optics(program, values),
        focal_mm=focal_mm(values),
        filter=as_name(values.get("FILTER")),
        pointing_ra_deg=ra,
        pointing_dec_deg=dec,
        pointing_source=source,
        object_name=object_name(program, values),
        site_lat_deg=lat,
        site_lon_deg=lon,
        clock_offset_min=clock_offset_min(values),
        filter_wheel=as_name(values.get("FWHEEL")),
        focuser=as_name(values.get("FOCNAME")),
        guide_camera=as_name(values.get("GUIDECAM")),
        mount=mount(program, values),
        focuser_position=focuser_position(values),
        focuser_temp_c=focuser_temp_c(values),
    )
