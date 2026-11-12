"""Le **prove** accanto a una domanda di *Da confermare* (`spine/frame_proofs.py`), lette su un
archivio fatto a mano: notti e ottica e camera dei frame di un gruppo, in una query sola.

* Un gruppo coi soli corredi e senza notte, o con la notte e senza corredo, ha la sua riga lo
  stesso: le due liste sono indipendenti.
* A pari frame i corredi vanno per nome dell'ottica, poi della camera; il pezzo che manca va
  prima di ogni nome, e l'ordine non dipende da quello delle notti.
"""

from astrolog.spine import frame_proofs
from astrolog.spine.frame_proofs import FrameRig
from conftest import LATER
from test_object_measures import _rig


def _frame(conn, group, night=None, rig=None):
    """`group` va in `object_raw`: il proprietario delle prove, senza bisogno di un oggetto."""
    n = conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]
    conn.execute(
        "INSERT INTO frames(frame_hash, image_type, object_raw, local_night, rig_id, header_json,"
        " created_at) VALUES (?, 'light', ?, ?, ?, '[]', ?)",
        (f"h{n}", group, night, rig, LATER),
    )


def _of(conn):
    return frame_proofs.of(conn, "f.object_raw")


def test_a_group_with_rigs_and_no_night_and_one_with_a_night_and_no_rig(conn):
    _frame(conn, "solo corredo", rig=_rig(conn, "Askar", "ATR"))
    _frame(conn, "solo notte", night="2024-10-31")
    proofs = _of(conn)
    assert proofs["solo corredo"].nights == []
    assert proofs["solo corredo"].rigs == [FrameRig(optics="Askar", camera="ATR", frames=1)]
    assert proofs["solo notte"].nights == ["2024-10-31"]
    assert proofs["solo notte"].rigs == []


def test_at_equal_frames_the_rigs_go_by_optics_then_camera_the_missing_piece_first(conn):
    """Le notti in ordine inverso ai nomi: la riga arriva prima per la notte, non per il nome."""
    _frame(conn, "ottiche", night="2024-01-01", rig=_rig(conn, "B ottica", "Y camera"))
    _frame(conn, "ottiche", night="2024-01-02", rig=_rig(conn, "A ottica", "Z camera"))
    _frame(conn, "camere", night="2024-01-01", rig=_rig(conn, "C ottica", "Cb"))
    _frame(conn, "camere", night="2024-01-02", rig=_rig(conn, None, "Cb"))
    _frame(conn, "camere", night="2024-01-03", rig=_rig(conn, "C2 ottica", "Ca"))
    _frame(conn, "camere", night="2024-01-04", rig=_rig(conn, "C2 ottica", None))
    _frame(conn, "camere", night="2024-01-05", rig=_rig(conn, "C ottica", "Ca"))
    proofs = _of(conn)
    assert [g.optics for g in proofs["ottiche"].rigs] == ["A ottica", "B ottica"]
    assert [(g.optics, g.camera) for g in proofs["camere"].rigs] == [
        (None, "Cb"),
        ("C ottica", "Ca"),
        ("C ottica", "Cb"),
        ("C2 ottica", None),
        ("C2 ottica", "Ca"),
    ]


def test_the_rig_most_used_comes_first(conn):
    poco, tanto = _rig(conn, "A ottica", "A camera"), _rig(conn, "Z ottica", "Z camera")
    _frame(conn, "gruppo", rig=poco)
    _frame(conn, "gruppo", rig=tanto)
    _frame(conn, "gruppo", night="2024-01-01", rig=tanto)
    assert _of(conn)["gruppo"].rigs == [
        FrameRig(optics="Z ottica", camera="Z camera", frames=2),
        FrameRig(optics="A ottica", camera="A camera", frames=1),
    ]
