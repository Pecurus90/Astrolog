"""La porta sola fra le prove e la pipeline: chi riempie un DB di prova passa da `porta.fill`, cosi'
una fetta del passo 40 che toglie uno stadio vecchio cambia un file, non cento (passo 40.2)."""

import ast
from pathlib import Path

import porta
from conftest import add_folder, one

QUI = Path(__file__).parent

# Gli stadi della vecchia che riempiono un archivio: solo la porta li chiama per il conftest.
STADI = {"scan_once", "normalize_frames", "identify_frames"}


def _called(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    }


def test_the_conftest_fills_an_archive_only_through_the_door():
    assert _called(QUI / "conftest.py") & STADI == set()
    assert _called(QUI / "porta.py") >= STADI


def test_each_depth_stops_where_it_says(conn, tmp_path):
    from synthetic import build_archive

    build_archive(tmp_path / "lib")
    done = "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'done'"
    porta.fill(conn, add_folder(conn, tmp_path / "lib"), porta.Upto.SCANNED)
    assert one(conn, "SELECT COUNT(*) FROM frames") > 0
    assert one(conn, done, ("normalize",)) == 0
    porta.fill(conn, None, porta.Upto.NORMALIZED)
    assert one(conn, done, ("normalize",)) > 0
    assert one(conn, done, ("identify",)) == 0
    porta.fill(conn, None, porta.Upto.IDENTIFIED)
    assert one(conn, done, ("identify",)) > 0
