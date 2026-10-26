"""Colour frame made one plane as WBPP measures it: VNG debayer (Chang, Cheung, Pan 1999; PCL
VNGThread copied term by term), then HSI intensity. Pure: pixels in, pixels out. software-ok"""

from collections.abc import Iterator, Mapping

import numpy as np

# Channel (0 R, 1 G, 2 B) at [row % 2][col % 2]. [C PCL BayerPatternToColorIndices]
COLOURS = {
    "RGGB": ((0, 1), (1, 2)),
    "BGGR": ((2, 1), (1, 0)),
    "GBRG": ((1, 2), (0, 1)),
    "GRBG": ((1, 0), (2, 1)),
}
K1, K2 = 1.5, 0.5  # threshold k1 min + k2 (max - min) [C Chang 1999, PCL VNGThread]
TIE = 1e-10  # on [0,1]: a gradient at the threshold is in [C PCL VNGThread]
BORDER = 2  # the 5x5 window: two rows and columns copied from the nearest computed [C PCL]
STRIP = 256  # [T] output rows per pass: memory a few MB, whatever the sensor

# N E S W NE SE NW SW: (a, b, weight) on the 5x5 window, row-major, centre 12; the full-weight SE
# and SW terms of a red or blue centre are PCL's own. [C PCL VNGThread::ComputeGradients]
_STRAIGHT = (
    ((7, 17, 1), (2, 12, 1), (6, 16, 0.5), (8, 18, 0.5), (1, 11, 0.5), (3, 13, 0.5)),
    ((13, 11, 1), (14, 12, 1), (8, 6, 0.5), (18, 16, 0.5), (9, 7, 0.5), (19, 17, 0.5)),
    ((17, 7, 1), (22, 12, 1), (16, 6, 0.5), (18, 8, 0.5), (21, 11, 0.5), (23, 13, 0.5)),
    ((11, 13, 1), (10, 12, 1), (6, 8, 0.5), (16, 18, 0.5), (5, 7, 0.5), (15, 17, 0.5)),
)
# [C PCL VNGThread::ComputeGradients] green centre
_GREEN = (
    *_STRAIGHT,
    ((8, 16, 1), (4, 12, 1), (3, 11, 1), (9, 17, 1)),
    ((18, 6, 1), (24, 12, 1), (23, 11, 1), (19, 7, 1)),
    ((6, 18, 1), (0, 12, 1), (1, 13, 1), (5, 17, 1)),
    ((16, 8, 1), (20, 12, 1), (21, 13, 1), (15, 7, 1)),
)
# [C PCL VNGThread::ComputeGradients] red or blue centre
_OTHER = (
    *_STRAIGHT,
    ((8, 16, 1), (4, 12, 1), (7, 11, 0.5), (13, 17, 0.5), (3, 7, 0.5), (9, 13, 0.5)),
    ((18, 6, 1), (24, 12, 1), (13, 7, 0.5), (17, 11, 0.5), (19, 13, 1), (23, 17, 0.5)),
    ((6, 18, 1), (0, 12, 1), (7, 13, 0.5), (11, 17, 0.5), (1, 7, 0.5), (5, 11, 0.5)),
    ((16, 8, 1), (20, 12, 1), (11, 7, 0.5), (17, 13, 0.5), (15, 11, 1), (21, 17, 0.5)),
)
# Window samples each valid direction averages, per channel. [C PCL VNGThread::ComputeSums]
_GREEN_SUMS = (
    (1, 2, 3, 7, 11, 12, 13), (7, 9, 12, 13, 14, 17, 19), (11, 12, 13, 17, 21, 22, 23),
    (5, 7, 10, 11, 12, 15, 17), (3, 7, 8, 9, 13), (13, 17, 18, 19, 23), (1, 5, 6, 7, 11),
    (11, 15, 16, 17, 21),
)  # fmt: skip
# [C PCL VNGThread::ComputeSums] red or blue centre
_OTHER_SUMS = (
    (2, 6, 7, 8, 12), (8, 12, 13, 14, 18), (12, 16, 17, 18, 22), (6, 10, 11, 12, 16),
    (3, 4, 7, 8, 9, 12, 13), (12, 13, 17, 18, 19, 23, 24), (0, 1, 5, 6, 7, 11, 12),
    (11, 12, 15, 16, 17, 20, 21),
)  # fmt: skip


def pattern_of(cards: Mapping[str, object]) -> str | None:
    """BAYERPAT with an odd XBAYROFF swapping columns, an odd YBAYROFF rows; ROWORDER not read
    (PCL DebayerInstance::BayerPatternFromTargetPropertyValue). None: no RGB Bayer matrix."""
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
    rgb = np.empty((3, *mosaic.shape), dtype=np.float32)
    for start, rows in _strips(mosaic, pattern, top, strip):
        rgb[:, start : start + rows.shape[1]] = rows
    return _rows_copied(rgb)


