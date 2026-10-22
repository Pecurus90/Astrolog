"""Mattone 2: cosa e' cambiato, senza aprire file (percorso, dimensione, data).
Radice muta: niente sparisce."""

import json
import os
import shutil
import stat
import string
import sys
from pathlib import Path

import pytest

from astrolog.pipeline.changes import RootOverlapError, add_root
from astrolog.pipeline.scan import scan_root
from conftest import LATER, NOW, folder_link, nina_light


def _file(path: Path, size: int = 2880) -> Path:
    """Smallest FITS with END: read, skipped as not supported, its size and date kept."""
    path.parent.mkdir(parents=True, exist_ok=True)
    head = ("SIMPLE  =                    T".ljust(80) + "END".ljust(80)).encode("ascii")
    path.write_bytes(head + b" " * (size - len(head)))
    return path


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
    folder_link(disk, archive / "acquisizioni")
    root = add_root(conn, archive, NOW)
    assert scan_root(conn, root, NOW).changes.new == ["acquisizioni/posa.fits", "qui.fits"]
    (disk / "posa.fits").unlink()
    disk.rmdir()  # unplugged
    (archive / "qui.fits").unlink()
    changes = scan_root(conn, root, LATER).changes
    assert changes.reachable is True
    assert changes.unreachable == ["acquisizioni"]
    assert changes.gone == ["qui.fits"]


