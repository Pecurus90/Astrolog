"""Colour frame made one plane as WBPP measures it: VNG debayer (Chang, Cheung, Pan, SPIE 3650,
1999), then HSI intensity. Pure: pixels in, pixels out. software-ok"""

import functools
from collections.abc import Mapping

import numpy as np

from .cores import compiled, each, inlined, maximum, minimum

# Channel (0 R, 1 G, 2 B) at [row % 2][col % 2]. [C BAYERPAT: letters row by row from pixel 0]
COLOURS = {
    "RGGB": ((0, 1), (1, 2)),
    "BGGR": ((2, 1), (1, 0)),
    "GBRG": ((1, 2), (0, 1)),
    "GRBG": ((1, 0), (2, 1)),
}
# threshold k1 min + k2 (max - min); equal gradients all pass, flat sky too [C Chang 1999]
K1, K2 = 1.5, 0.5
BORDER = 2  # [T] the 5x5 window: two rows and columns copied from the nearest computed
STRIP = 256  # [T] output rows per pass: memory a few MB, whatever the sensor

# N E S W NE SE NW SW: (a, b, weight) on the 5x5 window, row-major, centre 12. Formulas as printed
# by Chen, Stanford Psych 221 (1999), 1-based there; SE "|B25 - R13|" is R25. [C Chang 1999]
_STRAIGHT = (
    ((7, 17, 1), (2, 12, 1), (6, 16, 0.5), (8, 18, 0.5), (1, 11, 0.5), (3, 13, 0.5)),
    ((13, 11, 1), (14, 12, 1), (8, 6, 0.5), (18, 16, 0.5), (9, 7, 0.5), (19, 17, 0.5)),
    ((17, 7, 1), (22, 12, 1), (18, 8, 0.5), (16, 6, 0.5), (23, 13, 0.5), (21, 11, 0.5)),
    ((11, 13, 1), (10, 12, 1), (16, 18, 0.5), (6, 8, 0.5), (15, 17, 0.5), (5, 7, 0.5)),
)
# green centre: the diagonals weigh all four terms 1 [C Chang 1999]
_GREEN = (
    *_STRAIGHT,
    ((8, 16, 1), (4, 12, 1), (3, 11, 1), (9, 17, 1)),
    ((18, 6, 1), (24, 12, 1), (19, 7, 1), (23, 11, 1)),
    ((6, 18, 1), (0, 12, 1), (5, 17, 1), (1, 13, 1)),
    ((16, 8, 1), (20, 12, 1), (21, 13, 1), (15, 7, 1)),
)
# red or blue centre [C Chang 1999]
_OTHER = (
    *_STRAIGHT,
    ((8, 16, 1), (4, 12, 1), (7, 11, 0.5), (13, 17, 0.5), (3, 7, 0.5), (9, 13, 0.5)),
    ((18, 6, 1), (24, 12, 1), (13, 7, 0.5), (17, 11, 0.5), (19, 13, 0.5), (23, 17, 0.5)),
    ((6, 18, 1), (0, 12, 1), (11, 17, 0.5), (7, 13, 0.5), (5, 11, 0.5), (1, 7, 0.5)),
    ((16, 8, 1), (20, 12, 1), (17, 13, 0.5), (11, 7, 0.5), (21, 17, 0.5), (15, 11, 0.5)),
)
# Region of each direction, averaged per channel: Chen's table, a green centre's from US 6421084;
# the directions they omit by symmetry. [C Chang 1999]
_GREEN_SUMS = (
    (1, 2, 3, 7, 11, 12, 13), (7, 9, 12, 13, 14, 17, 19), (11, 12, 13, 17, 21, 22, 23),
    (5, 7, 10, 11, 12, 15, 17), (3, 7, 8, 9, 13), (13, 17, 18, 19, 23), (1, 5, 6, 7, 11),
    (11, 15, 16, 17, 21),
)  # fmt: skip
# red or blue centre [C Chang 1999]
_OTHER_SUMS = (
    (2, 6, 7, 8, 12), (8, 12, 13, 14, 18), (12, 16, 17, 18, 22), (6, 10, 11, 12, 16),
    (3, 4, 7, 8, 9, 12, 13), (12, 13, 17, 18, 19, 23, 24), (0, 1, 5, 6, 7, 11, 12),
    (11, 12, 15, 16, 17, 20, 21),
)  # fmt: skip


