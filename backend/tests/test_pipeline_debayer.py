"""VNG against Chang, Cheung, Pan (SPIE 3650, 1999) as printed by Chen, Stanford Psych 221:
acorn.stanford.edu/psych221/projects/1999/tingchen/algodep/vargra.html; window 1-25, centre 13."""

# ruff: noqa: E501  (the printed formulas, one per line, read against the page)
import re

import numpy as np
import pytest

from astrolog.pipeline.debayer import COLOURS, intensity, pattern_of, vng

_TOP = 65535.0

# R the centre colour, B the other one; G at N E S W. Printed SE "|B25 - R13|" is R25.
_RED_GRADIENTS = (
    "|G8 - G18| + |R3 - R13| + |B7 - B17| / 2 + |B9 - B19| / 2 + |G2 - G12| / 2 + |G4 - G14| / 2",
    "|G14 - G12| + |R15 - R13| + |B9 - B7| / 2 + |B19 - B17| / 2 + |G10 - G8| / 2 + |G20 - G18| / 2",
    "|G18 - G8| + |R23 - R13| + |B19 - B9| / 2 + |B17 - B7| / 2 + |G24 - G14| / 2 + |G22 - G12| / 2",
    "|G12 - G14| + |R11 - R13| + |B17 - B19| / 2 + |B7 - B9| / 2 + |G16 - G18| / 2 + |G6 - G8| / 2",
    "|B9 - B17| + |R5 - R13| + |G8 - G12| / 2 + |G14 - G18| / 2 + |G4 - G8| / 2 + |G10 - G14| / 2",
    "|B19 - B7| + |R25 - R13| + |G14 - G8| / 2 + |G18 - G12| / 2 + |G20 - G14| / 2 + |G24 - G18| / 2",
    "|B7 - B19| + |R1 - R13| + |G12 - G18| / 2 + |G8 - G14| / 2 + |G6 - G12| / 2 + |G2 - G8| / 2",
    "|B17 - B9| + |R21 - R13| + |G18 - G14| / 2 + |G12 - G8| / 2 + |G22 - G18| / 2 + |G16 - G12| / 2",
)
# printed for S W NE SE; N E NW SW the same by symmetry
_RED_REGIONS = (
    "G8 + (B7 + B9) / 2 + (R3 + R13) / 2",
    "G14 + (B9 + B19) / 2 + (R13 + R15) / 2",
    "G18 + (B17 + B19) / 2 + (R13 + R23) / 2",
    "G12 + (B7 + B17) / 2 + (R11 + R13) / 2",
    "(G4 + G8 + G10 + G14) / 4 + B9 + (R13 + R5) / 2",
    "(G14 + G18 + G20 + G24) / 4 + B19 + (R13 + R25) / 2",
    "(G2 + G6 + G8 + G12) / 4 + B7 + (R13 + R1) / 2",
    "(G12 + G16 + G18 + G22) / 4 + B17 + (R13 + R21) / 2",
)
# R at W and E, B at N and S.
_GREEN_GRADIENTS = (
    "|G3 - G13| + |B8 - B18| + |G7 - G17| / 2 + |G9 - G19| / 2 + |R2 - R12| / 2 + |R4 - R14| / 2",
    "|R14 - R12| + |G15 - G13| + |G9 - G7| / 2 + |G19 - G17| / 2 + |B10 - B8| / 2 + |B20 - B18| / 2",
    "|B18 - B8| + |G23 - G13| + |G19 - G9| / 2 + |G17 - G7| / 2 + |R24 - R14| / 2 + |R22 - R12| / 2",
    "|R12 - R14| + |G11 - G13| + |G17 - G19| / 2 + |G7 - G9| / 2 + |B16 - B18| / 2 + |B6 - B8| / 2",
    "|G9 - G17| + |G5 - G13| + |R4 - R12| + |B10 - B18|",
    "|G19 - G7| + |G25 - G13| + |B20 - B8| + |R24 - R12|",
    "|G7 - G19| + |G1 - G13| + |B6 - B18| + |R2 - R14|",
    "|G17 - G9| + |G21 - G13| + |R22 - R14| + |B16 - B8|",
)
# US 6421084 (same authors) S W NE SE, its red our B, its 4-sample "/ 2" a "/ 4";
# N E NW SW by symmetry
_GREEN_REGIONS = (
    "(G3 + G13) / 2 + B8 + (R2 + R4 + R12 + R14) / 4",
    "(G13 + G15) / 2 + R14 + (B8 + B10 + B18 + B20) / 4",
    "(G13 + G23) / 2 + B18 + (R12 + R14 + R22 + R24) / 4",
    "(G11 + G13) / 2 + R12 + (B6 + B8 + B16 + B18) / 4",
    "G9 + (R4 + R14) / 2 + (B8 + B10) / 2",
    "G19 + (R14 + R24) / 2 + (B18 + B20) / 2",
    "G7 + (R2 + R12) / 2 + (B6 + B8) / 2",
    "G17 + (R12 + R22) / 2 + (B16 + B18) / 2",
)
_SAMPLE = re.compile(r"([RGB])(\d+)")
_DIFFERENCE = re.compile(r"\|([RGB]\d+) - ([RGB]\d+)\|( / 2)?")
_AVERAGE = re.compile(r"\(([^)]*)\) / (\d)|([RGB]\d+)")