@pytest.mark.skipif(sys.platform != "win32", reason="hidden attribute: Windows")
def test_a_folder_made_hidden_after_a_scan_is_not_judged(conn, tmp_path):
    """Nascosta dall'utente (attributo): non letta, le sue pose restano com'erano."""
    import ctypes

    nas = tmp_path / "nas"
    _file(nas / "notte" / "a.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    assert ctypes.windll.kernel32.SetFileAttributesW(str(nas / "notte"), stat.FILE_ATTRIBUTE_HIDDEN)
    changes = scan_root(conn, root, LATER).changes
    assert (changes.hidden, changes.gone) == (["notte"], [])
    row = conn.execute("SELECT state FROM pipeline_files").fetchone()
    assert row["state"] == "present"


def test_a_file_moved_to_the_bin_is_gone(conn, tmp_path):
    """Cestino: la posa cancellata dall'utente sparisce, anche se il cestino sta nella radice."""
    nas = tmp_path / "nas"
    a = _file(nas / "notte" / "a.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    (nas / ".Trashes").mkdir()
    a.rename(nas / ".Trashes" / "a.fits")
    changes = scan_root(conn, root, LATER).changes
    assert (changes.hidden, changes.gone) == ([".Trashes"], ["notte/a.fits"])


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


@pytest.mark.skipif(sys.platform == "darwin", reason="APFS accepts only valid UTF-8 names")
@pytest.mark.parametrize("bad", ["n\udce9b.fits", "nuit\udce9/a.fits"])
def test_a_name_that_is_not_text_is_left_out_and_the_scan_goes_on(conn, tmp_path, bad):
    """Nome latin-1 su NAS Linux (Python: surrogato): non scrivibile nel DB. Prima fermava tutto."""
    nas = tmp_path / "nas"
    _file(nas / "good.fits")
    _file(nas / bad)
    result = scan_root(conn, add_root(conn, nas, NOW), NOW)
    assert result.changes.new == ["good.fits"]
    assert result.changes.unlooked == [bad]
    receipt = conn.execute("SELECT finished, left_out FROM pipeline_scans").fetchone()
    assert receipt["finished"] == 1
    assert bad in json.loads(receipt["left_out"])["unlooked"]


def test_a_file_not_looked_at_does_not_stop_the_others_being_judged(conn, tmp_path, monkeypatch):
    """Il primo non si guarda: i seguenti si giudicano lo stesso, nessuno sparito per errore."""
    _file(tmp_path / "a.fits")
    _file(tmp_path / "b.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    real = os.stat

    def flaky(path, *args, **kwargs):
        if str(path).endswith("a.fits"):
            raise PermissionError("errore passeggero (mock)")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", flaky)
    changes = scan_root(conn, root, LATER).changes
    monkeypatch.setattr(os, "stat", real)
    assert (changes.unlooked, changes.unchanged, changes.gone) == (["a.fits"], ["b.fits"], [])


def test_each_scan_leaves_its_receipt(conn, tmp_path):
    _file(tmp_path / "a.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    scan_root(conn, root, LATER)
    rows = conn.execute(
        "SELECT reachable, new, changed, unchanged, gone FROM pipeline_scans ORDER BY id"
    ).fetchall()
    assert [tuple(r) for r in rows] == [(1, 1, 0, 0, 0), (1, 0, 0, 1, 0)]


def test_an_emptied_root_that_had_files_counts_as_silent(conn, tmp_path):
    """NAS smontato in Docker: cartella di mount vuota ma aperta. Muta, nessuno sparito."""
    nas = tmp_path / "nas"  # tmp_path holds the DB: never empty
    _file(nas / "night" / "a.fits")
    _file(nas / "b.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    shutil.rmtree(nas / "night")
    (nas / "b.fits").unlink()
    changes = scan_root(conn, root, LATER).changes
    assert (changes.reachable, changes.gone) == (False, [])
    _file(nas / "night" / "a.fits")
    _file(nas / "b.fits")
    back = scan_root(conn, root, "2026-10-24T20:00:00+00:00").changes
    assert (back.new, back.gone) == ([], [])  # never gone, so never new


def test_a_new_empty_root_is_reachable(conn, tmp_path):
    """Mai visti file: niente da proteggere, la cartella vuota e' solo vuota."""
    nas = tmp_path / "nas"
    nas.mkdir()
    changes = scan_root(conn, add_root(conn, nas, NOW), NOW).changes
    assert changes.reachable is True


def _other_volume(conn, root):
    """Root's stored volume differs from disk's: another disk under same letter or mount."""
    conn.execute("UPDATE pipeline_roots SET device = device || '-other' WHERE id = ?", (root,))
    conn.commit()


def test_another_disk_under_the_same_letter_is_judged_and_said(conn, tmp_path):
    """Si giudica sempre (pose sparite, tornano col disco giusto) e la ricevuta lo dice.
    Prima: radice muta, che restava muta per sempre se l'archivio era davvero cambiato."""
    nas = tmp_path / "nas"
    a = _file(nas / "night" / "a.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    a.unlink()
    _file(nas / "other" / "b.fits")
    _other_volume(conn, root)
    changes = scan_root(conn, root, LATER).changes
    assert (changes.reachable, changes.gone) == (True, ["night/a.fits"])
    assert changes.new == ["other/b.fits"]
    said = conn.execute("SELECT volume_changed FROM pipeline_scans ORDER BY id").fetchall()
    assert [r[0] for r in said] == [0, 1]
    assert scan_root(conn, root, LATER).changes.unchanged == ["other/b.fits"]  # adopted, no repeat


def test_the_right_disk_back_brings_its_frames_back(conn, tmp_path):
    """Altro disco: pose sparite; disco giusto di nuovo: stesse pose, stesso frame (le risposte)."""
    nas = tmp_path / "nas"
    shot = nina_light(nas / "night" / "a.fits", 1).read_bytes()
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    frame = conn.execute("SELECT frame_id FROM pipeline_files").fetchone()[0]
    (nas / "night" / "a.fits").unlink()
    _other_volume(conn, root)
    assert scan_root(conn, root, LATER).changes.gone == ["night/a.fits"]
    (nas / "night" / "a.fits").write_bytes(shot)
    _other_volume(conn, root)
    assert scan_root(conn, root, LATER).changes.new == ["night/a.fits"]
    row = conn.execute("SELECT state, frame_id FROM pipeline_files").fetchone()
    assert tuple(row) == ("present", frame)


def test_the_archive_copied_to_a_new_disk_is_judged(conn, tmp_path):
    """Stesso archivio su un disco nuovo: le pose ci sono, si giudica come sempre."""
    nas = tmp_path / "nas"
    _file(nas / "a.fits")
    b = _file(nas / "b.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    b.unlink()
    _other_volume(conn, root)
    changes = scan_root(conn, root, LATER).changes
    assert (changes.reachable, changes.unchanged, changes.gone) == (True, ["a.fits"], ["b.fits"])


def test_a_root_with_no_frames_on_a_new_volume_takes_its_new_frames(conn, tmp_path):
    """Aggiunta vuota, poi il volume cambia: nessuna posa da proteggere, si legge."""
    nas = tmp_path / "nas"
    nas.mkdir()
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    _other_volume(conn, root)
    _file(nas / "night" / "a.fits")
    assert scan_root(conn, root, LATER).changes.new == ["night/a.fits"]


def test_a_copied_archive_reordered_later_is_still_judged(conn, tmp_path):
    """Dopo la copia il volume nuovo diventa il suo: riordinare non la rende muta."""
    nas = tmp_path / "nas"
    _file(nas / "night" / "a.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    _other_volume(conn, root)
    assert scan_root(conn, root, LATER).changes.unchanged == ["night/a.fits"]
    (nas / "night").rename(nas / "2026-10-22")
    changes = scan_root(conn, root, LATER).changes
    assert (changes.reachable, changes.gone) == (True, ["night/a.fits"])


def test_a_root_emptied_of_fits_but_with_left_out_entries_still_judges(conn, tmp_path):
    """Resta un cestino: la cartella risponde davvero, i file tolti sono spariti."""
    nas = tmp_path / "nas"
    _file(nas / "a.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    (nas / "a.fits").unlink()
    _file(nas / ".Trashes" / "a.fits")
    assert scan_root(conn, root, LATER).changes.gone == ["a.fits"]


@pytest.mark.parametrize("left", ["notes.txt", "night/", "a.xisf"])
def test_a_root_emptied_of_fits_but_not_empty_still_judges(conn, tmp_path, left):
    """Restano note, cartelle di notte o altri file: montata, i FITS tolti sono spariti."""
    nas = tmp_path / "nas"
    _file(nas / "a.fits")
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    (nas / "a.fits").unlink()
    if left.endswith("/"):
        (nas / left).mkdir()
    else:
        (nas / left).write_bytes(b"x")
    changes = scan_root(conn, root, LATER).changes
    assert (changes.reachable, changes.gone) == (True, ["a.fits"])


def test_the_same_root_is_added_once(conn, tmp_path):
    assert add_root(conn, tmp_path, NOW) == add_root(conn, tmp_path, LATER)


@pytest.mark.parametrize("name", ["a.fits", "missing"])
def test_only_a_folder_that_exists_is_added(conn, tmp_path, name):
    """Un file o un percorso che non c'e': nessuna radice."""
    (tmp_path / "a.fits").write_bytes(b"")
    with pytest.raises(NotADirectoryError):
        add_root(conn, tmp_path / name, NOW)
    assert conn.execute("SELECT COUNT(*) FROM pipeline_roots").fetchone()[0] == 0


def test_the_same_folder_written_another_way_is_the_same_root(conn, tmp_path):
    """Barra finale, barre, maiuscole (Windows): una cartella, una radice."""
    (tmp_path / "Archive").mkdir()
    first = add_root(conn, tmp_path / "Archive", NOW)
    spellings = [str(tmp_path / "Archive") + os.sep, str(tmp_path / "Archive").replace("\\", "/")]
    if sys.platform == "win32":
        spellings.append(str(tmp_path / "ARCHIVE"))
    for spelling in spellings:
        assert add_root(conn, spelling, LATER) == first
    assert conn.execute("SELECT COUNT(*) FROM pipeline_roots").fetchone()[0] == 1


def test_a_folder_inside_or_around_a_root_is_refused_saying_which(conn, tmp_path):
    """Dentro o intorno a una gia' aggiunta: rifiutata col perche', mai contata due volte."""
    (tmp_path / "archive" / "night").mkdir(parents=True)
    add_root(conn, tmp_path / "archive", NOW)
    with pytest.raises(RootOverlapError) as inside:
        add_root(conn, tmp_path / "archive" / "night", NOW)
    assert inside.value.inside is True
    assert Path(inside.value.other) == tmp_path / "archive"
    assert str(inside.value) == f"inside {tmp_path / 'archive'}"
    with pytest.raises(RootOverlapError) as around:
        add_root(conn, tmp_path, NOW)
    assert around.value.inside is False
    assert conn.execute("SELECT COUNT(*) FROM pipeline_roots").fetchone()[0] == 1


@pytest.mark.skipif(sys.platform != "win32", reason="drive letters: Windows only")
def test_roots_on_two_drives_are_both_added(conn, tmp_path):
    mine = os.path.splitdrive(tmp_path)[0].upper()
    others = [
        f"{d}:\\" for d in string.ascii_uppercase if f"{d}:" != mine and Path(f"{d}:\\").is_dir()
    ]
    if not others:
        pytest.skip("one drive only")
    first = add_root(conn, tmp_path, NOW)
    assert add_root(conn, others[0], NOW) != first


def test_a_linked_folder_written_inside_a_root_is_inside(conn, tmp_path):
    """Collegamento dentro la radice: la radice lo legge gia', non e' una seconda radice."""
    (tmp_path / "elsewhere" / "night").mkdir(parents=True)
    (tmp_path / "archive").mkdir()
    folder_link(tmp_path / "elsewhere" / "night", tmp_path / "archive" / "linked")
    add_root(conn, tmp_path / "archive", NOW)
    with pytest.raises(RootOverlapError) as inside:
        add_root(conn, tmp_path / "archive" / "linked", NOW)
    assert inside.value.inside is True


def test_adding_a_root_never_touches_the_other_roots_disks(conn, tmp_path, monkeypatch):
    """NAS spento fra le radici salvate: confronto sulle chiavi salvate, nessun accesso."""
    (tmp_path / "nas").mkdir()
    (tmp_path / "local").mkdir()
    add_root(conn, tmp_path / "nas", NOW)
    real = os.path.realpath

    def nas_off(path, *args, **kwargs):
        if "nas" in str(path):
            raise AssertionError("touched the other root")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", nas_off)
    assert add_root(conn, tmp_path / "local", NOW) == 2


@pytest.mark.skipif(sys.platform != "win32", reason="network shares: Windows")
def test_a_folder_inside_a_network_share_root_is_inside(conn):
    add_root(conn, r"\\localhost\C$", NOW)
    with pytest.raises(RootOverlapError):
        add_root(conn, r"\\localhost\C$\Windows", NOW)


@pytest.mark.parametrize("drive_first", [True, False])
def test_a_folder_on_a_drive_root_added_is_inside_it(conn, tmp_path, drive_first):
    """Radice di un disco ('C:\\' o '/'): finisce gia' con la barra, il dentro si vede lo stesso."""
    drive = Path(tmp_path.anchor)
    first, second = (drive, tmp_path) if drive_first else (tmp_path, drive)
    add_root(conn, first, NOW)
    with pytest.raises(RootOverlapError) as overlap:
        add_root(conn, second, NOW)
    assert overlap.value.inside is drive_first


def test_the_same_folder_through_a_link_is_the_same_root(conn, tmp_path):
    """Junction o symlink verso una cartella gia' aggiunta: stessa radice, file mai due volte."""
    (tmp_path / "archive").mkdir()
    folder_link(tmp_path / "archive", tmp_path / "shortcut")
    assert add_root(conn, tmp_path / "shortcut", NOW) == add_root(conn, tmp_path / "archive", NOW)


@pytest.mark.skipif(sys.platform != "win32", reason="\\\\?\\ and admin shares: Windows")
def test_the_same_folder_written_as_long_path_or_share_is_the_same_root(conn, tmp_path):
    """Prima: forma lunga, condivisione, UNC lunga = radici nuove, file contati 4 volte."""
    (tmp_path / "archive" / "night").mkdir(parents=True)
    plain = str(tmp_path / "archive")
    drive, rest = os.path.splitdrive(plain)
    share = f"\\\\localhost\\{drive[0]}$" + rest
    first = add_root(conn, plain, NOW)
    for spelling in ("\\\\?\\" + plain, share, "\\\\?\\UNC" + share[1:]):
        assert add_root(conn, spelling, NOW) == first, spelling
    with pytest.raises(RootOverlapError):
        add_root(conn, "\\\\?\\" + plain + "\\night", NOW)


def test_a_volume_number_past_signed_64_bits_is_stored(conn, tmp_path, monkeypatch):
    """Seriale di volume Windows a 64 bit senza segno (disco vero: 17585015167195144138): prima
    OverflowError, nessuna radice."""
    from astrolog.pipeline import changes

    real = os.stat

    def big(path, *args, **kwargs):
        st = real(path, *args, **kwargs)
        if not stat.S_ISDIR(st.st_mode):
            return st
        hidden = {k: getattr(st, k) for k in dir(st) if k.startswith("st_") and k != "st_dev"}
        return os.stat_result((*st[:2], 17585015167195144138, *st[3:10]), hidden)

    monkeypatch.setattr(changes.os, "stat", big)
    (tmp_path / "nas").mkdir()
    _file(tmp_path / "nas" / "a.fits")
    root = add_root(conn, tmp_path / "nas", NOW)
    assert scan_root(conn, root, NOW).changes.new == ["a.fits"]


@pytest.mark.skipif(sys.platform != "win32", reason="admin shares: Windows")
@pytest.mark.parametrize("plain_first", [True, False])
def test_a_folder_inside_or_around_written_as_share_is_refused(conn, tmp_path, plain_first):
    """Z:\\Astro poi \\\\nas\\astro\\notte: prima accettate tutte e due, file contati due volte."""
    (tmp_path / "archive" / "night").mkdir(parents=True)
    drive, rest = os.path.splitdrive(str(tmp_path))
    share = f"\\\\localhost\\{drive[0]}$" + rest
    parent, child = str(tmp_path / "archive"), share + "\\archive\\night"
    first, second = (parent, child) if plain_first else (child, share + "\\archive")
    if not plain_first:
        first = str(tmp_path / "archive" / "night")
    add_root(conn, first, NOW)
    with pytest.raises(RootOverlapError) as overlap:
        add_root(conn, second, NOW)
    assert overlap.value.inside is plain_first


@pytest.mark.skipif(sys.platform != "win32", reason="admin shares: Windows")
def test_a_letter_mapped_below_a_share_still_sees_what_holds_it(conn, tmp_path):
    """Z: = \\\\nas\\dati\\astro (lettera sotto la condivisione), poi \\\\nas\\dati: la contiene.
    Junction al posto della lettera: risalendo il testo non si vede chi sta sopra."""
    (tmp_path / "s" / "m" / "archive").mkdir(parents=True)
    folder_link(tmp_path / "s" / "m", tmp_path / "J")
    drive, rest = os.path.splitdrive(str(tmp_path))
    add_root(conn, tmp_path / "J" / "archive", NOW)
    with pytest.raises(RootOverlapError) as overlap:
        add_root(conn, f"\\\\localhost\\{drive[0]}$" + rest + "\\s", NOW)
    assert overlap.value.inside is False


def test_a_renamed_root_folder_added_again_is_a_new_root(conn, tmp_path):
    """Rinominata, tiene il suo id sul disco: non e' piu' la radice salvata, che ora manca."""
    (tmp_path / "Astro").mkdir()
    first = add_root(conn, tmp_path / "Astro", NOW)
    (tmp_path / "Astro").rename(tmp_path / "Astro2026")
    assert add_root(conn, tmp_path / "Astro2026", NOW) != first


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 strips a trailing dot: Windows only")
def test_a_root_ending_with_a_dot_is_kept_as_itself(conn, tmp_path):
    """Radice 'night.': prima cercata come 'night', rifiutata o confusa con la sorella."""
    os.makedirs("\\\\?\\" + str(tmp_path / "night."))
    root = add_root(conn, str(tmp_path / "night."), NOW)
    path = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root,)).fetchone()[0]
    assert path.endswith("night.")


def test_a_sibling_with_a_common_prefix_is_not_inside(conn, tmp_path):
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive2").mkdir()
    assert add_root(conn, tmp_path / "archive", NOW) != add_root(conn, tmp_path / "archive2", NOW)