def pattern_of(cards: Mapping[str, object]) -> str | None:
    """BAYERPAT with an odd XBAYROFF swapping columns, an odd YBAYROFF rows; ROWORDER not read.
    None: no RGB Bayer matrix."""
    written = cards.get("BAYERPAT")
    if not isinstance(written, str):
        return None
    cells = list(written.strip().upper())
    if _odd(cards.get("XBAYROFF")) and len(cells) == 4:
        cells = [cells[1], cells[0], cells[3], cells[2]]
    if _odd(cards.get("YBAYROFF")) and len(cells) == 4:
        cells = [cells[2], cells[3], cells[0], cells[1]]
    pattern = "".join(cells)
    return pattern if pattern in COLOURS else None


def _odd(written: object) -> bool:
    number = isinstance(written, int | float) and not isinstance(written, bool)
    return number and int(written) % 2 == 1  # type: ignore[arg-type]


def vng(mosaic: np.ndarray, pattern: str, *, top: float, strip: int = STRIP) -> np.ndarray:
    """(3, rows, cols) float32 R G B; `top`: the full scale the interpolated channels clip at."""
    return _filled(np.empty((3, *mosaic.shape), dtype=np.float32), mosaic, pattern, (top, strip))


def debayered(mosaic: np.ndarray, pattern: str, *, top: float) -> np.ndarray:
    """The intensity plane of the VNG image, pixel by pixel: never three full planes."""
    plane = np.empty((1, *mosaic.shape), dtype=np.float32)
    return _filled(plane, mosaic, pattern, (top, STRIP))[0]


def intensity(rgb: np.ndarray) -> np.ndarray:
    """HSI intensity (min + max) / 2, the plane SubframeSelector measures a colour frame on
    (sonde 26.48, pi_plane: its counts on RGB are those on this plane)."""
    return (rgb.min(axis=0) + rgb.max(axis=0)) / 2


def _filled(
    planes: np.ndarray, mosaic: np.ndarray, pattern: str, at: tuple[float, int]
) -> np.ndarray:
    """VNG on the inner rows a strip per core into `planes`: three R G B, or one the intensity;
    the two border rows and columns copied from the nearest computed."""
    top, strip = at
    image = np.ascontiguousarray(mosaic, dtype=np.float32)
    tables = _tables(pattern)
    each(lambda span: _vng(image, tables, np.float64(top), span, planes),
         _strips(mosaic.shape[0], strip))  # fmt: skip
    planes[:, :, :BORDER] = planes[:, :, BORDER : BORDER + 1]
    planes[:, :, -BORDER:] = planes[:, :, -BORDER - 1 : -BORDER]
    return _rows_copied(planes)


def _rows_copied(planes: np.ndarray) -> np.ndarray:
    planes[:, :BORDER] = planes[:, BORDER : BORDER + 1]
    planes[:, -BORDER:] = planes[:, -BORDER - 1 : -BORDER]
    return planes