def _sample(name: str, v: list[float], role: dict[str, int], channel: list[int]) -> float:
    """A printed sample; its letter must be the colour sitting there."""
    letter, number = _SAMPLE.fullmatch(name).groups()  # type: ignore[union-attr]
    k = int(number) - 1
    assert channel[k] == role[letter], f"{name} is not that colour"
    return v[k]


def _gradient(formula: str, v: list[float], role: dict[str, int], channel: list[int]) -> float:
    terms = _DIFFERENCE.findall(formula)
    assert len(terms) == formula.count("|") // 2
    return sum(
        abs(_sample(a, v, role, channel) - _sample(b, v, role, channel)) * (0.5 if half else 1)
        for a, b, half in terms
    )


def _region(formula: str, v: list[float], role: dict[str, int], channel: list[int]) -> list[float]:
    """The three averages of one region, per channel (R G B)."""
    out = [0.0, 0.0, 0.0]
    for inside, n, single in _AVERAGE.findall(formula):
        names = [m[0] for m in _SAMPLE.finditer(inside or single)]
        assert len(names) == int(n or 1)
        out[role[names[0][0]]] = sum(_sample(s, v, role, channel) for s in names) / len(names)
    return out


def _pixel(v: list[float], channel: list[int]) -> list[float]:
    centre = channel[12]
    green = centre == 1
    role = {"G": 1, "R": channel[11], "B": channel[7]} if green else {"G": 1, "R": centre}
    role.setdefault("B", 2 - centre)
    gradients = [
        _gradient(f, v, role, channel) for f in (_GREEN_GRADIENTS if green else _RED_GRADIENTS)
    ]
    low, high = min(gradients), max(gradients)
    chosen = [i for i, g in enumerate(gradients) if g <= 1.5 * low + 0.5 * (high - low)]
    regions = _GREEN_REGIONS if green else _RED_REGIONS
    sums = np.sum([_region(regions[i], v, role, channel) for i in chosen], axis=0)
    return [
        v[12] if c == centre else min(max(v[12] + (sums[c] - sums[centre]) / len(chosen), 0.0), 1.0)
        for c in range(3)
    ]


