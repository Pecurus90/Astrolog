"""Mattone 2: cosa e' cambiato, senza aprire file (percorso, dimensione, data).
Radice muta: niente sparisce."""

import os
import sys
from pathlib import Path

from astrolog.pipeline.changes import add_root
from astrolog.pipeline.frames import scan_root

NOW = "2026-10-22T20:00:00+00:00"
LATER = "2026-10-23T20:00:00+00:00"


def _file(path: Path, size: int = 2880) -> Path:
    """Smallest FITS with END: read, skipped as not supported, its size and date kept."""
    path.parent.mkdir(parents=True, exist_ok=True)
    head = ("SIMPLE  =                    T".ljust(80) + "END".ljust(80)).encode("ascii")
    path.write_bytes(head + b" " * (size - len(head)))
    return path


def _link(target: Path, link: Path) -> None:
    """Folder link: junction on Windows (no privilege needed), symlink elsewhere."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def test_the_first_scan_finds_every_file_new(conn, tmp_path):
    _file(tmp_path / "a.fits")
    _file(tmp_path / "notte" / "b.fit")
    root = add_root(conn, tmp_path, NOW)
    changes = scan_root(conn, root, NOW).changes
    assert changes.new == ["a.fits", "notte/b.fit"]
    assert changes.to_read == ["a.fits", "notte/b.fit"]
    assert changes.unchanged == changes.changed == changes.gone == []


def test_a_second_scan_opens_nothing_when_nothing_changed(conn, tmp_path):
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    changes = scan_root(conn, root, LATER).changes
    assert changes.unchanged == ["a.fits"]
    assert changes.to_read == []


def test_a_file_with_another_size_or_date_is_changed(conn, tmp_path):
    a = _file(tmp_path / "a.fits")
    b = _file(tmp_path / "b.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _file(a, size=5760)
    stat = b.stat()
    os.utime(b, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    changes = scan_root(conn, root, LATER).changes
    assert changes.changed == ["a.fits", "b.fits"]
    assert changes.to_read == ["a.fits", "b.fits"]


def test_a_deleted_file_is_gone_and_remembered(conn, tmp_path):
    a = _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    a.unlink()
    assert scan_root(conn, root, LATER).changes.gone == ["a.fits"]
    row = conn.execute("SELECT state FROM pipeline_files WHERE rel_path = 'a.fits'").fetchone()
    assert row["state"] == "gone"
    assert scan_root(conn, root, LATER).changes.gone == []  # gone once, not every scan


def test_a_file_that_comes_back_is_read_again(conn, tmp_path):
    a = _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    a.unlink()
    scan_root(conn, root, NOW)
    _file(a)
    changes = scan_root(conn, root, LATER).changes
    assert changes.new == ["a.fits"]
    assert changes.to_read == ["a.fits"]


def test_an_unreachable_root_makes_nothing_gone(conn, tmp_path):
    archive = tmp_path / "nas"
    _file(archive / "a.fits")
    root = add_root(conn, archive, NOW)
    scan_root(conn, root, NOW)
    archive.rename(tmp_path / "spento")  # NAS off
    changes = scan_root(conn, root, LATER).changes
    assert changes.reachable is False
    assert changes.gone == []
    row = conn.execute("SELECT state FROM pipeline_files").fetchone()
    assert row["state"] == "present"


def test_an_unplugged_linked_disk_makes_nothing_gone(conn, tmp_path):
    """Sottocartella collegata ad altro disco: disco staccato, suoi file non spariti; altre
    cartelle giudicate lo stesso."""
    disk = tmp_path / "disco_esterno"
    _file(disk / "posa.fits")
    archive = tmp_path / "archivio"
    _file(archive / "qui.fits")
    _link(disk, archive / "acquisizioni")
    root = add_root(conn, archive, NOW)
    assert scan_root(conn, root, NOW).changes.new == ["acquisizioni/posa.fits", "qui.fits"]
    (disk / "posa.fits").unlink()
    disk.rmdir()  # unplugged
    (archive / "qui.fits").unlink()
    changes = scan_root(conn, root, LATER).changes
    assert changes.reachable is True
    assert changes.unreachable == ["acquisizioni"]
    assert changes.gone == ["qui.fits"]


def test_an_online_only_file_is_not_gone(conn, tmp_path, monkeypatch):
    """OneDrive o iCloud tolgono file dal disco, lasciano segnaposto: non sparito; tornato uguale,
    non si rilegge."""
    from astrolog.pipeline import walk

    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    monkeypatch.setattr(walk, "_online_only", lambda entry: True)
    assert scan_root(conn, root, LATER).changes.gone == []
    monkeypatch.setattr(walk, "_online_only", lambda entry: False)
    changes = scan_root(conn, root, LATER).changes
    assert changes.unchanged == ["a.fits"]
    assert changes.to_read == []


def test_a_file_whose_date_cannot_be_read_is_not_gone(conn, tmp_path, monkeypatch):
    """Errore passeggero NAS sul singolo file: file c'e', solo non guardato. Non si giudica, come
    cartella che non risponde."""
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    real = os.stat

    def flaky(path, *args, **kwargs):
        if str(path).endswith("a.fits"):
            raise PermissionError("errore passeggero (mock)")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", flaky)
    changes = scan_root(conn, root, LATER).changes
    assert changes.gone == []
    assert changes.unlooked == ["a.fits"]  # left out, and said
    monkeypatch.setattr(os, "stat", real)
    assert scan_root(conn, root, LATER).changes.unchanged == ["a.fits"]


def test_each_scan_leaves_its_receipt(conn, tmp_path):
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    scan_root(conn, root, LATER)
    rows = conn.execute(
        "SELECT reachable, new, changed, unchanged, gone FROM pipeline_scans ORDER BY id"
    ).fetchall()
    assert [tuple(r) for r in rows] == [(1, 1, 0, 0, 0), (1, 0, 0, 1, 0)]


def test_the_same_root_is_added_once(conn, tmp_path):
    assert add_root(conn, tmp_path, NOW) == add_root(conn, tmp_path, LATER)
