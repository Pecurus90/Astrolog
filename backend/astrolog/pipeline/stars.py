"""One frame measured on its pixels (ADR 0022, docs/domini/misure.md): sky, noise, stars on a
median-filtered copy, HFD and shape on the raw frame. Pure: pixels in, numbers out."""

import math
from dataclasses import dataclass
from functools import partial
from typing import Any

import numpy as np
import sep  # pyright: ignore[reportMissingImports] -- compiled module, no stubs

from ..units import sigma_from_mad
from . import transparency
from .background import banding, gradient, valid_pixels
from .cores import median, side_by_side, started
from .debayer import COLOURS, debayered
from .detect import Detections, detect
from .field import (
    Photometry,
    bright_side,
    elongation,
    fwhm_tilt,
    photometry,
    psf_signal_weight,
    psf_snr,
)
from .median import median3x3
from .mmt import Background, mstar_nstar
from .noise import NOISE_FLOOR_ADU, Mrs, mrs, structure_noise
from .pixel_stats import PixelStats, pixel_stats, snr
from .psf_fit import Fitted, fit_stars
from .psf_flux import ring_sky
from .shape import MIN_STARS, Shape, estimated_fwhm, shape_of
from .trails import trails

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
class Estimates:
    """Noise and PSF signal Image Analysis reads; a colour frame's from Debayer, per CFA channel
    off the raw data (ImageAnalysis par. 2.1.4-2.1.5). software-ok"""

    noise: Mrs  # PCL:Noise:Sigmas, Fractions
    found: Photometry | None  # PCL:Signal:PSFTotalFlux, PSFTotalMeanFlux, PSFCounts
    mmt: Background | None  # PCL:Noise:MStar, NStar
    scales: tuple[float, float]  # PCL:Noise:ScaleLow, ScaleHigh


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
    trails: int  # Trails (trails.py)
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
    ladder: dict[int, float]  # window start -> median log10 flux (transparency.py); absent: none


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
    # each CFA channel's own, as Debayer writes them; mono's M* beside the rest (cores.py). The
    # stars never wait for them: only the noise written does.
    channels = partial(mstar_nstar, raw)
    if pattern is not None:
        channels = partial(_by_channel, sensor, pattern, saturation)
    extra = started(channels)
    first, quiet, stats = side_by_side(
        lambda: _first_pass(raw, sensor, saturation), lambda: mrs(raw),
        lambda: pixel_stats(raw, full_scale=saturation, pedestal=pedestal))  # fmt: skip

    def written() -> float:
        # MRS, not the first pass: crowded fields lift a MAD (40k synthetic stars: 19.8 for 10)
        return max((quiet if pattern is None else extra().noise).sigma, NOISE_FLOOR_ADU)

    valid = valid_pixels(raw, saturation)
    (found, fits, crossed), sky_field = side_by_side(
        lambda: _stars(raw, (sensor, saturation), quiet, (first, valid)),
        lambda: _sky_field(raw, valid, written()))  # fmt: skip
    noise = written()
    chosen = _spread(first.objects, first.usable, raw.shape)
    shape, star_field, ladder, found_flux = side_by_side(
        lambda: shape_of(first.images, first.objects, chosen, first.noise, (fits, len(found.x))),
        lambda: _star_field(fits, raw.shape), lambda: _ladder(raw, found, fits),
        lambda: photometry(fits) if pattern is None else None)  # fmt: skip
    said = extra() if pattern is not None else Estimates(
        quiet, found_flux, extra(), (stats.scale_low_adu, stats.scale_high_adu))  # fmt: skip
    sky_field["trails"] = crossed
    across = Across(ceiling_adu=saturation, saturated=int(found.saturated.sum()),
                    gradient_angle_deg=bright_side(first.back), ladder=ladder,
                    **_flux(said, noise, len(found.x)), **_pixel_values(stats, said, noise),
                    **sky_field, **star_field)  # fmt: skip
    common = {"stars": len(found.x), "kept": len(first.hfds), "background_adu": first.level,
              "noise_adu": noise, "shape": shape} | vars(across)  # fmt: skip
    if len(first.hfds) < MIN_STARS:
        return TooFewStars(**common)
    return Measured(**common, hfd_px=float(np.median(first.hfds)))


