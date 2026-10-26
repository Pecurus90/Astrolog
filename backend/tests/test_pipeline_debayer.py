"""VNG debayer against a literal transcription of the reference VNGThread (PCL,
DebayerInstance.cpp), pixel by pixel; the pattern from the header as its Auto reads it."""

import numpy as np
import pytest

from astrolog.pipeline.debayer import (
    _GREEN,
    _GREEN_SUMS,
    _OTHER,
    _OTHER_SUMS,
    COLOURS,
    intensity,
    pattern_of,
    vng,
)

_TOP = 65535.0
# PCL's tables live once in debayer.py; the oracle checks the vectorised loop around them.


def _oracle(cfa: np.ndarray, pattern: str) -> np.ndarray:
    """PCL's reference loop on [0,1] doubles, borders copied from the nearest computed pixel."""
    colours = COLOURS[pattern]
    rows, cols = cfa.shape
    out = np.zeros((3, rows, cols))
    for row in range(2, rows - 2):
        for col in range(2, cols - 2):
            v = [cfa[row + k // 5 - 2, col + k % 5 - 2] for k in range(25)]
            channel = [colours[(row + k // 5 - 2) % 2][(col + k % 5 - 2) % 2] for k in range(25)]
            centre = channel[12]
            table = _GREEN if centre == 1 else _OTHER
            gradients = [sum(abs(v[a] - v[b]) * w for a, b, w in terms) for terms in table]
            low, high = min(gradients), max(gradients)
            threshold = 1.5 * low + 0.5 * (high - low)
            valid = [i for i in range(8) if gradients[i] <= threshold + 1e-10]
            sums = [0.0, 0.0, 0.0]
            for i in valid:
                part, count = [0.0, 0.0, 0.0], [0, 0, 0]
                for k in (_GREEN_SUMS if centre == 1 else _OTHER_SUMS)[i]:
                    part[channel[k]] += v[k]
                    count[channel[k]] += 1
                for c in range(3):
                    if count[c]:
                        sums[c] += part[c] / count[c]
            for c in range(3):
                value = v[12] + (sums[c] - sums[centre]) / len(valid)
                out[c, row, col] = v[12] if c == centre else min(max(value, 0.0), 1.0)
        out[:, row, :2] = out[:, row, 2:3]
        out[:, row, -2:] = out[:, row, -3:-2]
    out[:, :2] = out[:, 2:3]
    out[:, -2:] = out[:, -3:-2]
    return out


@pytest.mark.parametrize("pattern", sorted(COLOURS))
def test_vng_is_pixinsights_pixel_for_pixel(pattern: str) -> None:
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
    """SubframeSelector measures a colour frame on (min + max) / 2 (PCL RGBColorSystem)."""
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
def test_the_pattern_is_read_as_pixinsights_auto(cards: dict[str, object], pattern: str) -> None:
    """BAYERPAT shifted by odd XBAYROFF, YBAYROFF; ROWORDER not read (PCL BayerPatternFrom...)."""
    assert pattern_of(cards) == pattern