@functools.cache
def _tables(pattern: str) -> tuple[np.ndarray, ...]:
    """Per centre parity (row % 2 * 2 + col % 2), padded: its colour; each direction's pairs,
    float32 weights and their number; its region's pixels by colour, in order, and how many."""
    centres = np.zeros(4, dtype=np.int64)
    pairs = np.zeros((4, 8, 6, 2), dtype=np.int64)
    weights = np.zeros((4, 8, 6), dtype=np.float32)
    terms = np.zeros((4, 8), dtype=np.int64)
    members = np.zeros((4, 8, 3, 7), dtype=np.int64)
    sizes = np.zeros((4, 8, 3), dtype=np.int64)
    colours = COLOURS[pattern]
    for p in range(4):
        row, col = divmod(p, 2)
        centres[p] = colours[row][col]
        green = centres[p] == 1
        directions, regions = (_GREEN, _GREEN_SUMS) if green else (_OTHER, _OTHER_SUMS)
        for d, (direction, region) in enumerate(zip(directions, regions, strict=True)):
            terms[p, d] = len(direction)
            for t, (a, b, w) in enumerate(direction):
                pairs[p, d, t], weights[p, d, t] = (a, b), w
            for k in region:
                colour = colours[(row + k // 5) % 2][(col + k % 5) % 2]
                members[p, d, colour, sizes[p, d, colour]] = k
                sizes[p, d, colour] += 1
    return centres, pairs, weights, terms, members, sizes


def _strips(height: int, strip: int) -> list[tuple[int, int]]:
    """Inner rows in even-sized strips from row 2: a strip's row parity is the frame's."""
    step = max(2, strip - strip % 2)
    return [(start, min(start + step, height - BORDER))
            for start in range(BORDER, height - BORDER, step)]  # fmt: skip


@compiled
def _vng(mosaic: np.ndarray, tables: tuple[np.ndarray, ...], top: float, span: tuple[int, int],
         planes: np.ndarray) -> None:  # fmt: skip
    """Rows `span` (inner), every inner column: R G B into three planes, or the intensity into
    one. float32 sums as numpy's on float32, the step over the count in float64 as theirs."""
    cols = mosaic.shape[1]
    window = np.empty(25, dtype=np.float32)
    scratch = np.empty((2, 8), dtype=np.float32)  # gradients; R G B sums
    rgb = np.empty(3, dtype=np.float32)
    for r in range(*span):
        for c in range(BORDER, cols - BORDER):
            for dy in range(5):
                for dx in range(5):
                    window[dy * 5 + dx] = mosaic[r - BORDER + dy, c - BORDER + dx]
            _pixel(window, tables, (r % 2) * 2 + c % 2, (top, scratch), rgb)
            if planes.shape[0] == 3:
                planes[0, r, c], planes[1, r, c], planes[2, r, c] = rgb[0], rgb[1], rgb[2]
            else:
                low = minimum(minimum(rgb[0], rgb[1]), rgb[2])
                high = maximum(maximum(rgb[0], rgb[1]), rgb[2])
                planes[0, r, c] = (low + high) / np.float32(2)


@inlined
def _gradients(window: np.ndarray, tables: tuple[np.ndarray, ...], parity: int,
               gradient: np.ndarray) -> np.float32:  # fmt: skip
    """The eight directions' gradients into `gradient`; the threshold k1 min + k2 (max - min)."""
    _, pairs, weights, terms, _, _ = tables
    for d in range(8):
        total = np.float32(0)
        for t in range(terms[parity, d]):
            a, b = pairs[parity, d, t, 0], pairs[parity, d, t, 1]
            total += abs(window[a] - window[b]) * weights[parity, d, t]
        gradient[d] = total
    low, high = gradient[0], gradient[0]
    for d in range(1, 8):
        low, high = minimum(low, gradient[d]), maximum(high, gradient[d])
    return np.float32(K1) * low + np.float32(K2) * (high - low)


@inlined
def _pixel(window: np.ndarray, tables: tuple[np.ndarray, ...], parity: int,
           at: tuple[float, np.ndarray], rgb: np.ndarray) -> None:  # fmt: skip
    """One pixel's R G B from its 5x5 window (Chang 1999): gradients, the threshold, the mean
    step of each colour over the directions under it, added to the centre."""
    centres, _, _, _, members, sizes = tables
    top, scratch = at
    gradient, sums = scratch[0], scratch[1]
    centre = centres[parity]
    under = _gradients(window, tables, parity, gradient)
    sums[:3] = 0
    count = 0
    for d in range(8):
        if not gradient[d] <= under:
            continue
        count += 1
        for colour in range(3):
            n = sizes[parity, d, colour]
            if n:
                mean = np.float32(0)
                for m in range(n):
                    mean += window[members[parity, d, colour, m]]
                sums[colour] += mean / np.float32(n)
    for colour in range(3):
        if colour == centre:
            rgb[colour] = window[12]
        else:
            moved = float(window[12]) + float(sums[colour] - sums[centre]) / count
            rgb[colour] = min(max(moved, 0.0), top) if moved == moved else moved
