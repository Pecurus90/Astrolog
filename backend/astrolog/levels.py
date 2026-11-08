"""A measure's word, the weather's and a frame's alike (glossario.md, `level`): one home under the
weather and the pipeline, which do not know each other."""

from enum import StrEnum


class Verdict(StrEnum):
    GO = "go"
    MARGINAL = "marginal"
    NOGO = "nogo"


TILT_GOOD_PCT = 10.0  # [C ASTAP manual: "equal or less than 10% ... good"; software-ok]
TILT_PROBLEM_PCT = 20.0  # [C ASTAP manual: "equal or more than 20% ... tilt problem"; software-ok]
# FWHM in pixels: under 1.5 badly undersampled, 2-3 ideal, past 3 oversampled
SEVERE_UNDER_PX = 1.5  # [C Howell et al. 1996, PASP 108:1074]
IDEAL_LOW_PX = 2.0  # [C AAVSO CCD Photometry Guide; Diffraction Limited]
IDEAL_HIGH_PX = 3.0  # [C AAVSO CCD Photometry Guide; Diffraction Limited]


class SamplingClass(StrEnum):
    SEVERE_UNDER = "severe_under"
    UNDER = "under"
    IDEAL = "ideal"
    OVER = "over"


def tilt_level(tilt_pct: float) -> Verdict:
    """ADR 0044: a frame's tilt, or a night's median of it."""
    if tilt_pct <= TILT_GOOD_PCT:
        return Verdict.GO
    return Verdict.MARGINAL if tilt_pct < TILT_PROBLEM_PCT else Verdict.NOGO


def sampling_class(fwhm_px: float | None) -> SamplingClass | None:
    """ADR 0022: a frame's FWHM in px, or a night's median of it."""
    if fwhm_px is None:
        return None
    if fwhm_px < SEVERE_UNDER_PX:
        return SamplingClass.SEVERE_UNDER
    if fwhm_px < IDEAL_LOW_PX:
        return SamplingClass.UNDER
    return SamplingClass.IDEAL if fwhm_px <= IDEAL_HIGH_PX else SamplingClass.OVER