def _oracle(cfa: np.ndarray, pattern: str) -> np.ndarray:
    """The printed formulas on [0,1] doubles; borders copied from the nearest computed pixel."""
    colours = COLOURS[pattern]
    rows, cols = cfa.shape
    out = np.zeros((3, rows, cols))
    for row in range(2, rows - 2):
        for col in range(2, cols - 2):
            v = [float(cfa[row + k // 5 - 2, col + k % 5 - 2]) for k in range(25)]
            channel = [colours[(row + k // 5) % 2][(col + k % 5) % 2] for k in range(25)]
            out[:, row, col] = _pixel(v, channel)
        out[:, row, :2] = out[:, row, 2:3]
        out[:, row, -2:] = out[:, row, -3:-2]
    out[:, :2] = out[:, 2:3]
    out[:, -2:] = out[:, -3:-2]
    return out


@pytest.mark.parametrize("pattern", sorted(COLOURS))
def test_vng_is_the_published_formulas_pixel_for_pixel(pattern: str) -> None:
    rng = np.random.default_rng(len(pattern) + ord(pattern[0]))
    cfa = rng.uniform(0, _TOP, (14, 17)).round().astype(np.float32)
    ours = vng(cfa, pattern, top=_TOP)
    assert ours.shape == (3, 14, 17)
    np.testing.assert_allclose(ours / _TOP, _oracle(cfa / _TOP, pattern), rtol=0, atol=2e-6)


def test_vng_keeps_a_star_where_its_colours_differ() -> None:
    """A red-rich star on a grey sky: smooth enough for VNG, sharp enough to tell its edges."""
    rows, cols = np.indices((24, 24))
    star = np.exp(-((rows - 11.3) ** 2 + (cols - 12.6) ** 2) / (2 * 1.6**2))
    gain = np.array([[2.0, 1.0], [1.0, 0.5]])[rows % 2, cols % 2]  # R G / G B
    cfa = (1000 + 30000 * star * gain).astype(np.float32)
    np.testing.assert_allclose(
        vng(cfa, "RGGB", top=_TOP) / _TOP, _oracle(cfa / _TOP, "RGGB"), rtol=0, atol=2e-6
    )


def test_a_grey_sky_stays_grey_to_the_edge() -> None:
    rgb = vng(np.full((9, 12), 1234.0, dtype=np.float32), "GBRG", top=_TOP)
    assert np.all(rgb == 1234.0)


def test_large_frames_go_by_strips_and_match_one_pass() -> None:
    rng = np.random.default_rng(7)
    cfa = rng.uniform(0, 4000, (70, 40)).astype(np.float32)
    np.testing.assert_array_equal(vng(cfa, "BGGR", top=_TOP, strip=8), vng(cfa, "BGGR", top=_TOP))


def test_intensity_is_the_hsi_mid_of_the_channels() -> None:
    """SubframeSelector measures a colour frame on (min + max) / 2 (sonde 26.48, pi_plane)."""
    rgb = np.array([[[1.0]], [[4.0]], [[2.0]]], dtype=np.float32)
    assert intensity(rgb)[0, 0] == pytest.approx(2.5)


@pytest.mark.parametrize(
    ("cards", "pattern"),
    [
        ({"BAYERPAT": "RGGB"}, "RGGB"),
        ({"BAYERPAT": " bggr "}, "BGGR"),
        ({"BAYERPAT": "RGGB", "XBAYROFF": 1}, "GRBG"),
        ({"BAYERPAT": "RGGB", "YBAYROFF": 1}, "GBRG"),
        ({"BAYERPAT": "RGGB", "XBAYROFF": 1, "YBAYROFF": 1}, "BGGR"),
        ({"BAYERPAT": "GRBG", "XBAYROFF": 2, "YBAYROFF": 0}, "GRBG"),
        ({"BAYERPAT": "RGGB", "ROWORDER": "BOTTOM-UP"}, "RGGB"),
        ({"BAYERPAT": "CYGM"}, None),
        ({"BAYERPAT": ""}, None),
        ({}, None),
    ],
)
def test_the_pattern_is_read_from_the_header(cards: dict[str, object], pattern: str) -> None:
    """BAYERPAT shifted by odd XBAYROFF, YBAYROFF; ROWORDER not read."""
    assert pattern_of(cards) == pattern
