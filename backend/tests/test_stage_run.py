"""La guardia della posa e la ricevuta, scritte una volta per i quattro stadi che lavorano posa per
posa (`spine/stage_run.py`)."""

import pytest

from astrolog.spine import group, identify, normalize, solve
from astrolog.spine.stage_run import frame_safely
from astrolog.spine.stages import set_status


def _a_frame(conn):
    return conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('h', 'light', '[]', 'now')"
    ).lastrowid


def test_a_broken_pose_is_marked_failed_and_the_round_goes_on(conn):
    frame_id = _a_frame(conn)
    set_status(conn, frame_id, "identify", "pending")
    counts, errors = {"errors": 0}, []

    def broken():
        raise RuntimeError("disco che sparisce")

    assert frame_safely(conn, "identify", frame_id, broken, counts, errors) is None
    row = conn.execute(
        "SELECT status, reason FROM frame_stages WHERE frame_id = ? AND stage = 'identify'",
        (frame_id,),
    ).fetchone()
    assert tuple(row) == ("failed", "internal_error")
    assert counts == {"errors": 1}
    assert errors == [{"frame_id": frame_id, "reason": "RuntimeError: disco che sparisce"}]


def test_a_pose_that_works_returns_what_the_stage_said(conn):
    counts, errors = {"errors": 0}, []
    assert frame_safely(conn, "solve", 1, lambda: "fermati", counts, errors) == "fermati"
    assert counts == {"errors": 0} and errors == []


@pytest.mark.parametrize(
    "run",
    [
        normalize.normalize_frames,
        lambda conn: solve.solve_frames(conn, exe=None),
        identify.identify_frames,
        group.group_frames,
    ],
)
def test_every_stage_closes_with_the_same_receipt(conn, run):
    """Il worker e la pagina leggono la ricevuta di ogni stadio allo stesso modo."""
    last = list(run(conn))[-1]
    assert {"done", "status", "reason", "total", "errors_detail"} <= set(last)
    assert (last["done"], last["status"], last["reason"]) == (True, "ok", None)