def debayered(mosaic: np.ndarray, pattern: str, *, top: float) -> np.ndarray:
    """The intensity plane of the VNG image, a strip at a time: never three full planes."""
    plane = np.empty(mosaic.shape, dtype=np.float32)
    for start, rows in _strips(mosaic, pattern, top, STRIP):
        plane[start : start + rows.shape[1]] = intensity(rows)
    return _rows_copied(plane[np.newaxis])[0]


def intensity(rgb: np.ndarray) -> np.ndarray:
    """HSI intensity (min + max) / 2, the plane SubframeSelector measures a colour frame on
    (PCL SubframeSelectorInstance ReadInputData, RGBColorSystem::Intensity)."""
    return (rgb.min(axis=0) + rgb.max(axis=0)) / 2


def _rows_copied(planes: np.ndarray) -> np.ndarray:
    planes[:, :BORDER] = planes[:, BORDER : BORDER + 1]
    planes[:, -BORDER:] = planes[:, -BORDER - 1 : -BORDER]
    return planes


def _strips(
    mosaic: np.ndarray, pattern: str, top: float, strip: int
) -> Iterator[tuple[int, np.ndarray]]:
    """Inner rows in even-sized strips from row 2: a strip's row parity is the frame's."""
    height = mosaic.shape[0]
    step = max(2, strip - strip % 2)
    for start in range(BORDER, height - BORDER, step):
        stop = min(start + step, height - BORDER)
        yield start, _strip(mosaic[start - BORDER : stop + BORDER], COLOURS[pattern], top)


def _strip(block: np.ndarray, colours: tuple[tuple[int, int], ...], top: float) -> np.ndarray:
    rows, cols = block.shape[0] - 2 * BORDER, block.shape[1] - 2 * BORDER
    out = np.empty((3, rows, block.shape[1]), dtype=np.float32)
    # the four same-parity planes, contiguous: a window sample is then a plain slice
    planes = [[np.ascontiguousarray(block[r::2, c::2]) for c in (0, 1)] for r in (0, 1)]
    for pr in (0, 1):
        for pc in (0, 1):
            nr, nc = len(range(pr, rows, 2)), len(range(pc, cols, 2))
            if nr and nc:
                window = [
                    planes[(pr + k // 5) % 2][(pc + k % 5) % 2][
                        (pr + k // 5) // 2 : (pr + k // 5) // 2 + nr,
                        (pc + k % 5) // 2 : (pc + k % 5) // 2 + nc,
                    ]
                    for k in range(25)
                ]
                channels = [colours[(pr + k // 5) % 2][(pc + k % 5) % 2] for k in range(25)]
                out[:, pr:rows:2, BORDER + pc : BORDER + cols : 2] = _lattice(window, channels, top)
    out[:, :, :BORDER] = out[:, :, BORDER : BORDER + 1]
    out[:, :, -BORDER:] = out[:, :, -BORDER - 1 : -BORDER]
    return out


def _lattice(window: list[np.ndarray], channels: list[int], top: float) -> np.ndarray:
    """One of the four sub-lattices: every centre the same colour, so one table for all."""
    centre = channels[12]
    green = centre == 1
    terms = _GREEN if green else _OTHER
    pairs = {frozenset((a, b)) for direction in terms for a, b, _ in direction}
    diffs = {pair: np.abs(np.subtract(*(window[k] for k in pair))) for pair in pairs}
    gradients = np.zeros((len(terms), *window[12].shape), dtype=np.float32)
    for gradient, direction in zip(gradients, terms, strict=True):
        for a, b, w in direction:  # in PCL's order: the same float sums
            gradient += diffs[frozenset((a, b))] * w if w != 1 else diffs[frozenset((a, b))]
    low, high = gradients.min(axis=0), gradients.max(axis=0)
    valid = gradients <= K1 * low + K2 * (high - low) + TIE * top
    sums = np.zeros((3, *window[12].shape), dtype=np.float32)
    for direction, samples in enumerate(_GREEN_SUMS if green else _OTHER_SUMS):
        for channel in set(channels[k] for k in samples):
            members = [window[k] for k in samples if channels[k] == channel]
            sums[channel] += np.where(valid[direction], sum(members) / len(members), 0)
    count = valid.sum(axis=0)
    rgb = np.empty_like(sums)
    for channel in range(3):
        moved = window[12] + (sums[channel] - sums[centre]) / count
        rgb[channel] = window[12] if channel == centre else np.clip(moved, 0, top)
    return rgb
