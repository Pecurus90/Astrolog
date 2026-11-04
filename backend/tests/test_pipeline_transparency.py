"""Series transparency as Image Analysis measures it: brightness ladder per frame,
relative extinction, cloud extinction from Bouguer's law. software-ok"""

import math

import numpy as np
import pytest

from astrolog.pipeline.transparency import (
    STARTS,
    SeriesFrame,
    brightness_ladder,
    transparency,
)

# Abell 2151 L, 29 frames: his RelativeExtinction, Airmass, CloudExtinction
_AIRMASS = [1.208776, 1.203649, 1.198726, 1.179418, 1.175467, 1.171687, 1.157249, 1.154422,
            1.151716, 1.142182, 1.14033, 1.138635, 1.133109, 1.132192, 1.131421, 1.129813,
            1.129837, 1.130023, 1.135393, 1.136719, 1.138173, 1.146386, 1.148731, 1.151227,
            1.164368, 1.167757, 1.171345, 1.188721, 1.193224]  # fmt: skip
_RELATIVE = [0.047629, 0.045565, 0.060678, 0.046302, 0.038903, 0.053855, 0.015888, 0.046153,
             0.040459, 0.040285, 0.042137, 0.03764, 0.032935, 0.03312, 0.032846, 0.036131,
             0.031473, 0.045093, 0.010702, 0.0, 0.01452, 0.02374, 0.023045, 0.012114, 0.003163,
             0.005782, 0.010822, 0.022146, 0.024383]  # fmt: skip
_CLOUD = [0.00998, 0.008704, 0.024573, 0.013163, 0.006371, 0.021904, -0.013845, 0.016854,
          0.011576, 0.012866, 0.015004, 0.010766, 0.006911, 0.007236, 0.00708, 0.010612, 0.005952,
          0.019542, -0.015673, -0.026579, -0.012282, -0.004324, -0.00538, -0.016694, -0.027663,
          -0.025565, -0.021077, -0.012422, -0.010877]  # fmt: skip


def _frame(
    log_flux: float, airmass: float | None = 1.0, exposure: float | None = 60.0
) -> SeriesFrame:
    """A frame whose window at rank 1 holds `log_flux`, the other windows empty."""
    return SeriesFrame(ladder={1: log_flux}, exposure_s=exposure, airmass=airmass)


def test_the_ladder_is_the_median_log_flux_of_fifty_ranks_by_decreasing_flux() -> None:
    flux = 10 ** np.linspace(6, 2, 500)  # rank 1 brightest
    ladder = brightness_ladder(flux, np.zeros(500, dtype=bool))
    assert list(ladder) == [1, 51, 101, 201, 401]  # 801 needs 850 stars
    assert ladder[1] == pytest.approx(np.median(np.log10(flux[:50])))
    assert ladder[401] == pytest.approx(np.median(np.log10(flux[400:450])))


def test_the_windows_start_at_one_fifty_one_and_double() -> None:
    """ImageAnalysis par. 2.1.7: ranks 1, 51, 101, 201, 401, ..., 6401. software-ok"""
    assert STARTS == (1, 51, 101, 201, 401, 801, 1601, 3201, 6401)


def test_saturated_stars_count_as_brighter_than_any_of_their_window() -> None:
    """Their flux is too low: the median stays the one of the same stars unsaturated."""
    flux = 10 ** np.linspace(6, 2, 100)
    clear = brightness_ladder(flux, np.zeros(100, dtype=bool))[1]
    clipped = flux.copy()
    saturated = np.zeros(100, dtype=bool)
    saturated[:15] = True
    clipped[:15] = flux[40]  # clipped cores measure like fainter stars, and rank among them
    assert brightness_ladder(clipped, saturated)[1] == pytest.approx(clear, abs=1e-12)


def test_a_window_forty_percent_saturated_is_not_available() -> None:
    flux = 10 ** np.linspace(6, 2, 100)
    saturated = np.zeros(100, dtype=bool)
    saturated[:19] = True
    assert 1 in brightness_ladder(flux, saturated)
    saturated[:20] = True
    assert 1 not in brightness_ladder(flux, saturated)


def test_stars_without_a_flux_take_no_rank() -> None:
    flux = 10 ** np.linspace(6, 2, 60)
    holes = flux.copy()
    holes[[3, 7]] = np.nan
    assert 51 not in brightness_ladder(holes, np.zeros(60, dtype=bool))
    assert brightness_ladder(holes, np.zeros(60, dtype=bool))[1] == pytest.approx(
        np.median(np.log10(np.delete(flux, [3, 7])[:50]))
    )


