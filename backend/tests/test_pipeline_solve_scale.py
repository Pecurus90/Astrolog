"""Mattone solve, ASTAP 8: una scala risolta lontana da quella dell'header si segnala e la soluzione
resta (D8, ADR 0036); una soluzione si dimentica a richiesta e la posa si rifa'."""

import pytest

from astrolog.pipeline.solve import forget
from conftest import nina_light
from test_pipeline_solve import _SKY, FakeAstap, _scanned, _solutions, _solve

_POINTING = _SKY[2:]


def _solved(conn, tmp_path, cards: tuple[str, ...]) -> dict:
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, cards)
    _solve(conn, _scanned(conn, nas), FakeAstap("solved.ini"), tmp_path)
    [row] = _solutions(conn)
    return row


def test_a_scale_close_to_the_header_raises_no_warning(conn, tmp_path):
    """3,76 um a 560 mm: 1,385"/px attesi, ASTAP ne misura 1,381."""
    row = _solved(conn, tmp_path, _SKY)
    assert row["expected_scale_arcsec_px"] == pytest.approx(3.76 / 560 * 206.264806, rel=1e-6)
    assert row["scale_disagrees"] == 0


def test_a_scale_far_from_the_header_is_said_and_the_solution_stays(conn, tmp_path):
    """Focale scritta doppia (riduttore nel profilo, o un falso positivo): avviso, cielo tenuto."""
    row = _solved(conn, tmp_path, ("FOCALLEN=               1120.0", _SKY[1], *_POINTING))
    assert row["outcome"] == "solved" and row["ra_deg"] is not None
    assert row["scale_disagrees"] == 1


def test_without_a_scale_in_the_header_there_is_nothing_to_compare(conn, tmp_path):
    row = _solved(conn, tmp_path, _POINTING)
    assert (row["expected_scale_arcsec_px"], row["scale_disagrees"]) == (None, None)


def test_a_forgotten_solution_is_tried_again_at_the_next_pass(conn, tmp_path):
    """Header corretto, catalogo nuovo: dimenticata, la posa torna da risolvere."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    [row] = _solutions(conn)
    assert forget(conn, row["frame_id"]) is True
    assert _solutions(conn) == []
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and len(_solutions(conn)) == 1


def test_forgetting_a_shot_never_solved_says_so(conn):
    assert forget(conn, 404) is False
