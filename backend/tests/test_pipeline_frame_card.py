"""La scheda di una posa con copie e' quella del file arrivato per primo (docs/domini/misure.md).
Prima: ogni lettore sceglieva il suo file (misurato, primo per percorso, tutti)."""

import shutil
import sqlite3

from astrolog.pipeline.roots import add_root
from astrolog.pipeline.scan import scan_root
from astrolog.pipeline.sqm_measure import biases
from conftest import LATER, NOW, THEN, nina_light
from test_pipeline_scan import _touch_later

M33 = ("OBJECT  = 'M 33'",)
CAMERA = ("INSTRUME= 'ZWO ASI2600MM Pro'",)


def _cards(conn: sqlite3.Connection) -> dict[int, str | None]:
    """Frame -> path of the file whose card stands for it."""
    return {
        row["id"]: row["rel_path"]
        for row in conn.execute(
            "SELECT fr.id, f.rel_path FROM pipeline_frames AS fr"
            " LEFT JOIN pipeline_files AS f ON f.id = fr.card_file_id"
        )
    }


def _only(conn: sqlite3.Connection) -> str | None:
    cards = _cards(conn)
    assert len(cards) == 1, cards
    return next(iter(cards.values()))


def _measured(conn: sqlite3.Connection, rel: str) -> None:
    """A measure row read from `rel`, as measure.py would write it."""
    conn.execute(
        "INSERT INTO pipeline_measures (frame_id, file_id, outcome, measured_at)"
        " SELECT frame_id, id, 'not_supported', ? FROM pipeline_files"
        " WHERE rel_path = ? AND state = 'present'",
        (NOW, rel),
    )


def _measure_file(conn: sqlite3.Connection) -> str | None:
    rows = conn.execute(
        "SELECT f.rel_path FROM pipeline_measures AS m"
        " LEFT JOIN pipeline_files AS f ON f.id = m.file_id"
    ).fetchall()
    return rows[0]["rel_path"] if rows else "no measure"


def test_a_copy_that_arrives_later_does_not_change_the_card(conn, tmp_path):
    """La copia arriva dopo e il suo percorso viene prima nell'alfabeto: vale l'originale."""
    nina_light(tmp_path / "b.fits", 5)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "a-backup" / "b.fits", 5, M33)
    scan_root(conn, root, LATER)
    assert _only(conn) == "b.fits"


def test_two_copies_seen_in_the_same_scan_take_the_first_read(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 5)
    nina_light(tmp_path / "b.fits", 5, M33)
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _only(conn) == "a.fits"


def test_when_the_original_goes_its_copy_takes_the_card(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 5)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "b.fits", 5, M33)
    scan_root(conn, root, LATER)
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, THEN)
    assert _only(conn) == "b.fits"


def test_an_original_rewritten_by_another_program_leaves_the_card_to_its_copy(conn, tmp_path):
    """Il file lascia la posa (header tolto): la scheda non resta su un file senza scheda."""
    nina_light(tmp_path / "a.fits", 5)
    nina_light(tmp_path / "b.fits", 5, M33)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "a.fits", 5, ("PROGRAM = 'Editor 1.9.3'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _only(conn) == "b.fits"


def test_an_original_back_after_its_copy_took_the_card_does_not_take_it_back(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 5)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "b.fits", 5, M33)
    scan_root(conn, root, LATER)
    moved = tmp_path.parent / f"{tmp_path.name}-aside.fits"
    (tmp_path / "a.fits").rename(moved)
    scan_root(conn, root, THEN)
    moved.rename(tmp_path / "a.fits")
    scan_root(conn, root, "2026-01-01T00:00:00+00:00")
    assert _only(conn) == "b.fits"


def test_a_moved_original_keeps_the_card_and_its_measure(conn, tmp_path):
    """Spostato non e' una copia: la scheda e la misura seguono il percorso nuovo."""
    nina_light(tmp_path / "a.fits", 5)
    nina_light(tmp_path / "b.fits", 5, M33)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _measured(conn, "a.fits")
    (tmp_path / "night").mkdir()
    (tmp_path / "a.fits").rename(tmp_path / "night" / "a.fits")
    scan_root(conn, root, LATER)
    assert _only(conn) == "night/a.fits"
    assert _measure_file(conn) == "night/a.fits"


def test_a_new_card_sends_the_shot_to_be_measured_again(conn, tmp_path):
    """Misura, cielo e SQM fatti coi fatti della scheda vecchia: si rifanno con la nuova."""
    nina_light(tmp_path / "a.fits", 5)
    nina_light(tmp_path / "b.fits", 5, M33)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _measured(conn, "a.fits")
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, LATER)
    assert _measure_file(conn) == "no measure"


def test_a_card_that_stays_keeps_the_measure(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 5)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _measured(conn, "a.fits")
    nina_light(tmp_path / "b.fits", 5, M33)
    scan_root(conn, root, LATER)
    assert _measure_file(conn) == "a.fits"


def test_an_fpack_copy_stands_for_the_shot_only_without_a_plain_file(conn, tmp_path):
    """Il .fz non si misura e fpack copia l'header: il file semplice arrivato dopo prende posto."""
    nina_light(tmp_path / "a.fits", 5)
    shutil.move(tmp_path / "a.fits", tmp_path / "a.fits.fz")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    assert _only(conn) == "a.fits.fz"
    nina_light(tmp_path / "a.fits", 5)
    scan_root(conn, root, LATER)
    assert _only(conn) == "a.fits"


def test_a_shot_without_files_left_has_no_card(conn, tmp_path):
    """Sparito tiene il frame (lo spostato si riconosce), non la scheda."""
    nina_light(tmp_path / "a.fits", 5)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, LATER)
    assert _only(conn) is None


def test_the_camera_offsets_count_shots_not_their_copies(conn, tmp_path):
    """Prima: due copie della stessa posa contavano due frame, e i file spariti restavano."""
    nina_light(tmp_path / "a.fits", 5, CAMERA)
    nina_light(tmp_path / "b.fits", 5, (*CAMERA, *M33))
    nina_light(tmp_path / "gone.fits", 6, CAMERA)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "gone.fits").unlink()
    scan_root(conn, root, LATER)
    assert [(r["camera"], r["frames"]) for r in biases(conn)] == [("ZWO ASI2600MM Pro", 1)]
