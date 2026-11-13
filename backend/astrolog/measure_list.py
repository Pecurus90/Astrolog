"""Every measure a frame has (misure.md): column, unit, group, why NULL. Under the pipeline that
writes them and the app that reads them, so neither imports the other (ADR 0030)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

# Brightness ladder (pipeline/transparency.py): windows of 50 ranks by decreasing flux, from these.
STARTS = (1, 51, 101, 201, 401, 801, 1601, 3201, 6401)  # [C ImageAnalysis par. 2.1.7; software-ok]


class Table(StrEnum):
    MEASURES = "pipeline_measures"
    SKY = "pipeline_sky"
    SQM = "pipeline_sqm"


class Unit(StrEnum):
    PX = "px"
    ARCSEC = "arcsec"
    ADU = "adu"
    ADU_PER_S = "adu_per_s"
    COUNT = "count"
    RATIO = "ratio"  # a pure number
    FRACTION = "fraction"  # 0 to 1
    NOISE = "noise"  # in units of the frame's noise
    PCT = "pct"
    DEG = "deg"
    HOURS = "hours"
    BITS = "bits"
    DEX = "dex"
    MAG = "mag"
    MAG_ARCSEC2 = "mag_arcsec2"


class Group(StrEnum):
    """The brief's groups (handoff/design-v59.md, 1.1), the tiles' among them."""

    STARS_SHAPE = "stars_shape"
    SIGNAL = "signal"
    BACKGROUND = "background"
    FIELD = "field"
    SKY = "sky"
    MOON_SUN = "moon_sun"
    BRIGHTNESS = "brightness"  # SQM and its calibration
    LADDER = "ladder"  # brightness ladder, for transparency over a series


class Silent(StrEnum):
    """Why a measure has no value: its stage's outcome, or the measure's own reason."""

    NOT_MEASURED_YET = "not_measured_yet"
    TOO_FEW_STARS = "too_few_stars"
    UNREADABLE = "unreadable"
    NOT_SUPPORTED = "not_supported"
    FZ_UNSUPPORTED = "fz_unsupported"
    SKY_PENDING = "sky_pending"
    NOT_SOLVED = "not_solved"
    NO_SITE_TIME_OR_CENTRE = "no_site_time_or_centre"
    NO_SITE_OR_TIME = "no_site_or_time"
    BELOW_HORIZON = "below_horizon"
    SQM_PENDING = "sqm_pending"
    SQM_NOT_THIS_FILTER = "sqm_not_this_filter"
    CALIBRATION_FAILED = "calibration_failed"
    NO_ALTITUDE = "no_altitude"
    NEEDS_CAMERA_BIAS = "needs_camera_bias"
    SKY_UNDER_BIAS = "sky_under_bias"
    NO_BIAS_DECLARED = "no_bias_declared"
    UNDER_5_STARS = "under_5_stars"
    NO_FIT = "no_fit"
    NOT_FITTED = "not_fitted"  # the shape estimated: no PSF residual
    UNDER_32_FITS = "under_32_fits"
    AN_AREA_WITHOUT_STARS = "an_area_without_stars"
    CENTRE_OR_RING_EMPTY = "centre_or_ring_empty"
    ROUND_STARS = "round_stars"
    FLAT_SKY = "flat_sky"
    NO_EXPOSURE = "no_exposure"
    NOISE_ZERO = "noise_zero"
    NO_PIXEL_UNDER_MODEL = "no_pixel_under_model"
    NO_PSF_SNR_OR_MSTAR = "no_psf_snr_or_mstar"
    UNDER_50_STARS = "under_50_stars"


@dataclass(frozen=True)
class Entry:
    key: str  # the column, and the name in the Selection's formula
    table: Table
    unit: Unit
    group: Group
    why: Silent | None  # NULL in a row its stage wrote whole; None: never NULL there
    solved_only: bool = False  # sky: only with a solution
    on_airmass: bool = False  # NULL also below the horizon


_M, _K, _Q = Table.MEASURES, Table.SKY, Table.SQM
_SHAPE, _SIG, _BG, _FIELD = Group.STARS_SHAPE, Group.SIGNAL, Group.BACKGROUND, Group.FIELD
_NONE = None  # written on every row its stage wrote whole

MEASURES: tuple[Entry, ...] = (
    Entry("stars", _M, Unit.COUNT, _SHAPE, _NONE),
    Entry("kept", _M, Unit.COUNT, _SHAPE, _NONE),
    Entry("saturated", _M, Unit.COUNT, _SHAPE, _NONE),
    Entry("hfd_px", _M, Unit.PX, _SHAPE, _NONE),
    Entry("hfd_arcsec", _K, Unit.ARCSEC, _SHAPE, Silent.NOT_SOLVED, solved_only=True),
    Entry(
        "hfd_zenith_arcsec",
        _K,
        Unit.ARCSEC,
        _SHAPE,
        Silent.NO_SITE_TIME_OR_CENTRE,
        solved_only=True,
        on_airmass=True,
    ),  # fmt: skip
    Entry("fwhm_px", _M, Unit.PX, _SHAPE, Silent.UNDER_5_STARS),
    Entry("fwhm_arcsec", _K, Unit.ARCSEC, _SHAPE, Silent.UNDER_5_STARS, solved_only=True),
    Entry(
        "fwhm_zenith_arcsec",
        _K,
        Unit.ARCSEC,
        _SHAPE,
        Silent.NO_SITE_TIME_OR_CENTRE,
        solved_only=True,
        on_airmass=True,
    ),  # fmt: skip
    Entry("eccentricity", _M, Unit.RATIO, _SHAPE, Silent.UNDER_5_STARS),
    Entry("angle_deg", _M, Unit.DEG, _SHAPE, Silent.ROUND_STARS),
    Entry("angle_pa_deg", _K, Unit.DEG, _SHAPE, Silent.ROUND_STARS, solved_only=True),
    Entry("shape_stars", _M, Unit.COUNT, _SHAPE, Silent.UNDER_5_STARS),
    Entry("fwhm_sigma_px", _M, Unit.PX, _SHAPE, Silent.UNDER_5_STARS),
    Entry("eccentricity_sigma", _M, Unit.RATIO, _SHAPE, Silent.UNDER_5_STARS),
    Entry("psf_residual", _M, Unit.RATIO, _SHAPE, Silent.NOT_FITTED),
    Entry("psf_residual_sigma", _M, Unit.RATIO, _SHAPE, Silent.NOT_FITTED),
    Entry("elongation_angle_deg", _M, Unit.DEG, _SHAPE, Silent.ROUND_STARS),
    Entry("elongation_coherence", _M, Unit.FRACTION, _SHAPE, Silent.ROUND_STARS),
    Entry("psf_snr", _M, Unit.RATIO, _SIG, Silent.NO_FIT),
    Entry("psf_signal_weight", _M, Unit.RATIO, _SIG, Silent.NO_PSF_SNR_OR_MSTAR),
    Entry("psf_flux_adu", _M, Unit.ADU, _SIG, Silent.NO_FIT),
    Entry("psf_mean_flux_adu", _M, Unit.ADU, _SIG, Silent.NO_FIT),
    Entry("psf_count", _M, Unit.COUNT, _SIG, Silent.NO_FIT),
    Entry("snr", _M, Unit.RATIO, _SIG, Silent.NOISE_ZERO),
    Entry("background_adu", _M, Unit.ADU, _BG, _NONE),
    Entry("noise_adu", _M, Unit.ADU, _BG, _NONE),
    Entry("ceiling_adu", _M, Unit.ADU, _BG, _NONE),
    Entry("median_adu", _M, Unit.ADU, _BG, _NONE),
    Entry("sky_rate_adu_s", _M, Unit.ADU_PER_S, _BG, Silent.NO_EXPOSURE),
    Entry("sigma_adu", _M, Unit.ADU, _BG, _NONE),
    Entry("entropy_bits", _M, Unit.BITS, _BG, _NONE),
    Entry("noise_ratio", _M, Unit.FRACTION, _BG, _NONE),
    Entry("mstar_adu", _M, Unit.ADU, _BG, Silent.NO_PIXEL_UNDER_MODEL),
    Entry("nstar_adu", _M, Unit.ADU, _BG, Silent.NO_PIXEL_UNDER_MODEL),
    Entry("row_banding", _M, Unit.NOISE, _BG, Silent.NOISE_ZERO),
    Entry("column_banding", _M, Unit.NOISE, _BG, Silent.NOISE_ZERO),
    Entry("gradient_noise", _M, Unit.NOISE, _FIELD, Silent.NOISE_ZERO),
    Entry("gradient_angle_deg", _M, Unit.DEG, _FIELD, Silent.FLAT_SKY),
    Entry("gradient_pa_deg", _K, Unit.DEG, _FIELD, Silent.FLAT_SKY, solved_only=True),
    Entry("trails", _M, Unit.COUNT, _FIELD, _NONE),
    Entry("hfd_tilt_pct", _M, Unit.PCT, _FIELD, Silent.AN_AREA_WITHOUT_STARS),
    *(
        Entry(f"hfd_{area}_px", _M, Unit.PX, _FIELD, Silent.AN_AREA_WITHOUT_STARS)
        for area in ("corner_1", "corner_2", "corner_3", "corner_4", "centre")
    ),
    Entry("off_axis_px", _M, Unit.PX, _FIELD, Silent.CENTRE_OR_RING_EMPTY),
    Entry(
        "off_axis_arcsec", _K, Unit.ARCSEC, _FIELD, Silent.CENTRE_OR_RING_EMPTY, solved_only=True
    ),  # fmt: skip
    Entry("fwhm_tilt", _M, Unit.RATIO, _FIELD, Silent.UNDER_32_FITS),
    Entry("fwhm_curvature", _M, Unit.RATIO, _FIELD, Silent.UNDER_32_FITS),
    Entry("altitude_deg", _K, Unit.DEG, Group.SKY, Silent.NO_SITE_TIME_OR_CENTRE),
    Entry("airmass", _K, Unit.RATIO, Group.SKY, Silent.NO_SITE_TIME_OR_CENTRE, on_airmass=True),
    Entry("azimuth_deg", _K, Unit.DEG, Group.SKY, Silent.NO_SITE_TIME_OR_CENTRE),
    Entry("hour_angle_h", _K, Unit.HOURS, Group.SKY, Silent.NO_SITE_TIME_OR_CENTRE),
    Entry("moon_altitude_deg", _K, Unit.DEG, Group.MOON_SUN, Silent.NO_SITE_OR_TIME),
    Entry("moon_separation_deg", _K, Unit.DEG, Group.MOON_SUN, Silent.NO_SITE_TIME_OR_CENTRE),
    Entry("moon_illumination", _K, Unit.FRACTION, Group.MOON_SUN, Silent.NO_SITE_OR_TIME),
    Entry("sun_altitude_deg", _K, Unit.DEG, Group.MOON_SUN, Silent.NO_SITE_OR_TIME),
    Entry("sqm", _Q, Unit.MAG_ARCSEC2, Group.BRIGHTNESS, Silent.SKY_UNDER_BIAS),
    Entry("zero_point_mag", _Q, Unit.MAG, Group.BRIGHTNESS, Silent.CALIBRATION_FAILED),
    Entry("calibration_stars", _Q, Unit.COUNT, Group.BRIGHTNESS, Silent.CALIBRATION_FAILED),
    Entry("sky_adu", _Q, Unit.ADU, Group.BRIGHTNESS, Silent.CALIBRATION_FAILED),
    Entry("bias_adu", _Q, Unit.ADU, Group.BRIGHTNESS, Silent.NO_BIAS_DECLARED),
    *(
        Entry(f"ladder_{start}_dex", _M, Unit.DEX, Group.LADDER, Silent.UNDER_50_STARS)
        for start in STARTS
    ),
)

# Where a frame's sky is brighter, clockwise from North (pipeline/sky_measure.sky_side).
SkySide = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
SIDES: tuple[SkySide, ...] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


# Columns that are no measure: keys, outcomes, words, times; the route sends the words apart.
NOT_MEASURES: dict[Table, frozenset[str]] = {
    _M: frozenset(
        {
            "frame_id",
            "file_id",
            "outcome",
            "shape",
            "tilt_level",
            "sampling_class",
            "duration_s",
            "measured_at",
        }
    ),  # fmt: skip
    _K: frozenset({"frame_id", "solved", "mid_utc", "angle_axis", "gradient_side", "computed_at"}),
    _Q: frozenset(
        {"frame_id", "file_id", "outcome", "catalogue", "colour", "duration_s", "computed_at"}
    ),  # fmt: skip
}
