"""Qn di Rousseeuw e Croux e la soglia relativa che ne nasce (ADR 0039): la costante e i fattori di
piccolo campione citati, la selezione esatta contro il conto ingenuo, la resistenza agli outlier."""

import math

import numpy as np
import pytest

from astrolog import robust
from astrolog.robust import qn, relative_bounds


def _naive(values: list[float]) -> float:
    """Qn senza correzione per n: il k-esimo scarto fra tutte le coppie, contato a mano."""
    x = np.asarray(values, dtype=float)
    i, j = np.triu_indices(len(x), k=1)
    gaps = np.sort(np.abs(x[i] - x[j]))
    h = len(x) // 2 + 1
    return float(gaps[math.comb(h, 2) - 1])


def test_the_constant_is_the_corrected_one():
    """1/(sqrt 2 Phi^-1(5/8)) = 2.219144: il 2.2219 dei primi lavori e' un refuso (robustbase)."""
    from statistics import NormalDist

    exact = 1 / (math.sqrt(2) * NormalDist().inv_cdf(5 / 8))
    assert pytest.approx(exact, abs=1e-5) == robust.QN_CONSTANT
    assert pytest.approx(2.21914) == robust.QN_CONSTANT


def test_the_small_sample_factors_are_robustbase():
    """Fino a 12 la tavola di robustbase 0.99-7, oltre il suo polinomio in 1/n (dispari e pari)."""
    assert robust.small_sample_factor(2) == pytest.approx(0.399356)
    assert robust.small_sample_factor(9) == pytest.approx(0.87344)
    assert robust.small_sample_factor(12) == pytest.approx(0.75743)
    odd = 1 + (1.60188 + (-2.1284 - 5.172 / 13) / 13) / 13
    assert robust.small_sample_factor(13) == pytest.approx(1 / odd)
    even = 1 + (3.67561 + (1.9654 + (6.987 - 77 / 40) / 40) / 40) / 40
    assert robust.small_sample_factor(40) == pytest.approx(1 / even)


@pytest.mark.parametrize("n", [3, 10, 11, 25, 200])
def test_the_selection_matches_every_pair(n: int):
    """La bisezione da' lo stesso scarto del conto su tutte le coppie, anche coi valori ripetuti."""
    rng = np.random.default_rng(n)
    values = np.round(rng.normal(0, 3, n), 1).tolist()
    expected = _naive(values) * robust.QN_CONSTANT * robust.small_sample_factor(n)
    assert qn(values) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("n", [5, 10, 11, 50])
def test_qn_is_a_sigma_on_a_normal(n: int):
    """Con la correzione per n la media su campioni normali e' sigma, entro 4 errori standard."""
    rng = np.random.default_rng(1993)
    draws = [qn(rng.normal(0, 1, n).tolist()) or 0.0 for _ in range(4000)]
    mean = float(np.mean(draws))
    assert abs(mean - 1) < 4 * float(np.std(draws)) / math.sqrt(len(draws))


def test_outliers_do_not_move_qn():
    """Il 30% di valori assurdi non porta Qn lontano: il punto di rottura e' al 50%."""
    rng = np.random.default_rng(7)
    clean = rng.normal(0, 1, 70).tolist()
    assert qn(clean + [1e6] * 30) == pytest.approx(qn(clean), rel=0.6)


def test_qn_needs_two_values():
    """Uno o nessun valore: nessuna scala. Tutti uguali: scala zero."""
    assert qn([]) is None
    assert qn([4.0]) is None
    assert qn([2.0, 2.0, 2.0]) == 0.0


def test_the_largest_pair_is_counted_despite_rounding():
    """Con -0.5 e 0.1, -0.5 + (0.1 + 0.5) scende sotto 0.1: la coppia piu' larga va contata."""
    assert qn([-0.5, 0.1]) == pytest.approx(0.6 * robust.QN_CONSTANT * 0.399356)
    rng = np.random.default_rng(2)
    for _ in range(2000):
        values = rng.normal(size=int(rng.integers(2, 6))).tolist()
        expected = _naive(values) * robust.QN_CONSTANT * robust.small_sample_factor(len(values))
        assert qn(values) == pytest.approx(expected, rel=1e-12)


def test_the_relative_bounds_are_two_and_a_half_qn():
    """Mediana +- 2,5 Qn (ADR 0039); sotto 10 valori la soglia tace."""
    values = [float(v) for v in range(1, 11)]
    bounds = relative_bounds(values)
    assert bounds is not None
    scale = qn(values)
    assert scale is not None
    assert bounds.median == pytest.approx(5.5)
    assert bounds.low == pytest.approx(5.5 - 2.5 * scale)
    assert bounds.high == pytest.approx(5.5 + 2.5 * scale)
    assert relative_bounds(values[:9]) is None


def test_a_zero_scale_is_silent():
    """Qn zero (valori ripetuti, frame copiati): la soglia sarebbe la mediana, e tace."""
    assert relative_bounds([0.5] * 8 + [0.6, 0.7]) is None