def test_the_relative_extinction_is_zero_on_the_most_transparent_frame() -> None:
    """ImageAnalysis eq. 30: -2.5 l_i less its smallest over the series. software-ok"""
    frames = [_frame(5.0), _frame(5.0 + math.log10(0.8)), _frame(5.0 + math.log10(0.5))]
    found = transparency(frames)
    assert found.window == 1
    assert [f.relative_mag for f in found.frames] == pytest.approx(
        [0.0, -2.5 * math.log10(0.8), -2.5 * math.log10(0.5)]
    )


def test_the_flux_is_per_second_when_every_frame_has_its_exposure() -> None:
    frames = [_frame(5.0, exposure=60.0), _frame(5.0 + math.log10(2), exposure=120.0)]
    assert [f.relative_mag for f in transparency(frames).frames] == pytest.approx([0.0, 0.0])
    frames[0] = _frame(5.0, exposure=None)  # one unknown: fluxes as measured
    assert transparency(frames).frames[0].relative_mag == pytest.approx(2.5 * math.log10(2))


def test_the_window_is_the_one_most_frames_have_the_brightest_on_a_tie() -> None:
    both = SeriesFrame(ladder={51: 4.0, 101: 3.5}, exposure_s=60.0, airmass=1.0)
    deep = SeriesFrame(ladder={101: 3.4}, exposure_s=60.0, airmass=1.0)
    assert transparency([both, both]).window == 51
    found = transparency([both, deep, deep])
    assert found.window == 101
    assert [f.relative_mag for f in found.frames] == pytest.approx([0.0, 0.25, 0.25])


def test_a_frame_without_the_window_has_no_extinction() -> None:
    frames = [_frame(5.0), _frame(4.9), SeriesFrame(ladder={}, exposure_s=60.0, airmass=1.0)]
    assert transparency(frames).frames[2].relative_mag is None
    assert transparency([]).window is None


def test_the_cloud_extinction_gives_back_the_programs_own_on_abell_2151() -> None:
    """His Bouguer fit: biweight on the positive residuals only, MAD scale. software-ok"""
    frames = [SeriesFrame(ladder={1: -value / 2.5}, exposure_s=180.0, airmass=x)
              for value, x in zip(_RELATIVE, _AIRMASS, strict=True)]  # fmt: skip
    found = transparency(frames)
    assert [f.relative_mag for f in found.frames] == pytest.approx(_RELATIVE, abs=1e-12)
    assert [f.cloud_mag for f in found.frames] == pytest.approx(_CLOUD, abs=1e-6)
    assert found.coefficient == pytest.approx(0.153625, abs=1e-5)


def test_clouds_only_add_extinction_and_do_not_tilt_the_line() -> None:
    airmass = np.linspace(1.0, 2.0, 20)
    clear = 0.25 * airmass
    cloudy = clear.copy()
    cloudy[[4, 9, 15]] += [0.5, 1.0, 0.8]
    frames = [_frame(-m / 2.5, x) for m, x in zip(cloudy, airmass, strict=True)]
    found = transparency(frames)
    assert found.coefficient == pytest.approx(0.25, abs=1e-6)
    clouds = [f.cloud_mag for f in found.frames]
    assert None not in clouds
    values = np.array(clouds, dtype=float)
    assert values[9] == pytest.approx(1.0, abs=1e-6)
    assert np.abs(np.delete(values, [4, 9, 15])).max() < 1e-6


def test_a_short_span_of_air_masses_fits_only_the_constant() -> None:
    """Under 0.05 of air mass the cloud extinction is the relative one less a constant."""
    frames = [_frame(-m / 2.5, 1.0 + 0.002 * i) for i, m in enumerate([0.1, 0.12, 0.1, 0.4, 0.11])]
    found = transparency(frames)
    assert found.coefficient is None
    relative = np.array([f.relative_mag for f in found.frames], dtype=float)
    clouds = np.array([f.cloud_mag for f in found.frames], dtype=float)
    assert not np.isnan(clouds).any()
    assert np.ptp(relative - clouds) == pytest.approx(0.0, abs=1e-12)
    assert clouds[3] > 0.25


def test_under_five_frames_with_an_air_mass_there_is_no_cloud_extinction() -> None:
    frames = [_frame(5.0 - 0.1 * i, 1.0 + 0.1 * i) for i in range(4)] + [_frame(4.0, None)]
    found = transparency(frames)
    assert all(f.cloud_mag is None for f in found.frames)
    assert found.frames[4].relative_mag is not None
