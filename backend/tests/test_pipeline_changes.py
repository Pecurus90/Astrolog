"""Mattone 2 della pipeline nuova: cosa e' cambiato dall'ultima scansione, senza aprire i file.
Percorso, dimensione e data; una cartella che non risponde non fa sparire i suoi file."""

import os
import sys
from pathlib import Path

from astrolog.pipeline.changes import add_root, sync

NOW = "2026-10-22T20:00:00+00:00"
LATER = "2026-10-23T20:00:00+00:00"


def _file(path: Path, size: int = 2880) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b" " * size)
    return path


def _link(target: Path, link: Path) -> None:
    """A folder link on disk: a junction on Windows (no privilege needed), a symlink elsewhere."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def test_the_first_scan_finds_every_file_new(conn, tmp_path):
    _file(tmp_path / "a.fits")
    _file(tmp_path / "notte" / "b.fit")
    root = add_root(conn, tmp_path, NOW)
    changes = sync(conn, root, NOW)
    assert changes.new == ["a.fits", "notte/b.fit"]
    assert changes.to_read == ["a.fits", "notte/b.fit"]
    assert changes.unchanged == changes.changed == changes.gone == []


def test_a_second_scan_opens_nothing_when_nothing_changed(conn, tmp_path):
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    changes = sync(conn, root, LATER)
    assert changes.unchanged == ["a.fits"]
    assert changes.to_read == []


def test_a_file_with_another_size_or_date_is_changed(conn, tmp_path):
    a = _file(tmp_path / "a.fits")
    b = _file(tmp_path / "b.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    _file(a, size=5760)
    stat = b.stat()
    os.utime(b, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    changes = sync(conn, root, LATER)
    assert changes.changed == ["a.fits", "b.fits"]
    assert changes.to_read == ["a.fits", "b.fits"]


def test_a_deleted_file_is_gone_and_remembered(conn, tmp_path):
    a = _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    a.unlink()
    assert sync(conn, root, LATER).gone == ["a.fits"]
    row = conn.execute("SELECT state FROM pipeline_files WHERE rel_path = 'a.fits'").fetchone()
    assert row["state"] == "gone"
    assert sync(conn, root, LATER).gone == []  # gone once, not at every scan


def test_a_file_that_comes_back_is_read_again(conn, tmp_path):
    a = _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    a.unlink()
    sync(conn, root, NOW)
    _file(a)
    changes = sync(conn, root, LATER)
    assert changes.new == ["a.fits"]
    assert changes.to_read == ["a.fits"]


def test_an_unreachable_root_makes_nothing_gone(conn, tmp_path):
    archive = tmp_path / "nas"
    _file(archive / "a.fits")
    root = add_root(conn, archive, NOW)
    sync(conn, root, NOW)
    archive.rename(tmp_path / "spento")  # the NAS is off
    changes = sync(conn, root, LATER)
    assert changes.reachable is False
    assert changes.gone == []
    row = conn.execute("SELECT state FROM pipeline_files").fetchone()
    assert row["state"] == "present"


def test_an_unplugged_linked_disk_makes_nothing_gone(conn, tmp_path):
    """La cartella principale e' un collegamento a un altro disco: staccato il disco, i suoi file
    non sono spariti, e quelli delle altre cartelle si giudicano lo stesso."""
    disk = tmp_path / "disco_esterno"
    _file(disk / "posa.fits")
    archive = tmp_path / "archivio"
    _file(archive / "qui.fits")
    _link(disk, archive / "acquisizioni")
    root = add_root(conn, archive, NOW)
    assert sync(conn, root, NOW).new == ["acquisizioni/posa.fits", "qui.fits"]
    (disk / "posa.fits").unlink()
    disk.rmdir()  # unplugged
    (archive / "qui.fits").unlink()
    changes = sync(conn, root, LATER)
    assert changes.reachable is True
    assert changes.unreachable == ["acquisizioni"]
    assert changes.gone == ["qui.fits"]


def test_an_online_only_file_is_not_gone(conn, tmp_path, monkeypatch):
    """OneDrive o iCloud tolgono il file dal disco e lasciano il segnaposto: non e' sparito, e
    quando torna uguale non si rilegge."""
    from astrolog.pipeline import walk

    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    monkeypatch.setattr(walk, "_online_only", lambda entry: True)
    assert sync(conn, root, LATER).gone == []
    monkeypatch.setattr(walk, "_online_only", lambda entry: False)
    changes = sync(conn, root, LATER)
    assert changes.unchanged == ["a.fits"]
    assert changes.to_read == []


def test_a_file_whose_date_cannot_be_read_is_not_gone(conn, tmp_path, monkeypatch):
    """Un errore passeggero di un NAS sul singolo file: il file c'e', solo non si e' potuto
    guardare. Non si giudica, come una cartella che non risponde."""
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    real = os.stat

    def flaky(path, *args, **kwargs):
        if str(path).endswith("a.fits"):
            raise PermissionError("errore passeggero (mock)")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", flaky)
    changes = sync(conn, root, LATER)
    assert changes.gone == []
    assert changes.unlooked == ["a.fits"]  # left out, and said
    monkeypatch.setattr(os, "stat", real)
    assert sync(conn, root, LATER).unchanged == ["a.fits"]


def test_each_scan_leaves_its_receipt(conn, tmp_path):
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    sync(conn, root, NOW)
    sync(conn, root, LATER)
    rows = conn.execute(
        "SELECT reachable, new, changed, unchanged, gone FROM pipeline_scans ORDER BY id"
    ).fetchall()
    assert [tuple(r) for r in rows] == [(1, 1, 0, 0, 0), (1, 0, 0, 1, 0)]


def test_the_same_root_is_added_once(conn, tmp_path):
    assert add_root(conn, tmp_path, NOW) == add_root(conn, tmp_path, LATER)
