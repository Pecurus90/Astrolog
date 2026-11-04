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


def test_the_biweight_is_the_centre_of_a_normal_and_ignores_far_outliers():
    """Tukey (ImageAnalysis par. 2.2): oltre 6 MAD peso zero; sul campione normale e' la media."""
    rng = np.random.default_rng(3)
    values = rng.normal(10.0, 1.0, 2001)
    clean = robust.biweight_location(values)
    assert clean == pytest.approx(10.0, abs=0.05)
    spoiled = np.concatenate([values, np.full(300, 40.0)])
    assert robust.biweight_location(spoiled) == pytest.approx(clean, abs=0.05)
    assert float(np.mean(spoiled)) > 13


def test_the_biweight_is_the_fixed_point_of_its_weights():
    """L'iterazione di eq. 109 si ferma dove M = somma pesata / somma dei pesi, MAD del passo 0."""
    values = np.array([1.0, 2.0, 2.5, 3.0, 3.2, 4.0, 9.0])
    centre = robust.biweight_location(values)
    assert centre is not None
    mad = float(np.median(np.abs(values - np.median(values))))
    u = (values - centre) / (robust.BIWEIGHT_C * mad)
    w = np.where(np.abs(u) < 1, (1 - u * u) ** 2, 0.0)
    assert centre == pytest.approx(float((w * values).sum() / w.sum()), abs=1e-9)


def test_the_biweight_of_nothing_or_of_ties():
    assert robust.biweight_location([]) is None
    assert robust.biweight_location([2.0, 2.0, 2.0, 5.0]) == 2.0  # MAD zero: the median


def test_chauvenet_keeps_a_normal_sample_and_drops_far_outliers():
    """Maples et al. 2018: N P(>|z|) < 0.5 rejects; with the correction factors a clean normal
    sample loses almost nothing, and 5% at 50 sigma go, however much they pull the mean."""
    rng = np.random.default_rng(7)
    clean = rng.normal(10.0, 1.0, 1000)
    assert robust.robust_chauvenet(clean).sum() >= 995
    spoiled = np.concatenate([clean, np.full(50, 60.0)])
    kept = robust.robust_chauvenet(spoiled)
    assert not kept[1000:].any() and kept[:1000].sum() >= 990


def test_chauvenet_rejects_one_at_a_time_from_the_farthest():
    """Rejected one per pass, the farthest first, until none passes the criterion."""
    values = np.array([10.0, 10.2, 9.8, 10.1, 9.9, 10.05, 9.95, 10.0, 10.15, 9.85, 13.0, 30.0])
    kept = robust.robust_chauvenet(values)
    assert kept.tolist() == [True] * 10 + [False, False]


def test_chauvenet_on_ties_or_too_few_keeps_all():
    assert robust.robust_chauvenet(np.full(10, 3.0)).all()
    assert robust.robust_chauvenet(np.array([1.0, 100.0])).all()
    assert robust.robust_chauvenet(np.empty(0)).size == 0


def test_rejected_values_are_winsorized_to_the_nearest_kept():
    """ImageWeighting par. 2.2.1: replaced with the nearest accepted values, the count kept."""
    values = np.array([1.0, 5.0, 6.0, 7.0, 50.0])
    kept = np.array([False, True, True, True, False])
    assert robust.winsorized(values, kept).tolist() == [5.0, 5.0, 6.0, 7.0, 7.0]


def _naive_sn(values: np.ndarray) -> float:
    """Sn by the definition: himed over j of |x_i - x_j|, then lomed over i."""
    x = np.sort(values)
    inner = np.sort(np.abs(x[:, None] - x[None, :]), axis=1)[:, len(x) // 2]
    return float(np.sort(inner)[(len(x) + 1) // 2 - 1])


def test_sn_is_the_definition_on_small_samples():
    rng = np.random.default_rng(7)
    for n in (1, 2, 3, 10, 51, 400):
        values = rng.normal(0.0, 1.0, n)
        assert robust.sn(values) == pytest.approx(_naive_sn(values), abs=1e-12)
    assert robust.sn(np.empty(0)) is None


def test_sn_of_a_half_normal_sample_needs_its_own_factor():
    """ImageWeighting eq. 20: 1 / 0.4867777 = 2.054326 makes Sn of a half-normal its sigma."""
    values = np.abs(np.random.default_rng(8).normal(0.0, 1.0, 400_000))
    sn = robust.sn(values)
    assert sn is not None
    assert 2.054326 * sn == pytest.approx(1.0, rel=0.005)


def test_the_biweight_fit_drops_the_outliers_a_least_squares_follows():
    """A line, a fifth of its points thrown 50 sigma up: the biweight finds the line again."""
    rng = np.random.default_rng(9)
    x = np.linspace(-1.0, 1.0, 200)
    y = 2.0 + 0.5 * x + rng.normal(0.0, 0.01, x.size)
    y[::5] += 0.5
    design = np.column_stack([np.ones_like(x), x])
    assert robust.biweight_fit(design, y) == pytest.approx([2.0, 0.5], abs=0.005)
    assert np.linalg.lstsq(design, y, rcond=None)[0][0] == pytest.approx(2.1, abs=0.01)


def test_the_upper_biweight_fit_downweights_only_the_points_above():
    """Clouds only add extinction (ImageAnalysis par. 2.1.7): points far below keep their weight,
    points far above lose it; the scale is the MAD about the median residual. software-ok"""
    rng = np.random.default_rng(11)
    x = np.linspace(1.0, 2.0, 100)
    design = np.column_stack([np.ones_like(x), x])
    y = 0.1 + 0.2 * x + rng.normal(0.0, 0.01, x.size)
    up, down = y.copy(), y.copy()
    up[::10] += 0.5
    down[::10] -= 0.5
    assert robust.biweight_fit(design, up, upper=True) == pytest.approx([0.1, 0.2], abs=0.01)
    lower = robust.biweight_fit(design, down, upper=True)  # the points below pull it down
    assert lower[0] + 1.5 * lower[1] < 0.1 + 0.2 * 1.5 - 0.04
    assert robust.biweight_fit(design, down) == pytest.approx([0.1, 0.2], abs=0.01)


def test_the_biweight_fit_of_an_exact_surface_is_the_surface():
    """Residuals all zero, MAD zero: the ordinary fit stands."""
    x = np.linspace(-1.0, 1.0, 50)
    design = np.column_stack([np.ones_like(x), x, x * x])
    assert robust.biweight_fit(design, 1 + 2 * x + 3 * x * x) == pytest.approx([1, 2, 3])


def test_residuals_at_rounding_leave_the_ordinary_fit_alone():
    """A surface met to the last bits: a scale of 1e-16 would weigh rounding as outliers and,
    with every weight at zero, give back zeros. The ordinary fit stands, bit for bit."""
    x = np.linspace(-1.0, 1.0, 32)
    design = np.column_stack([np.ones_like(x), x, x * x])
    y = 3.0 + np.random.default_rng(10).normal(0.0, 1e-15, x.size)
    ordinary = np.linalg.lstsq(design, y, rcond=None)[0]
    assert robust.biweight_fit(design, y).tolist() == ordinary.tolist()


def test_a_zero_scale_is_silent():
    """Qn zero (valori ripetuti, frame copiati): la soglia sarebbe la mediana, e tace."""
    assert relative_bounds([0.5] * 8 + [0.6, 0.7]) is None