@dataclass(frozen=True)
class _First:
    """sep's pass: sky, stars for the HFD and the shape; the structure map's noise."""

    back: np.ndarray  # sep's sky
    level: float  # its global level
    images: tuple[np.ndarray, np.ndarray]  # residual, its 3x3 median
    noise: float  # MAD of the residual
    objects: np.ndarray  # sep's detections
    usable: np.ndarray  # those fit to measure (_kept)
    hfds: np.ndarray  # px, round ones spread on the grid
    structure: float  # structure_noise of the median copy


def _first_pass(raw: np.ndarray, sensor: np.ndarray, saturation: float) -> _First:
    sky = sep.Background(raw)
    back = sky.back()
    residual = raw - back
    noise = max(_sigma(residual), NOISE_FLOOR_ADU)
    images = (residual, median3x3(residual))
    objects = _found(images[1], noise)
    usable = _kept(sensor, objects, saturation)
    round_ones = usable[_round(objects[usable])]
    hfds = _hfd(images, objects, _spread(objects, round_ones, raw.shape))
    structure = max(structure_noise(images[1]), NOISE_FLOOR_ADU)
    return _First(back, float(sky.globalback), images, noise, objects, usable, hfds, structure)


def _flux(said: Estimates, noise: float, stars: int) -> dict[str, Any]:
    """PSF SNR, PSFFlux, PSFTotalMeanFlux, PSFCount, PSFSignalWeight, MStar, NStar from the
    estimates; `stars` the measured plane's, MIN_STARS. software-ok"""
    found, mmt = said.found, said.mmt
    back = {"mstar_adu": mmt.mstar_adu if mmt else None,
            "nstar_adu": mmt.nstar_adu if mmt else None}  # fmt: skip
    if found is None:
        return back | dict.fromkeys(("psf_snr", "psf_flux_adu", "psf_mean_flux_adu", "psf_count",
                                     "psf_signal_weight"))  # fmt: skip
    enough = stars >= MIN_STARS
    weight = psf_signal_weight(found, noise, mmt.mstar_adu) if enough and mmt else None
    return back | {"psf_snr": psf_snr(found.flux, noise) if enough else None,
                   "psf_flux_adu": found.flux, "psf_mean_flux_adu": found.mean_flux,
                   "psf_count": found.count, "psf_signal_weight": weight}  # fmt: skip


def _ladder(raw: np.ndarray, found: Detections, fits: Fitted) -> dict[int, float]:
    """Each fitted star's aperture flux; saturated, its structure's highest pixel at
    SATURATED_SHARE of the plane's (ImageAnalysis par. 2.1.7). software-ok"""
    flux = np.full(len(found.x), np.nan)
    flux[fits.star.astype(int)] = fits.aperture_flux
    peaks = np.array([raw[y0:y1, x0:x1].max() for x0, x1, y0, y1 in found.box.astype(int)])
    top = float(np.nanmax(raw)) if raw.size else 0.0
    return transparency.brightness_ladder(flux, peaks >= transparency.SATURATED_SHARE * top)


def _stars(
    raw: np.ndarray, clip: tuple[np.ndarray, float], quiet: Mrs, on: tuple["_First", np.ndarray]
) -> tuple[Detections, Fitted, int]:
    """Image Analysis's stars on the MRS noise, fitted on the plane with its sky: the sampling
    region's median needs the level (psf_fit.py); Trails off them on `on`'s valid. software-ok"""
    first, valid = on
    noise = max(quiet.sigma, NOISE_FLOOR_ADU)
    found = detect(*first.images, (noise, first.structure), clip=clip, level=(raw, clip[1]))
    fits, crossed = side_by_side(lambda: fit_stars(raw, found.x, found.y, found.box, found.flux),
                                 lambda: trails(raw, valid, found))  # fmt: skip
    return found, fits, crossed


