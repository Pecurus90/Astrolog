"""One frame measured on its pixels (ADR 0022, docs/domini/misure.md): sky, noise, stars on a
median-filtered copy, HFD and shape on the raw frame. Pure: pixels in, numbers out."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import sep  # pyright: ignore[reportMissingImports] -- compiled module, no stubs

from ..units import sigma_from_mad
from .background import banding, gradient, valid_pixels
from .debayer import COLOURS, debayered
from .detect import detect
from .field import bright_side, elongation, fwhm_tilt, photometry, psf_signal_weight, psf_snr
from .median import median3x3
from .mmt import Background, mstar_nstar
from .noise import NOISE_FLOOR_ADU, mrs, structure_noise
from .pixel_stats import pixel_stats, snr
from .psf_fit import Fitted, fit_stars
from .psf_flux import ring_sky
from .shape import MIN_STARS, Shape, estimated_fwhm, shape_of

THRESHOLD_SIGMA = 5.0  # [C Siril find_star default: 5 sigma over sky, software-ok]
NO_DEBLENDING = 1.0  # [C sep docs, extract: deblend_cont 1.0 disables deblending]
SATURATED_SHARE = 0.9  # [P ADR 0022: peak under 90% of saturation]
MIN_AXIS_RATIO = 0.5  # [C Siril find_star default roundness, software-ok]
ROOM_FWHM = 3.0  # [P plan 25.1: away from the edge and from neighbours more than 3 FWHM]
# Aperture radius in estimated FWHM: a Moffat beta 2.5 holds 99% of its flux there.
# [D Moffat 1969, enclosed flux 1-(1+r^2/a^2)^(1-b)]
APERTURE_FWHM = 3.0
RADII = 96  # [T] radii sampled per star; half flux interpolated between two
SUBPIX = 5  # [C sep docs: sum_circle default subpixel sampling]
# Stars spread over the field, not the brightest: a 3x3 grid, 60 a cell, across the flux ranking.
GRID = 3  # [P ADR 0022]
PER_CELL = 60  # [P ADR 0022]


@dataclass(frozen=True)
class Across:
    """What every frame with a sky has, stars or not (field.py)."""

    ceiling_adu: float  # DATAMAX, else the type's top (ADR 0041)
    saturated: int  # of `stars`, those with sensor pixels at the ceiling
    psf_snr: float | None  # None: under MIN_STARS stars, or no fit
    psf_flux_adu: float | None  # ImageAnalysis PSFFlux; None: no fit; software-ok
    psf_mean_flux_adu: float | None  # PSFTotalMeanFlux, ADU per square pixel
    psf_count: int | None  # PSFCount, the fits summed
    psf_signal_weight: float | None  # PSFSignalWeight; None: no PSF SNR or no M*
    gradient_angle_deg: float | None  # bright side, ours (field.bright_side); None: no plane
    gradient_noise: float | None  # ImageAnalysis Gradient, noise units; None: noise zero
    row_banding: float | None  # RowBanding, noise units
    column_banding: float | None  # ColumnBanding
    fwhm_tilt: float | None  # FWHMTilt; None: under 32 fits
    fwhm_curvature: float | None  # FWHMCurvature
    elongation_angle_deg: float | None  # ElongationAngle, counterclockwise; None: round or no fit
    elongation_coherence: float | None  # ElongationCoherence
    median_adu: float  # Image Analysis Median, the pedestal off (pixel_stats.py)
    sigma_adu: float  # Sigma
    entropy_bits: float  # Entropy
    noise_ratio: float  # NoiseRatio: share of pixels the MRS noise took
    snr: float | None  # SNR; None: noise zero
    mstar_adu: float | None  # MStar (mmt.py); None: no pixel under the model
    nstar_adu: float | None  # NStar


@dataclass(frozen=True)
class Measured(Across):
    stars: int  # as Image Analysis counts them (detect.py); software-ok
    kept: int  # stars the HFD is the median of
    hfd_px: float  # sensor pixels
    background_adu: float
    noise_adu: float
    shape: Shape | None  # on stars of any roundness: a trailed frame still has one


@dataclass(frozen=True)
class TooFewStars(Across):
    stars: int
    kept: int
    background_adu: float
    noise_adu: float
    shape: Shape | None


def measure_frame(
    data: np.ndarray, *, saturation: float, pattern: str | None, pedestal: float = 0.0
) -> Measured | TooFewStars:
    """`pattern`: Bayer matrix, VNG intensity as WBPP; None mono. `saturation`: full scale, the
    ceiling (ADR 0041), debayer clips there. `pedestal`: DN, off the median only (eq. 8)."""
    sensor = np.ascontiguousarray(data, dtype=np.float32)  # a clipped sensor pixel, colour too
    raw = sensor if pattern is None else debayered(sensor, pattern, top=saturation)
    sky = sep.Background(raw)
    back = sky.back()
    residual = raw - back
    noise = max(_sigma(residual), NOISE_FLOOR_ADU)
    images = (residual, median3x3(residual))
    objects = _found(images[1], noise)
    usable = _kept(sensor, objects, saturation)
    round_ones = usable[_round(objects[usable])]
    hfds = _hfd(images, objects, _spread(objects, round_ones, raw.shape))
    first_noise = noise
    # MRS, not the first pass: crowded fields lift a MAD (40k synthetic stars: 19.8 for 10)
    quiet = mrs(raw)
    noise = max(quiet.sigma, NOISE_FLOOR_ADU)
    structure = max(structure_noise(images[1]), NOISE_FLOOR_ADU)
    found = detect(*images, (noise, structure), clip=(sensor, saturation), level=(raw, saturation))
    # Fitted on the plane with its sky: the sampling region's median needs the level (psf_fit.py)
    fits = fit_stars(raw, found.x, found.y, found.box, found.flux)
    chosen = _spread(objects, usable, raw.shape)
    shape = shape_of(images, objects, chosen, first_noise, (fits, len(found.x)))
    mmt = mstar_nstar(raw)
    flux = _flux(fits, noise, len(found.x), mmt)
    pixel = _pixel_values(raw, saturation, pedestal, noise, quiet.ratio)
    if pattern is not None:  # noise said as WBPP says it
        noise = max(_mosaic_noise(sensor, pattern), NOISE_FLOOR_ADU)
    field = _sky_field(raw, saturation, noise) | _star_field(fits, raw.shape)
    across = Across(ceiling_adu=saturation, saturated=int(found.saturated.sum()),
                    gradient_angle_deg=bright_side(back), mstar_adu=mmt.mstar_adu if mmt else None,
                    nstar_adu=mmt.nstar_adu if mmt else None, **flux, **pixel, **field)  # fmt: skip
    common = {"stars": len(found.x), "kept": len(hfds), "background_adu": float(sky.globalback),
              "noise_adu": noise, "shape": shape} | vars(across)  # fmt: skip
    if len(hfds) < MIN_STARS:
        return TooFewStars(**common)
    return Measured(**common, hfd_px=float(np.median(hfds)))


def _flux(fits: Fitted, noise: float, stars: int, mmt: Background | None) -> dict[str, Any]:
    """PSF SNR, PSFFlux, PSFTotalMeanFlux, PSFCount, PSFSignalWeight; on the measured plane's own
    noise: a colour frame's intensity, as misure.md says. software-ok"""
    found = photometry(fits)
    if found is None:
        return dict.fromkeys(("psf_snr", "psf_flux_adu", "psf_mean_flux_adu", "psf_count",
                              "psf_signal_weight"))  # fmt: skip
    enough = stars >= MIN_STARS
    weight = psf_signal_weight(found, noise, mmt.mstar_adu) if enough and mmt else None
    return {"psf_snr": psf_snr(found.flux, noise) if enough else None, "psf_flux_adu": found.flux,
            "psf_mean_flux_adu": found.mean_flux, "psf_count": found.count,
            "psf_signal_weight": weight}  # fmt: skip


