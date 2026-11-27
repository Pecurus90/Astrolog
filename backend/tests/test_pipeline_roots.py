"""Una radice, una riga per le due pipeline (passo 40.3): si ritira e torna, si sposta, si
sostituisce, torna da un backup. Casi trovati dal verificatore del piano."""

import json
import os

import pytest

from astrolog.db.transaction import transaction
from astrolog.pipeline import roots
from astrolog.pipeline.scan import scan_root
from conftest import LATER, NOW, nina_light


def _files(conn):
    return [
        (r["root_id"], r["rel_path"])
        for r in conn.execute(
            "SELECT root_id, rel_path FROM pipeline_files WHERE state = 'present' ORDER BY id"
        )
    ]


def test_a_retired_outer_root_comes_back_over_an_active_inner_one(conn, tmp_path):
    """O ritirata con b/x.fits; I = O/b aggiunta dopo prende x.fits (resa da O); O torna e
    sostituisce I: un file presente una volta sola, mai un IntegrityError."""
    outer_path = tmp_path / "O"
    nina_light(outer_path / "b" / "x.fits", 1)
    outer = roots.add_root(conn, outer_path, NOW)
    scan_root(conn, outer, NOW)
    roots.retire(conn, outer, NOW)

    inner = roots.add_root(conn, outer_path / "b", NOW)
    assert _files(conn) == [(inner, "x.fits")]
    scan_root(conn, inner, LATER)

    with transaction(conn):
        assert roots.register(conn, outer_path, LATER) == outer
        roots.absorb(conn, outer, LATER)
        roots.retire(conn, outer, None)

    assert _files(conn) == [(outer, "b/x.fits")]
    retired = conn.execute("SELECT id FROM pipeline_roots WHERE retired_at IS NOT NULL").fetchall()
    assert [r[0] for r in retired] == [inner]


def test_a_move_onto_another_roots_path_is_refused_with_its_id(conn, tmp_path):
    """Spostare su un percorso che e' gia' di un'altra riga, anche ritirata: rifiutato col suo id,
    mai due righe per una cartella."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    a = roots.add_root(conn, tmp_path / "a", NOW)
    b = roots.add_root(conn, tmp_path / "b", NOW)
    roots.retire(conn, b, NOW)
    with pytest.raises(roots.RootTakenError) as taken:
        roots.move(conn, a, tmp_path / "b")
    assert taken.value.other_id == b


def test_a_moved_root_keeps_its_id_files_and_takes_the_new_keys(conn, tmp_path):
    nina_light(tmp_path / "new" / "x.fits", 1)
    root = roots.add_root(conn, tmp_path / "old", NOW)
    roots.move(conn, root, tmp_path / "new")
    row = conn.execute("SELECT * FROM pipeline_roots").fetchone()
    assert (row["id"], row["path"]) == (root, str(tmp_path / "new"))
    assert row["device"] is not None
    assert roots.add_root(conn, tmp_path / "new", LATER) == root


def test_a_backup_brings_back_a_retired_root_inside_an_active_one_and_a_foreign_path(
    conn, tmp_path
):
    """Righe di un database solo: nessuna domanda di sovrapposizione. Un percorso di un altro
    sistema torna com'e' scritto, per lo spostamento che lo riconosce."""
    outer = roots.restore(conn, roots.Declared(str(tmp_path / "A"), "archivio", None, "[]"), NOW)
    inner = roots.restore(
        conn, roots.Declared(str(tmp_path / "A" / "M31"), None, "ieri", "[]"), NOW
    )
    foreign = "Z:/Astro" if not str(tmp_path).startswith("Z:") else "Y:/Astro"
    elsewhere = roots.restore(
        conn, roots.Declared(foreign, None, None, json.dumps([["a.fits", "h"]])), NOW
    )
    rows = conn.execute("SELECT id, name, retired_at FROM pipeline_roots ORDER BY id").fetchall()
    assert [tuple(r) for r in rows] == [
        (outer, "archivio", None),
        (inner, None, "ieri"),
        (elsewhere, None, None),
    ]
    # a second restore updates, never doubles
    again = roots.Declared(str(tmp_path / "A" / "M31"), "M31", None, "[]")
    assert roots.restore(conn, again, LATER) == inner
    assert conn.execute("SELECT COUNT(*) FROM pipeline_roots").fetchone()[0] == 3


def test_a_backup_path_of_another_system_comes_back_as_written(conn):
    """Un backup del NAS letto su Windows: `/volume1/photo` non diventa `C:\\volume1\\photo`, che
    non e' mai esistito; e il contrario sul NAS (revisore 26/11)."""
    foreign = "/volume1/photo" if os.name == "nt" else "Z:\\Astro"
    roots.restore(conn, roots.Declared(foreign, None, None, "[]"), NOW)
    assert conn.execute("SELECT path FROM pipeline_roots").fetchone()[0] == foreign


def test_the_same_folder_written_another_way_finds_its_retired_row(conn, tmp_path):
    (tmp_path / "Archive").mkdir()
    root = roots.add_root(conn, tmp_path / "Archive", NOW)
    roots.retire(conn, root, NOW)
    assert roots.add_root(conn, str(tmp_path / "Archive") + "/", LATER) == root


def _like_a_mac(monkeypatch, tmp_path):
    """Disco che ignora le maiuscole ma normcase che le tiene, come APFS (Nightly 45943367710)."""
    if not roots._ignores_case(str(tmp_path)):
        pytest.skip("disco che distingue le maiuscole")
    monkeypatch.setattr(os.path, "normcase", lambda p: p)


def test_a_path_not_there_yet_is_inside_the_root_that_holds_it(conn, tmp_path, monkeypatch):
    """Il disco si chiede alla cartella piu' vicina che c'e'.
    `M31/x`, non ancora creata, sta in M31."""
    _like_a_mac(monkeypatch, tmp_path)
    inner = tmp_path / "M31"
    inner.mkdir()
    root = roots.add_root(conn, inner, NOW)
    assert roots.holder(conn, str(inner / "x")) == roots.Root(root, str(inner))


def test_a_test_folder_comes_back_from_a_backup_on_its_own_row(conn, tmp_path, monkeypatch):
    """La cartella dei test ha le chiavi dell'app: l'import la ritrova, niente seconda riga."""
    from conftest import add_folder

    _like_a_mac(monkeypatch, tmp_path)
    folder = add_folder(conn, tmp_path)
    assert roots.restore(conn, roots.Declared(str(tmp_path), None, None, "[]"), NOW) == folder
