# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of
# the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Sky brightness of a light, mag/arcsec^2, by ASTAP's method (ADR 0022 point 8); ported from
ASTAP unit_sqm.pas, unit_annotation.pas, astap_main.pas, (c) Han Kleijn, MPL-2.0. Pure."""

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..units import sigma_from_mad
from .star_catalogue import MAX_FIELD_DEG, find_areas, read_area, window

# Flux calibration for extended objects: whole star flux inside a 14 px annulus.
ANNULUS_RADIUS = 14  # [C ASTAP unit_sqm.pas calculate_sqm: annulus_radius:=14]
SIGNAL_SIGMA = 3.0  # [C ASTAP HFD: val>3.0*sd_bg is signal]
STAR_FLOOR_SIGMA = 12.0  # [C ASTAP HFD: sumval<=12*sd_bg, no star]
BOXED_SHARE = 2 / 9  # [C ASTAP HFD: 2 of the 9 pixels of the box lit]
DROP_OFF = 0.1  # [C ASTAP HFD: distance_histogram<=0.1*distance_top_value]
DISK_SHARE = 0.35  # [C ASTAP HFD: illuminated_pixels<0.35*sqr(r+r-2), not a disk]
MIN_HFD, MAX_HFD = 0.8, 15.0  # [C ASTAP plot_and_measure_stars: hfd1<15 and hfd1>=0.8]
MIN_SNR = 30.0  # [C ASTAP plot_and_measure_stars: snr>30, "found emperical"]
# Stars tried: 730 on a 2328 x 1760 frame, the brightest; fainter ones add noise.
STARS_PER_PIXEL = 730 / (2328 * 1760)  # [C ASTAP plot_and_measure_stars]
OUTSIDE_PX = 50  # [C ASTAP plot_star: x>-50 and x<=width+50, counted toward the quota]
SATURATION_MARGIN = 1001.0  # [C ASTAP plot_star: pixel<data_max-1000, data_max=datamax_org-1]
OUTLIER_SIGMA = 1.5  # [C ASTAP get_best_mean: noise<1.50*sd]
FLUX_BIAS_MAG = 21.0  # [C ASTAP plot_and_measure_stars: 21 {bias}]
EDGE_WIDTH, EDGE_HEIGHT = 0.042, 0.015  # [C ASTAP get_hist: unused sensor areas up to 4.2%, 1.5%]
HISTOGRAM_TOP = 65000  # [C ASTAP get_hist: col<65000, bright stars out]
MEAN_OVER_MODE = 1.5  # [C ASTAP get_background: his_mean>1.5*backgr, use the mean]
SIXTEEN_BIT = 65535.0  # [T] top of a 16 bit pixel
WIDE_RANGE = 1.5  # [C ASTAP load_fits: measured_max<=1.5 or >65535*1.5, rescaled]
# Ozone 0.016 [Schaefer 1992] + Rayleigh 0.1451 + aerosol 0.120 per air mass; 0 at the zenith.
EXTINCTION_MAG = 0.2811  # [C ASTAP unit_hjd.pas atmospheric_absorption]
ZENITH_EXTINCTION_MAG = 0.28  # [C ASTAP unit_sqm.pas: correction at zenith defined as zero]


@dataclass(frozen=True)
class Wcs:
    ra_deg: float  # CRVAL1
    dec_deg: float  # CRVAL2
    crpix: tuple[float, float]  # FITS, from 1
    cd: tuple[float, float, float, float]  # degrees per pixel: CD1_1, CD1_2, CD2_1, CD2_2

    @property
    def scale_arcsec(self) -> float:
        return scale_arcsec(self.cd[1], self.cd[3])

    def to_pixels(self, ra: np.ndarray, dec: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Gnomonic projection to pixels counted from 0; SIP not used."""
        a0, d0 = math.radians(self.ra_deg), math.radians(self.dec_deg)
        a, d = np.radians(ra), np.radians(dec)
        cos_c = np.sin(d0) * np.sin(d) + np.cos(d0) * np.cos(d) * np.cos(a - a0)
        xi = np.degrees(np.cos(d) * np.sin(a - a0) / cos_c)
        eta = np.degrees((np.cos(d0) * np.sin(d) - np.sin(d0) * np.cos(d) * np.cos(a - a0)) / cos_c)
        inv = np.linalg.inv(np.array(self.cd).reshape(2, 2))
        dx, dy = inv[0, 0] * xi + inv[0, 1] * eta, inv[1, 0] * xi + inv[1, 1] * eta
        return dx + self.crpix[0] - 1, dy + self.crpix[1] - 1

    def to_sky(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        dx, dy = np.asarray(x) - (self.crpix[0] - 1), np.asarray(y) - (self.crpix[1] - 1)
        xi = np.radians(self.cd[0] * dx + self.cd[1] * dy)
        eta = np.radians(self.cd[2] * dx + self.cd[3] * dy)
        a0, d0 = math.radians(self.ra_deg), math.radians(self.dec_deg)
        den = math.cos(d0) - eta * math.sin(d0)
        ra = np.degrees(a0 + np.arctan2(xi, den)) % 360.0
        return ra, np.degrees(np.arctan2(math.sin(d0) + eta * math.cos(d0), np.hypot(xi, den)))


def scale_arcsec(cd1_2: float, cd2_2: float) -> float:
    """ASTAP's cdelt2 from the matrix (new_to_old_WCS), in arcseconds."""
    return math.hypot(cd1_2, cd2_2) * 3600.0


@dataclass(frozen=True)
class Flux:
    hfd: float
    snr: float
    flux: float
    x: float  # centre of gravity, from 0
    y: float


@dataclass(frozen=True)
class Calibration:
    zero_point_mag: float
    stars: int  # catalogue stars that set it
    sky_adu: float


def calibrate(
    data: np.ndarray, wcs: Wcs, folder: Path, code: str, *, colour: bool
) -> Calibration | None:
    """Zero point from the catalogue stars, sky from the histogram; colour on 2x2 blocks.
    None: no star calibrates."""
    data, top = as_sixteen_bit(np.asarray(data, dtype=np.float64))
    image, peaks = superpixel(data) if colour else (data, data)
    found = zero_point(image, peaks, top, wcs, (folder, code))
    if found is None:
        return None
    return Calibration(found[0], found[1], sky_mode(image))


def sky_brightness(
    zero_point_mag: float, sky_adu: float, taken_off_adu: float, scale_arcsec: float,
    airmass: float,
) -> float | None:  # fmt: skip
    """ZP - 2.5 log10((sky - pedestal - bias) / scale^2) + extinction; nothing left: None."""
    left = sky_adu - taken_off_adu
    if left <= 0:
        return None
    flat = zero_point_mag - 2.5 * math.log10(left / scale_arcsec**2)
    return flat + EXTINCTION_MAG * airmass - ZENITH_EXTINCTION_MAG


def as_sixteen_bit(data: np.ndarray) -> tuple[np.ndarray, float]:
    """The image and its top as ASTAP loads it: 0..1 or far over 16 bit rescaled to 65535."""
    top = float(data.max())
    if 0 < top <= WIDE_RANGE or top > SIXTEEN_BIT * WIDE_RANGE:
        return data * (SIXTEEN_BIT / top), SIXTEEN_BIT
    return data, top


def superpixel(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Each 2x2 block as its mean, same size and WCS; and as its maximum, for saturation. ASTAP's
    loop steps by one over a quarter of the frame: its intent is ported, not the slip."""
    h, w = data.shape[0] // 2 * 2, data.shape[1] // 2 * 2
    blocks = data[:h, :w].reshape(h // 2, 2, w // 2, 2)
    mean, top = data.copy(), data.copy()
    mean[:h, :w] = np.repeat(np.repeat(blocks.mean(axis=(1, 3)), 2, 0), 2, 1)
    top[:h, :w] = np.repeat(np.repeat(blocks.max(axis=(1, 3)), 2, 0), 2, 1)
    return mean, top


def sky_mode(image: np.ndarray) -> float:
    """get_hist and get_background: the histogram's mode from 1 to the mean, borders left out;
    the mean if over 1.5 times the mode."""
    h, w = image.shape
    dw, dh = math.trunc(w * EDGE_WIDTH), math.trunc(h * EDGE_HEIGHT)
    values = np.rint(image[dh : h - dh, dw : w - dw]).astype(np.int64).ravel()
    mean = round(float(values.sum()) / (values.size + 1))
    if mean == 0:
        return 0.0
    counted = values[(values >= 1) & (values < HISTOGRAM_TOP)]
    below_mean = np.bincount(counted, minlength=mean + 1)[1 : mean + 1]
    # no count at all: ASTAP keeps its first pixel
    sky = float(np.argmax(below_mean) + 1) if below_mean.any() else float(image[0, 0])
    return float(mean) if mean > MEAN_OVER_MODE * sky else sky


def zero_point(
    image: np.ndarray, peaks: np.ndarray, top: float, wcs: Wcs, catalogue: tuple[Path, str]
) -> tuple[float, int] | None:
    """MZERO and the stars behind it: plot_and_measure_stars in calibration mode."""
    ratios, weights = [], []
    for x, y, mag in _catalogue_stars(image.shape, wcs, catalogue):
        star = star_flux(image, round(x), round(y))
        if star is None or not (MIN_HFD <= star.hfd < MAX_HFD) or star.snr <= MIN_SNR:
            continue
        yc, xc = round(star.y), round(star.x)
        if peaks[yc - 1 : yc + 2, xc - 1 : xc + 2].max() >= top - SATURATION_MARGIN:
            continue
        ratios.append(star.flux / 10 ** ((FLUX_BIAS_MAG - mag) / 2.5))
        weights.append(star.snr)
    if not ratios:
        return None
    mean = best_mean(np.array(ratios), np.array(weights))
    if mean <= 0:
        return None
    return FLUX_BIAS_MAG + 2.5 * math.log10(mean), len(ratios)


def _catalogue_stars(
    shape: tuple[int, ...], wcs: Wcs, catalogue: tuple[Path, str]
) -> list[tuple[float, float, float]]:
    """Up to four areas, each read bright to faint until its quota of stars on the frame."""
    h, w = shape
    cdelt1 = math.hypot(wcs.cd[0], wcs.cd[2])
    field_org = math.hypot(w * cdelt1, h * wcs.scale_arcsec / 3600.0)
    field = min(field_org, MAX_FIELD_DEG)
    most = round(w * h * STARS_PER_PIXEL)
    if field_org > field:
        most = round(most * field**2 / field_org**2)
    ra0, dec0 = (float(v) for v in wcs.to_sky(np.array((w + 1) / 2 - 1), np.array((h + 1) / 2 - 1)))
    folder, code = catalogue
    found: list[tuple[float, float, float]] = []
    shared = 0.0
    for area, share in find_areas(ra0, dec0, field):
        shared += share
        quota = math.trunc(most * shared)
        stars = window(read_area(folder, code, area), ra0, dec0, field)
        xs, ys = wcs.to_pixels(stars.ra_deg, stars.dec_deg)
        on = (xs > -OUTSIDE_PX) & (xs <= w + OUTSIDE_PX)
        on &= (ys > -OUTSIDE_PX) & (ys <= h + OUTSIDE_PX)
        for i in np.flatnonzero(on)[: max(quota - len(found), 0)]:
            found.append((float(xs[i]), float(ys[i]), float(stars.mag[i])))
    return found


def best_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """get_best_mean: outside 1.5 sigma (from the MAD) out, the rest weighted by SNR."""
    if len(values) == 1:
        return float(values[0])
    if len(values) == 2:
        return float(values.mean())
    middle = smedian(values)
    sd = sigma_from_mad(smedian(np.abs(values - middle)))
    kept = np.abs(values - middle) < OUTLIER_SIGMA * sd
    if not kept.any():
        return 0.0
    return float((values[kept] * weights[kept]).sum() / weights[kept].sum())


def smedian(values: np.ndarray) -> float:
    """ASTAP's SMedian: odd and over 3, the mean of the three middle values."""
    s = np.sort(values)
    n, mid = len(s), (len(s) - 1) // 2
    if n <= 3 and n % 2:
        return float(s[mid])
    if n % 2:
        return float(s[mid - 1 : mid + 2].mean())
    return float((s[mid] + s[mid + 1]) / 2)


def star_flux(image: np.ndarray, x1: int, y1: int, rs: int = ANNULUS_RADIUS) -> Flux | None:
    """HFD with the full flux (aperture 99): sky from a one pixel ring, centre of gravity, the
    star's radius where its lit pixels drop, flux and SNR in ADU. None: no star there."""
    h, w = image.shape
    ring = rs + 1
    if x1 - ring <= 0 or x1 + ring >= w - 1 or y1 - ring <= 0 or y1 + ring >= h - 1:
        return None
    sky, sd = _ring_sky(image, x1, y1, rs)
    centre = _centre(image, (x1, y1), (sky, sd), rs)
    if centre is None:
        return None
    (xc, yc), rs = centre
    radius = _radius(image, (xc, yc), (sky, sd), rs + 2)
    if radius is None:
        return None
    offsets = np.arange(-radius, radius + 1)
    dy, dx = np.meshgrid(offsets, offsets, indexing="ij")
    values = _subpixel(image, xc + dx, yc + dy) - sky
    flux = max(float(values.sum()), 1e-5)
    hfd = max(MIN_HFD, 2 * float((values * np.hypot(dx, dy)).sum()) / flux)
    snr = flux / math.sqrt(flux + radius**2 * math.pi * sd**2) if flux >= 1 else 0.0
    return Flux(hfd, snr, flux, xc, yc)


def _ring_sky(image: np.ndarray, x1: int, y1: int, rs: int) -> tuple[float, float]:
    ring = rs + 1
    offsets = np.arange(-ring, ring + 1)
    dy, dx = np.meshgrid(offsets, offsets, indexing="ij")
    d2 = dx * dx + dy * dy
    values = image[y1 + dy, x1 + dx][(d2 > rs * rs) & (d2 <= ring * ring)]
    sky = smedian(values)
    return sky, max(sigma_from_mad(smedian(np.abs(values - sky))), 1.0)


def _centre(
    image: np.ndarray, at: tuple[int, int], sky: tuple[float, float], rs: int
) -> tuple[tuple[float, float], int] | None:
    """Centre of gravity of the lit pixels; the box shrinks until the star fills 2/9 of it."""
    h, w = image.shape
    (x1, y1), (level, sd) = at, sky
    while True:
        offsets = np.arange(-rs, rs + 1)
        dy, dx = np.meshgrid(offsets, offsets, indexing="ij")
        values = image[y1 + dy, x1 + dx] - level
        lit = values > SIGNAL_SIGMA * sd
        total = float(values[lit].sum())
        if total <= STAR_FLOOR_SIGMA * sd:
            return None
        xc = x1 + float((values[lit] * dx[lit]).sum()) / total
        yc = y1 + float((values[lit] * dy[lit]).sum()) / total
        if xc - rs < 0 or xc + rs > w - 1 or yc - rs < 0 or yc + rs > h - 1:
            return None
        count = int(lit.sum())
        boxed = count >= BOXED_SHARE * (rs + rs + 1) ** 2
        if not boxed:
            rs -= 2 if rs > 4 else 1
        if count <= 1:
            return None
        if boxed or rs <= 1:
            return (xc, yc), rs


def _radius(
    image: np.ndarray, centre: tuple[float, float], sky: tuple[float, float], rs: int
) -> int | None:
    """Where the lit pixels per ring drop under 10% of the most: the star's radius."""
    (xc, yc), (level, sd) = centre, sky
    offsets = np.arange(-rs, rs + 1)
    dy, dx = np.meshgrid(offsets, offsets, indexing="ij")
    distance = np.rint(np.hypot(dx, dy)).astype(np.int64)
    values = _subpixel(image, xc + dx, yc + dy) - level
    lit = (distance <= rs) & (values > SIGNAL_SIGMA * sd)
    per_ring = np.bincount(distance[lit], minlength=rs + 1)
    radius, top, started, illuminated = -1, 0, False, 0
    while True:
        radius += 1
        illuminated += int(per_ring[radius])
        started = started or per_ring[radius] > 0
        top = max(top, int(per_ring[radius]))
        if radius >= rs or (started and per_ring[radius] <= DROP_OFF * top):
            break
    if radius >= rs:
        return None
    if radius > 2 and illuminated < DISK_SHARE * (radius + radius - 2) ** 2:
        return None
    return radius


def _subpixel(image: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """value_subpixel: bilinear; 0 next to the border."""
    h, w = image.shape
    xt, yt = np.trunc(x).astype(np.int64), np.trunc(y).astype(np.int64)
    inside = (xt > 0) & (xt < w - 2) & (yt > 0) & (yt < h - 2)
    xt, yt = np.where(inside, xt, 1), np.where(inside, yt, 1)
    fx, fy = x - xt, y - yt
    value = (image[yt, xt] * (1 - fx) * (1 - fy) + image[yt, xt + 1] * fx * (1 - fy)
             + image[yt + 1, xt] * (1 - fx) * fy + image[yt + 1, xt + 1] * fx * fy)  # fmt: skip
    return np.where(inside, value, 0.0)