def _sky_field(raw: np.ndarray, valid: np.ndarray, noise: float) -> dict[str, Any]:
    """ImageAnalysis Gradient, RowBanding, ColumnBanding on the measured plane's `valid` pixels,
    in units of the noise written. software-ok"""
    bands, slope = side_by_side(lambda: banding(raw, valid, noise),
                                lambda: gradient(raw, valid, noise))  # fmt: skip
    return {"gradient_noise": slope,
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


def _pixel_values(stats: PixelStats, said: Estimates, noise: float) -> dict[str, Any]:
    """ImageAnalysis Median, Sigma, Entropy of the measured plane; NoiseRatio, SNR from the
    estimates. software-ok"""
    return {"median_adu": stats.median_adu, "sigma_adu": stats.sigma_adu,
            "entropy_bits": stats.entropy_bits, "noise_ratio": said.noise.ratio,
            "snr": snr(*said.scales, noise)}  # fmt: skip


def _sigma(residual: np.ndarray) -> float:
    return sigma_from_mad(median(np.abs(residual - median(residual))))


def _channels(data: np.ndarray, pattern: str) -> list[np.ndarray]:
    """R, G, B planes at half resolution, a channel's samples averaged per 2x2 quad (Debayer's
    channels: noise 1.000, flux 0.99-1.01 of its properties, sonde 26.56)."""
    rows, cols = data.shape[0] // 2 * 2, data.shape[1] // 2 * 2
    quads = data[:rows, :cols].reshape(rows // 2, 2, cols // 2, 2)
    colours = COLOURS[pattern]
    planes = []
    for channel in range(3):
        cells = [(r, c) for r in (0, 1) for c in (0, 1) if colours[r][c] == channel]
        mean = np.mean([quads[:, r, :, c] for r, c in cells], axis=0, dtype=np.float32)
        planes.append(np.ascontiguousarray(mean))
    return planes


def _estimates(plane: np.ndarray, saturation: float) -> Estimates:
    """One channel's plane as the mono chain measures it: MRS noise, stars fitted, M* N*, scales;
    M* N* and scales beside the stars."""
    aside = started(lambda: (mstar_nstar(plane), pixel_stats(plane, full_scale=saturation)))
    residual = plane - sep.Background(plane).back()
    filtered = median3x3(residual)
    quiet = mrs(plane)
    noise = max(quiet.sigma, NOISE_FLOOR_ADU)
    structure = max(structure_noise(filtered), NOISE_FLOOR_ADU)
    found = detect(residual, filtered, (noise, structure), clip=(plane, saturation),
                   level=(plane, saturation))  # fmt: skip
    fits = fit_stars(plane, found.x, found.y, found.box, found.flux)
    mmt, stats = aside()
    return Estimates(quiet, photometry(fits), mmt,
                     (stats.scale_low_adu, stats.scale_high_adu))  # fmt: skip


def _by_channel(sensor: np.ndarray, pattern: str, saturation: float) -> Estimates:
    """The three channels' estimates side by side, mid-ranged."""
    planes = _channels(sensor, pattern)
    return _mid_range(side_by_side(*(partial(_estimates, p, saturation) for p in planes)))


def _mid_range(channels: list[Estimates]) -> Estimates:
    """ImageAnalysis par. 2.1: each estimate (min + max) / 2 over the channels; a channel with no
    fit or no M*, none. PSFCount half up, as his (2079.5 -> 2080, sonde 26.56). software-ok"""

    def mid(values: list[float]) -> float:
        return (min(values) + max(values)) / 2

    found = [c.found for c in channels if c.found is not None]
    mmt = [c.mmt for c in channels if c.mmt is not None]
    psf = None
    if len(found) == len(channels):
        count = math.floor(mid([f.count for f in found]) + 0.5)
        psf = Photometry(mid([f.flux for f in found]), mid([f.mean_flux for f in found]), count)
    back = None
    if len(mmt) == len(channels):
        back = Background(mid([m.mstar_adu for m in mmt]), mid([m.nstar_adu for m in mmt]))
    noise = Mrs(mid([c.noise.sigma for c in channels]), mid([c.noise.ratio for c in channels]))
    scales = (mid([c.scales[0] for c in channels]), mid([c.scales[1] for c in channels]))
    return Estimates(noise, psf, back, scales)


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