def _sky_field(raw: np.ndarray, ceiling: float, noise: float) -> dict[str, Any]:
    """ImageAnalysis Gradient, RowBanding, ColumnBanding on the measured plane's valid pixels, in
    units of the noise written. software-ok"""
    valid = valid_pixels(raw, ceiling)
    bands = banding(raw, valid, noise)
    return {"gradient_noise": gradient(raw, valid, noise),
            "row_banding": bands.row if bands else None,
            "column_banding": bands.column if bands else None}  # fmt: skip


def _star_field(fits: Fitted, shape: tuple[int, ...]) -> dict[str, Any]:
    """FWHMTilt, FWHMCurvature, ElongationAngle, ElongationCoherence on the shape's fits."""
    shaped = fits.brightest()
    tilt, along = fwhm_tilt(shaped, shape), elongation(shaped)
    return {"fwhm_tilt": tilt.tilt if tilt else None,
            "fwhm_curvature": tilt.curvature if tilt else None,
            "elongation_angle_deg": along.angle_deg if along else None,
            "elongation_coherence": along.coherence if along else None}  # fmt: skip


def _pixel_values(
    raw: np.ndarray, ceiling: float, pedestal: float, noise: float, ratio: float
) -> dict[str, Any]:
    """ImageAnalysis Median, Sigma, Entropy, NoiseRatio, SNR: the measured plane, its MRS noise."""
    stats = pixel_stats(raw, full_scale=ceiling, pedestal=pedestal)
    return {"median_adu": stats.median_adu, "sigma_adu": stats.sigma_adu,
            "entropy_bits": stats.entropy_bits, "noise_ratio": ratio,
            "snr": snr(stats.scale_low_adu, stats.scale_high_adu, noise)}  # fmt: skip


