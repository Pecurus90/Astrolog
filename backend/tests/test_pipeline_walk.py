"""Walk pipeline nuova, portato da `fits/walk.py` coi test. In piu': cartelle collegate seguite
una volta, `.fts`, compressi `.fz`."""

import os
import stat
import sys
from types import SimpleNamespace

import pytest

from astrolog.pipeline import walk
from astrolog.pipeline.walk import long_path, walk_dir
from conftest import ScanFinta, VoceFinta, breaking_dir, fake_entries, unreadable_dir


def _touch(root, *parts):
    path = os.path.join(root, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb"):
        pass
    return path


def _link(target, link):
    """Folder link: junction on Windows (no privilege needed), symlink elsewhere."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def names(paths):
    return {os.path.basename(p) for p in paths}


def found(root):
    return walk_dir(str(root)).found


def test_collects_every_fits_extension_and_its_compressed_form_and_ignores_the_rest(tmp_path):
    root = str(tmp_path)
    wanted = ("a.fits", "b.fit", "D.FITS", "z.fts", "w.fits.fz", "W2.FIT.FZ", "sub/deep.fits")
    for n in wanted:
        _touch(root, *n.split("/"))
    for n in ("x.xisf", "y.ser", "v.fits.gz", "u.txt", "t.fitsx", "c.fz", "d.txt.fz"):
        _touch(root, n)
    assert names(found(root)) == {os.path.basename(n) for n in wanted}


def test_a_linked_folder_is_walked(tmp_path):
    """Archivio dietro collegamento (cartella verso altro disco): saltarlo perde tutte le pose."""
    _touch(str(tmp_path), "altro_disco", "posa.fits")
    root = tmp_path / "archivio"
    root.mkdir()
    _link(tmp_path / "altro_disco", root / "acquisizioni")
    assert names(found(root)) == {"posa.fits"}


def test_a_link_back_to_an_ancestor_does_not_loop(tmp_path):
    """Collegamento all'indietro: walk non gira in tondo, cartella percorsa una volta comunque
    raggiunta."""
    _touch(str(tmp_path), "sub", "deep.fits")
    _link(tmp_path, tmp_path / "sub" / "indietro")
    assert names(found(tmp_path)) == {"deep.fits"}
    assert len(found(tmp_path)) == 1


def test_a_folder_reached_by_two_links_is_walked_once(tmp_path):
    _touch(str(tmp_path), "vera", "posa.fits")
    root = tmp_path / "archivio"
    root.mkdir()
    _link(tmp_path / "vera", root / "uno")
    _link(tmp_path / "vera", root / "due")
    assert len(found(root)) == 1


def test_a_link_to_a_missing_folder_is_unreadable(tmp_path):
    """Collegamento verso disco staccato: non sparisce in silenzio, e' cartella che non si apre."""
    target = tmp_path / "staccato"
    target.mkdir()
    root = tmp_path / "archivio"
    root.mkdir()
    _link(target, root / "disco")
    target.rmdir()
    result = walk_dir(str(root))
    assert result.found == []
    assert names(result.unreadable) == {"disco"}


def test_a_symlink_to_a_missing_folder_is_unreadable(tmp_path, monkeypatch):
    """Symlink (Mac, NAS, Windows) su bersaglio sparito: `is_dir` falso, come documenta Python.
    Finto: qui crearlo chiede un privilegio."""
    root = str(tmp_path)
    _touch(root, "segnaposto")

    class _Rotto(VoceFinta):
        name = "disco"

        def is_symlink(self):
            return True

    fake_entries(monkeypatch, lambda _c, v: _Rotto() if v.name == "segnaposto" else v)
    result = walk_dir(root)
    assert result.found == []
    assert names(result.unreadable) == {"disco"}


def test_the_mac_twin_files_are_not_collected(tmp_path):
    """Gemello Mac `._nome.fits` su chiavetta o NAS: metadati Finder, non FITS. Senza,
    "1.200 file non letti" su 1.200 pose sane."""
    root = str(tmp_path)
    _touch(root, "M42.fits")
    _touch(root, "._M42.fits")
    _touch(root, "sub", "._deep.fit")
    _touch(root, "sub", "deep.fit")
    assert names(found(root)) == {"M42.fits", "deep.fit"}


def test_hidden_folders_are_not_walked_so_the_bin_stays_out(tmp_path, monkeypatch):
    """Cestino = pose cancellate. Nascosto per proprieta' (punto, attributo Windows), non per nome;
    attributo finto: su Mac e Linux non esiste. Cartelle saltate si nominano."""
    monkeypatch.setattr(walk, "PLATFORM", "win32")
    root = str(tmp_path)
    _touch(root, "buona.fits")
    _touch(root, ".Trashes", "cancellata.fits")
    _touch(root, "$RECYCLE.BIN", "cancellata2.fits")
    real = os.scandir

    class _Nascosta(VoceFinta):
        """Cartella con attributo nascosto, come la vede `os.scandir` su Windows."""

        name = "$RECYCLE.BIN"

        def is_dir(self, follow_symlinks=True):
            return True

        def stat(self, follow_symlinks=True):
            # non `os.stat_result`: su Mac e Linux non ha il campo, lo scarterebbe
            return SimpleNamespace(st_file_attributes=stat.FILE_ATTRIBUTE_HIDDEN)

    def fake(p):
        voci = ScanFinta(v for v in real(p) if v.name != "$RECYCLE.BIN")
        if os.path.normpath(str(p)) == os.path.normpath(root):
            voci.append(_Nascosta())
        return voci

    monkeypatch.setattr(walk.os, "scandir", fake)
    result = walk_dir(root)
    assert names(result.found) == {"buona.fits"}
    assert names(result.hidden) == {".Trashes", "$RECYCLE.BIN"}
    # filtro solo su sottocartelle: radice nascosta scelta (`D:\.astro`) si legge
    nascosta = os.path.join(root, ".Trashes")
    assert names(found(nascosta)) == {"cancellata.fits"}


# (nome, sistema, attributi Windows, flag Mac, raccolto?). Costanti e fonti in `pipeline/walk.py`.
SEGNI = [
    ("Windows, dati non sul disco", "win32", walk.FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS, 0, False),
    ("Windows, segnaposto nell'elenco", "win32", walk.FILE_ATTRIBUTE_RECALL_ON_OPEN, 0, False),
    ("Windows, archiviato altrove", "win32", stat.FILE_ATTRIBUTE_OFFLINE, 0, False),
    ("Windows, tenuto sul disco", "win32", 0x00080000, 0, True),  # FILE_ATTRIBUTE_PINNED
    ("Mac, senza dati", "darwin", 0, walk.SF_DATALESS, False),
    ("Mac, sul disco", "darwin", 0, 0, True),
    ("Linux: il segno non esiste", "linux", walk.FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS,
     walk.SF_DATALESS, True),
]  # fmt: skip


@pytest.mark.parametrize(
    "sistema, attributi, flag, raccolto", [c[1:] for c in SEGNI], ids=[c[0] for c in SEGNI]
)
def test_a_file_that_is_not_on_the_disk_is_not_collected(
    tmp_path, monkeypatch, sistema, attributi, flag, raccolto
):
    """Solo online (OneDrive, Dropbox, iCloud): aprirlo scarica, quindi nominato, non raccolto.
    Segno dall'elenco cartella; sistema senza segno: non si chiede."""
    root = str(tmp_path)
    _touch(root, "sul_disco.fits")
    _touch(root, "posa.fits")
    monkeypatch.setattr(walk, "PLATFORM", sistema)
    chiesti = []

    class _Posa(VoceFinta):
        name = "posa.fits"

        def stat(self, follow_symlinks=True):
            chiesti.append(follow_symlinks)
            return SimpleNamespace(st_file_attributes=attributi, st_flags=flag)

    fake_entries(monkeypatch, lambda _cartella, v: _Posa() if v.name == "posa.fits" else v)
    result = walk_dir(root)
    assert "sul_disco.fits" in names(result.found)
    assert ("posa.fits" in names(result.found)) is raccolto
    assert names(result.online_only) == (set() if raccolto else {"posa.fits"})
    # segno letto sulla voce, senza seguire collegamenti; dove non esiste, non si chiede
    assert chiesti == ([] if sistema == "linux" else [False])


def test_a_file_whose_sign_cannot_be_read_is_taken_as_on_the_disk(tmp_path, monkeypatch):
    """Segno illeggibile: file raccolto, come prima del segno. Se davvero non si apre, scansione lo
    conta fra gli errori invece di perderlo in silenzio."""
    root = str(tmp_path)
    _touch(root, "posa.fits")
    monkeypatch.setattr(walk, "PLATFORM", "win32")

    class _Muta(VoceFinta):
        name = "posa.fits"

        def stat(self, follow_symlinks=True):
            raise OSError("attributi illeggibili (mock)")

    fake_entries(monkeypatch, lambda _cartella, v: _Muta() if v.name == "posa.fits" else v)
    result = walk_dir(root)
    assert names(result.found) == {"posa.fits"}
    assert result.online_only == []


def test_an_old_icloud_placeholder_counts_as_online_only(tmp_path):
    """`.Nome.fits.icloud` (iCloud prima di Sonoma): solo online, col nome vero. No: non FITS,
    gemello `._`, segnaposto accanto al file vero (posa c'e')."""
    root = str(tmp_path)
    _touch(root, ".M42.FITS.icloud")
    _touch(root, ".M44.fits.fz.icloud")
    _touch(root, ".nota.txt.icloud")
    _touch(root, "._.M42.FITS.icloud")
    _touch(root, "M43.fits")
    _touch(root, ".m43.FITS.icloud")
    result = walk_dir(root)
    assert names(result.found) == {"M43.fits"}
    assert result.online_only == [os.path.join(root, "M42.FITS"), os.path.join(root, "M44.fits.fz")]


def test_a_link_to_a_file_is_collected_as_a_file(tmp_path, monkeypatch):
    root = str(tmp_path)
    _touch(root, "a.fits")
    monkeypatch.setattr(walk, "PLATFORM", "linux")  # qui si prova il collegamento, non il segno

    class _CollegamentoAUnFile(VoceFinta):
        name = "collegamento.fits"

        def is_symlink(self):
            return True

    fake_entries(monkeypatch, lambda _c, v: _CollegamentoAUnFile() if v.name == "a.fits" else v)
    assert names(found(root)) == {"collegamento.fits"}


def test_an_entry_that_cannot_be_asked_is_looked_at_as_a_file(tmp_path, monkeypatch):
    """`is_dir` che fallisce (documentato da Python): voce trattata come file, walk continua."""
    root = str(tmp_path)
    _touch(root, "posa.fits")
    monkeypatch.setattr(walk, "PLATFORM", "linux")  # qui si prova la voce muta, non il segno

    class _Muta(VoceFinta):
        name = "posa.fits"

        def is_dir(self, follow_symlinks=True):
            raise OSError("attributi illeggibili (mock)")

    fake_entries(monkeypatch, lambda _c, v: _Muta() if v.name == "posa.fits" else v)
    assert names(found(root)) == {"posa.fits"}


def test_empty_and_missing_folders(tmp_path):
    assert found(tmp_path) == []
    assert found(tmp_path / "nope") == []


def test_order_is_deterministic(tmp_path):
    for n in ("c.fits", "a.fits", "b.fits"):
        _touch(str(tmp_path), n)
    first = found(tmp_path)
    assert first == sorted(first) and first == found(tmp_path)


def test_unreadable_subfolder_is_reported_not_swallowed(tmp_path, monkeypatch):
    root = str(tmp_path)
    _touch(root, "a.fits")
    sub = os.path.join(root, "sub")
    _touch(root, "sub", "deep.fits")
    unreadable_dir(monkeypatch, walk, sub)
    result = walk_dir(root)
    assert "a.fits" in names(result.found) and "deep.fits" not in names(result.found)
    assert len(result.unreadable) == 1 and os.path.normpath(result.unreadable[0]).endswith("sub")


def test_a_folder_that_breaks_while_listed_is_unreadable_and_the_walk_goes_on(
    tmp_path, monkeypatch
):
    """NAS che cade a meta' elenco (Windows: errore 64). Prima: tutta la scansione ferma."""
    root = str(tmp_path)
    _touch(root, "a.fits")
    _touch(root, "sub", "one.fits")
    _touch(root, "sub", "two.fits")
    sub = os.path.join(root, "sub")
    breaking_dir(monkeypatch, walk, sub)
    result = walk_dir(root)
    assert "a.fits" in names(result.found)
    assert [os.path.normpath(u) for u in result.unreadable] == [os.path.normpath(sub)]


def test_deep_tree_does_not_recurse(tmp_path):
    _touch(str(tmp_path), *(["d"] * 40), "bottom.fits")
    assert "bottom.fits" in names(found(tmp_path))


def test_paths_beyond_260_characters(tmp_path):
    """Archivio profondo oltre i 260 caratteri di Windows: si trova lo stesso."""
    deep = str(tmp_path)
    while len(deep) < 300:
        deep = os.path.join(deep, "Nebulosa della Testa di Cavallo - IC 434 - sessione lunga")
    os.makedirs(long_path(deep), exist_ok=True)
    with open(long_path(os.path.join(deep, "frame.fits")), "wb"):
        pass
    result = found(tmp_path)
    assert len(result) == 1 and result[0].endswith("frame.fits")


@pytest.mark.skipif(os.name != "nt", reason="la forma dei percorsi lunghi esiste solo su Windows")
def test_a_long_network_path_gets_the_unc_form():
    """Rete profonda: forma `\\\\?\\UNC\\server\\share`, col prefisso semplice Windows non apre
    (*Maximum Path Length Limitation*). Solo Windows: unico col limite."""
    lungo = "x" * 250
    assert long_path(rf"\\nas\astro\{lungo}").startswith(r"\\?\UNC\nas\astro")
    assert long_path(rf"C:\astro\{lungo}").startswith(r"\\?\C:\astro")
    # col prefisso barre in avanti non sono separatori: normalizzate prima
    assert "/" not in long_path(f"C:/astro/{lungo}")
    assert long_path(r"C:\corto") == r"C:\corto"  # sotto soglia resta leggibile


def test_names_with_spaces_and_accents(tmp_path):
    _touch(str(tmp_path), "IC 405 - Nebulosa Stella Fiammeggiante", "posa n° 1 à.fits")
    assert len(found(tmp_path)) == 1
