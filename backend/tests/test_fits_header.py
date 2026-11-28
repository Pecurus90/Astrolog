"""Cio' che resta di `fits/`: il WCS che ASTAP scrive (lo legge `astap.py`), il marchio di
calibrazione e il testo di una card salvata (li legge `spine/rewrite.py` da `frames.header_json`).
I campi del frame li legge la scheda della pipeline (`test_pipeline_card.py`)."""

import pytest

from astrolog.fits.frame_type import says_calibrated
from astrolog.fits.header_keys import text
from astrolog.fits.header_wcs import solved, wcs_rotation_deg, wcs_scale


def test_a_calibrated_frame_is_still_a_frame():
    """`CALSTAT` dice **calibrato**, non **sommato**: fa un altro mestiere, e' il marchio di
    riscrittura, che vale solo fra due gemelli e non fa sparire niente."""
    assert says_calibrated({"CALSTAT": "BDF"})
    assert not says_calibrated({"CALSTAT": "uncalibrated"})
    assert not says_calibrated({"CALIBRAT": "F"})  # il falso FITS, non la lettera del flat


def test_solved_means_a_real_wcs():
    """Un `CRVAL1` nudo non e' un cielo misurato: senza questa distinzione una coordinata di
    puntamento passerebbe per una soluzione. Lo chiede il solver sull'esito di ASTAP."""
    for hdr in ({"WCSAXES": 2}, {"CD1_1": 0.0002}, {"PLTSOLVD": True}, {"PLTSOLVD": "T"}):
        assert solved(hdr) is True
    assert solved({"CRVAL1": 180.0, "CRVAL2": 0.0}) is False


def test_the_scale_comes_from_the_cd_matrix_or_from_cdelt():
    """La scala dalla matrice: la legge il solver sull'esito di ASTAP. Quella da pixel e focale
    e' un'altra cosa e vive in `units` (la prova `test_solve_field_from_the_header`)."""
    cd11, cd21 = 0.000402, 0.0000115
    header = {"CD1_1": cd11, "CD1_2": 0.0, "CD2_1": cd21, "CD2_2": cd11}
    assert wcs_scale(header) == pytest.approx((cd11**2 + cd21**2) ** 0.5 * 3600.0, abs=1e-4)
    assert wcs_scale({"CDELT1": -0.000402}) == pytest.approx(0.000402 * 3600.0, abs=1e-4)
    assert wcs_scale({"PIXSIZE1": 3.76}) is None


def test_rotation_is_crota2_from_cd_matrix():
    """La rotazione la legge il solver sull'esito di ASTAP. `OBJCTROT` non si legge mai: sui
    frame veri ha il segno opposto e vale zero come sentinella su meta' di essi."""
    header = {"CD1_1": 0.0, "CD1_2": -0.0004, "CD2_1": 0.0004, "CD2_2": 0.0}
    assert wcs_rotation_deg(header) == pytest.approx(90.0)
    assert wcs_rotation_deg({"CROTA2": -10.0}) == pytest.approx(350.0)
    assert wcs_rotation_deg({"OBJCTROT": 45.0}) is None
    # `CD1_2` assente si legge 0 (WCS Paper I): la matrice c'e' e l'angolo e' zero, non ignoto
    assert wcs_rotation_deg({"CD1_1": 0.0004, "CD2_2": 0.0004}) == 0.0
    # matrice degenere (CD1_2 e CD2_2 entrambe nulle): l'angolo resta ignoto, e si ripiega su
    # CROTA2 invece di dichiarare uno zero che non e' stato misurato
    assert wcs_rotation_deg({"CD1_1": 0.0004, "CD1_2": 0.0, "CD2_2": 0.0, "CROTA2": 33.0}) == 33.0
    assert wcs_rotation_deg({"CROTA1": -10.0}) == pytest.approx(350.0)  # la grafia secondaria


def test_an_apostrophe_is_part_of_the_name():
    """Togliere **tutti** gli apici mangiava le lettere dei nomi veri, e in archivio finiva
    `Barnards Loop`: si toglie solo la coppia che avvolge il valore."""
    for nome in ("Barnard's Loop", "Hind's Variable Nebula", "Baade's Window"):
        assert text(nome) == nome
    assert text("'M 31'") == "M 31"
    assert text("''") is None