def _sigma(residual: np.ndarray) -> float:
    return sigma_from_mad(float(np.median(np.abs(residual - np.median(residual)))))


def _mosaic_noise(data: np.ndarray, pattern: str) -> float:
    """MRS noise of each colour plane, a channel's samples averaged per 2x2 quad; then
    (min + max) / 2, the plane SubframeSelector measures (sonde 26.48, pi_plane)."""
    rows, cols = data.shape[0] // 2 * 2, data.shape[1] // 2 * 2
    quads = data[:rows, :cols].reshape(rows // 2, 2, cols // 2, 2)
    colours = COLOURS[pattern]
    sigmas = []
    for channel in range(3):
        cells = [(r, c) for r in (0, 1) for c in (0, 1) if colours[r][c] == channel]
        sigmas.append(mrs(np.mean([quads[:, r, :, c] for r, c in cells], axis=0)).sigma)
    return (min(sigmas) + max(sigmas)) / 2


def _found(filtered: np.ndarray, noise: float) -> np.ndarray:
    """Detections on the filtered copy: hot pixels gone, stars kept (ADR 0022, point 8). No
    deblending: it hands contested pixels out at random, and the same frame measured otherwise."""
    sep.set_extract_pixstack(max(300_000, filtered.size))  # dense fields fill sep's default
    data = np.ascontiguousarray(filtered)
    return sep.extract(data, THRESHOLD_SIGMA, err=noise, deblend_cont=NO_DEBLENDING)


def _kept(raw: np.ndarray, objects: np.ndarray, saturation: float) -> np.ndarray:
    """Indices of stars fit to measure: whole, unsaturated, alone, off the edge."""
    if len(objects) == 0:
        return np.array([], dtype=int)
    x, y, guess = objects["x"], objects["y"], estimated_fwhm(objects)
    room = ROOM_FWHM * guess
    rows, cols = raw.shape
    inside = (x > room) & (y > room) & (x < cols - 1 - room) & (y < rows - 1 - room)
    ok = (objects["flag"] == 0) & inside
    ok &= _peaks(raw, objects, guess) < SATURATED_SHARE * saturation
    candidates = np.flatnonzero(ok)
    return candidates[_alone(x, y, room, candidates)]


def _round(objects: np.ndarray) -> np.ndarray:
    """Round enough for the HFD; the shape takes them all, else a trailed frame has none."""
    return objects["b"] / np.maximum(objects["a"], 1e-9) > MIN_AXIS_RATIO


def _alone(x: np.ndarray, y: np.ndarray, room: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """No other detection within `room` of each candidate. Neighbours from a strip sorted on x:
    memory linear in the detections, not a table of every pair (dense fields hold 20k+)."""
    order = np.argsort(x)
    xs = x[order]
    low = np.searchsorted(xs, x[candidates] - room[candidates], side="left")
    high = np.searchsorted(xs, x[candidates] + room[candidates], side="right")
    alone = np.ones(len(candidates), dtype=bool)
    for k, (i, start, stop) in enumerate(zip(candidates, low, high, strict=True)):
        near = order[start:stop]
        near = near[near != i]
        alone[k] = bool(np.all(np.hypot(x[near] - x[i], y[near] - y[i]) > room[i]))
    return alone


def _spread(objects: np.ndarray, keep: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    """At most PER_CELL kept stars per grid cell, evenly along the cell's flux ranking."""
    rows, cols = shape
    cell = np.minimum(objects["y"][keep] * GRID // rows, GRID - 1) * GRID + np.minimum(
        objects["x"][keep] * GRID // cols, GRID - 1
    )
    chosen = []
    for number in range(GRID * GRID):
        here = keep[cell == number]
        ranked = here[np.argsort(objects["flux"][here])]
        if len(ranked) > PER_CELL:
            ranked = ranked[np.linspace(0, len(ranked) - 1, PER_CELL).round().astype(int)]
        chosen.append(ranked)
    return np.sort(np.concatenate(chosen)) if chosen else keep


def _peaks(raw: np.ndarray, objects: np.ndarray, guess: np.ndarray) -> np.ndarray:
    """Highest raw pixel near each centre: a clipped core stays flat at the ceiling."""
    peaks = np.empty(len(objects))
    rows, cols = raw.shape
    for i, (x, y, size) in enumerate(zip(objects["x"], objects["y"], guess, strict=True)):
        r = max(1, int(np.ceil(size)))
        y0, x0 = int(round(y)), int(round(x))
        peaks[i] = raw[
            max(0, y0 - r) : min(rows, y0 + r + 1), max(0, x0 - r) : min(cols, x0 + r + 1)
        ].max()
    return peaks


def _hfd(
    images: tuple[np.ndarray, np.ndarray], objects: np.ndarray, keep: np.ndarray
) -> np.ndarray:
    """HFD on the raw residual less the ring median on the filtered copy. No segment mask: a
    masked nebula empties the ring (Rosette)."""
    if len(keep) == 0:
        return np.array([])
    residual, filtered = images
    x, y = objects["x"][keep], objects["y"][keep]
    aperture = APERTURE_FWHM * estimated_fwhm(objects)[keep]
    sky = ring_sky(filtered, (x, y), aperture)
    steps = np.linspace(1 / RADII, 1.0, RADII)
    enclosed = np.empty((RADII, len(keep)))
    for i, share in enumerate(steps):
        radius = aperture * share
        flux, _, _ = sep.sum_circle(residual, x, y, radius, subpix=SUBPIX)
        enclosed[i] = flux - sky * np.pi * radius**2
    total = enclosed[-1]
    good = total > 0
    radii = np.empty(len(keep))
    for j in np.flatnonzero(good):
        radii[j] = (
            np.interp(total[j] / 2, np.maximum.accumulate(enclosed[:, j]), steps) * aperture[j]
        )
    return 2 * radii[good]
