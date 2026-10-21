"""Il walk della pipeline nuova, portato da `fits/walk.py` coi suoi test. Cambia per decisione di
Marco: le cartelle collegate si seguono (una volta sola), ed entrano `.fts` e i compressi `.fz`."""

import os
import stat
import sys
from types import SimpleNamespace

import pytest

from astrolog.pipeline import walk
from astrolog.pipeline.walk import long_path, walk_dir
from conftest import ScanFinta, VoceFinta, fake_entries, unreadable_dir


def _touch(root, *parts):
    path = os.path.join(root, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb"):
        pass
    return path


def _link(target, link):
    """A folder link on disk: a junction on Windows (no privilege needed), a symlink elsewhere."""
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
    """Un archivio puo' stare dietro un collegamento (una cartella che porta a un altro disco):
    saltarlo perderebbe tutte le pose che ci sono dentro."""
    _touch(str(tmp_path), "altro_disco", "posa.fits")
    root = tmp_path / "archivio"
    root.mkdir()
    _link(tmp_path / "altro_disco", root / "acquisizioni")
    assert names(found(root)) == {"posa.fits"}


def test_a_link_back_to_an_ancestor_does_not_loop(tmp_path):
    """Un collegamento che torna indietro non fa girare il walk in tondo: una cartella si
    percorre una volta sola, comunque la si raggiunga."""
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
    """Un collegamento verso un disco staccato non sparisce in silenzio: e' una cartella che non
    si apre."""
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
    """Il symlink di Mac, NAS e Windows su un bersaglio sparito non si dice cartella (`is_dir`
    falso, come lo documenta Python): si finge, perche' qui crearlo chiede un privilegio."""
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
    """macOS scrive un gemello `._nome.fits` accanto a ogni file su una chiavetta o un NAS:
    sono i metadati del Finder, pochi KB che non sono un FITS. Senza questa riga, un archivio
    passato da un Mac dice all'utente "1.200 file non letti" su 1.200 pose sane."""
    root = str(tmp_path)
    _touch(root, "M42.fits")
    _touch(root, "._M42.fits")
    _touch(root, "sub", "._deep.fit")
    _touch(root, "sub", "deep.fit")
    assert names(found(root)) == {"M42.fits", "deep.fit"}


def test_hidden_folders_are_not_walked_so_the_bin_stays_out(tmp_path, monkeypatch):
    """Nel cestino ci sono le pose che l'utente ha **cancellato**: percorrerlo le farebbe
    rientrare in archivio. Il cestino e le cartelle di servizio sono nascoste su tutti e tre i
    sistemi -- `.Trashes` su Mac, `$RECYCLE.BIN` e `System Volume Information` su Windows con
    l'attributo nascosto, il cestino di un NAS via SMB -- e si guarda la **proprieta'**, non
    una lista di nomi: un nome scritto a memoria copre il NAS che conosciamo e nessun altro.

    Le due meta' si provano insieme: la cartella col punto e' vera sul disco, quella con
    l'attributo di Windows si finge, perche' l'attributo non esiste su Mac e Linux e un test
    che si salta e' verde quanto uno che passa. Si finge anche il sistema, o fuori da Windows
    l'attributo non verrebbe nemmeno guardato.

    Le cartelle lasciate fuori non spariscono in silenzio: il walk le nomina."""
    monkeypatch.setattr(walk, "PLATFORM", "win32")
    root = str(tmp_path)
    _touch(root, "buona.fits")
    _touch(root, ".Trashes", "cancellata.fits")
    _touch(root, "$RECYCLE.BIN", "cancellata2.fits")
    real = os.scandir

    class _Nascosta(VoceFinta):
        """La cartella con l'attributo nascosto, come la vede `os.scandir` su Windows."""

        name = "$RECYCLE.BIN"

        def is_dir(self, follow_symlinks=True):
            return True

        def stat(self, follow_symlinks=True):
            # non `os.stat_result`: su Mac e Linux quel tipo non ha il campo, e lo scarterebbe
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
    # e l'altra meta' della regola: il filtro vale sulle SOTTOcartelle, non sulla radice. Chi
    # tiene l'archivio in una cartella nascosta (`D:\.astro`) deve trovarlo: se il filtro
    # valesse anche sulla radice, vedrebbe "0 file" sulla cartella che ha appena scelto.
    nascosta = os.path.join(root, ".Trashes")
    assert names(found(nascosta)) == {"cancellata.fits"}


# (nome, sistema, attributi di Windows, flag del Mac, il file si raccoglie?). Le costanti e le
# loro fonti stanno in `pipeline/walk.py`.
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
    """Un file solo online (OneDrive, Dropbox, iCloud) ha sul disco il segnaposto, e aprirlo lo
    scarica: non si raccoglie, si nomina. Il segno arriva con l'elenco della cartella, e dove
    il sistema non ce l'ha non si chiede nemmeno."""
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
    # il segno si legge sulla voce, senza seguire un collegamento; dove non esiste, non si chiede
    assert chiesti == ([] if sistema == "linux" else [False])


def test_a_file_whose_sign_cannot_be_read_is_taken_as_on_the_disk(tmp_path, monkeypatch):
    """Se il segno non si legge il file si raccoglie, come prima che il segno si guardasse: se
    davvero non si apre, la scansione lo conta fra gli errori invece di perderlo in silenzio."""
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
    """Prima di macOS Sonoma iCloud lasciava al posto del file un segnaposto nascosto
    `.Nome.fits.icloud`: vale come solo online, col nome del file vero. Non contano: un
    segnaposto che non e' di un FITS, il gemello `._` che il Mac gli scrive accanto su una
    chiavetta o un NAS, e un segnaposto rimasto accanto al suo file vero -- quello e' sul disco,
    e contarlo due volte direbbe "solo online" di una posa che c'e'."""
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
    """Un collegamento a un FITS e' un file: si raccoglie come gli altri."""
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
    """Chiedere a una voce se e' una cartella puo' fallire (Python lo documenta per
    `is_symlink`): allora si tratta come un file -- un FITS si raccoglie --, invece di fermare il
    walk su quella cartella."""
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


def test_deep_tree_does_not_recurse(tmp_path):
    _touch(str(tmp_path), *(["d"] * 40), "bottom.fits")
    assert "bottom.fits" in names(found(tmp_path))


def test_paths_beyond_260_characters(tmp_path):
    """Una cartella di archivio profonda supera i 260 caratteri di Windows: si trova lo stesso."""
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
    """Una cartella di rete profonda vuole la sua forma: `\\\\?\\UNC\\server\\share\\...`.
    Col prefisso semplice (`\\\\?\\\\\\server\\...`) Windows non la apre, e l'utente legge
    "la cartella non risponde" su una cartella che c'e'. La forma e la regola sulle barre in
    avanti stanno nella documentazione di Windows (*Maximum Path Length Limitation*).

    Gira solo su Windows -- e' l'unico sistema che ha questo limite -- ma **gira**: il cancello
    passa su Windows in locale e su tutti e tre i sistemi in CI."""
    lungo = "x" * 250
    assert long_path(rf"\\nas\astro\{lungo}").startswith(r"\\?\UNC\nas\astro")
    assert long_path(rf"C:\astro\{lungo}").startswith(r"\\?\C:\astro")
    # col prefisso le barre in avanti non valgono come separatore: si normalizzano prima
    assert "/" not in long_path(f"C:/astro/{lungo}")
    assert long_path(r"C:\corto") == r"C:\corto"  # sotto la soglia resta leggibile


def test_names_with_spaces_and_accents(tmp_path):
    _touch(str(tmp_path), "IC 405 - Nebulosa Stella Fiammeggiante", "posa n° 1 à.fits")
    assert len(found(tmp_path)) == 1
