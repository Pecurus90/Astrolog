"""Il walk delle cartelle: .fits e .fit, ricorsivo, ordinato, iterativo, symlink a cartella
non seguiti, cartelle illeggibili riportate e mai inghiottite. Portato da old/."""

import os
import stat
import time
from types import SimpleNamespace

import pytest

from astrolog.fits import walk
from astrolog.fits.walk import long_path, walk_dir
from conftest import (
    CartellaLegata,
    ScanFinta,
    VoceAvvolta,
    VoceFinta,
    fake_entries,
    unreadable_dir,
)


def _touch(root, *parts):
    path = os.path.join(root, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb"):
        pass
    return path


def names(paths):
    return {os.path.basename(p) for p in paths}


def test_collects_fits_and_fit_recursively_and_ignores_the_rest(tmp_path):
    root = str(tmp_path)
    for n in ("a.fits", "b.fit", "D.FITS", "sub/deep.fits", "sub/sub2/deeper.fit"):
        _touch(root, *n.split("/"))
    for n in ("x.xisf", "y.ser", "z.fts", "w.fits.fz", "v.fits.gz", "u.txt", "t.fitsx"):
        _touch(root, n)
    assert names(walk_dir(root)) == {"a.fits", "b.fit", "D.FITS", "deep.fits", "deeper.fit"}


def test_a_folder_symlink_is_not_followed_so_the_walk_cannot_loop(tmp_path, monkeypatch):
    """La promessa dell'intestazione: i collegamenti a cartella non si seguono, o il walk
    girerebbe in tondo su un link che punta a un antenato.

    Il link **non** si crea sul disco: su Windows senza privilegi non si puo', e un test che si
    salta e' verde quanto uno che passa -- resterebbe saltato per sempre senza che nessuno lo
    guardi. Si finge invece cio' che il sistema dice di un link: `is_dir()` vero, ma
    `is_dir(follow_symlinks=False)` falso. Dietro il link c'e' un file che non deve comparire:
    se compare, qualcuno ha guardato la prima delle due."""
    root = str(tmp_path)
    _touch(root, "a.fits")
    _touch(root, "sub", "deep.fits")
    real = os.scandir
    link = os.path.join(root, "sub", "indietro")

    class _Voce(VoceFinta):
        def __init__(self, name, cartella_se_seguito=False):
            self.name = name
            self._seguito = cartella_se_seguito

        def is_dir(self, follow_symlinks=True):
            return self._seguito and follow_symlinks

        def is_symlink(self):
            return self._seguito

    def fake(p):
        if os.path.normpath(str(p)) == os.path.normpath(link):
            return ScanFinta([_Voce("dietro_al_link.fits")])  # cio' che c'e' oltre il link
        with real(p) as vere:
            voci = ScanFinta(vere)
        if os.path.normpath(str(p)) == os.path.normpath(os.path.join(root, "sub")):
            voci.append(_Voce("indietro", cartella_se_seguito=True))
        return voci

    monkeypatch.setattr(walk.os, "scandir", fake)
    collegate = []
    assert names(walk_dir(root, linked=collegate)) == {"a.fits", "deep.fits"}
    assert names(collegate) == {"indietro"}  # non seguito, ma nominato


def test_the_mac_twin_files_are_not_collected(tmp_path):
    """macOS scrive un gemello `._nome.fits` accanto a ogni file su una chiavetta o un NAS:
    sono i metadati del Finder, pochi KB che non sono un FITS. Senza questa riga, un archivio
    passato da un Mac dice all'utente "1.200 file non letti" su 1.200 pose sane."""
    root = str(tmp_path)
    _touch(root, "M42.fits")
    _touch(root, "._M42.fits")
    _touch(root, "sub", "._deep.fit")
    _touch(root, "sub", "deep.fit")
    assert names(walk_dir(root)) == {"M42.fits", "deep.fit"}


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
    nascoste = []
    assert names(walk_dir(root, hidden=nascoste)) == {"buona.fits"}
    assert names(nascoste) == {".Trashes", "$RECYCLE.BIN"}
    # e l'altra meta' della regola: il filtro vale sulle SOTTOcartelle, non sulla radice. Chi
    # tiene l'archivio in una cartella nascosta (`D:\.astro`) deve trovarlo: se il filtro
    # valesse anche sulla radice, vedrebbe "0 file" sulla cartella che ha appena scelto.
    nascosta = os.path.join(root, ".Trashes")
    assert names(walk_dir(nascosta)) == {"cancellata.fits"}


# (nome, sistema, attributi di Windows, flag del Mac, il file si raccoglie?). Le costanti e le
# loro fonti stanno in `fits/walk.py`.
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
    solo_online = []
    trovati = walk_dir(root, online_only=solo_online)
    assert "sul_disco.fits" in names(trovati)
    assert ("posa.fits" in names(trovati)) is raccolto
    assert names(solo_online) == (set() if raccolto else {"posa.fits"})
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
    solo_online = []
    assert names(walk_dir(root, online_only=solo_online)) == {"posa.fits"}
    assert solo_online == []


def test_an_old_icloud_placeholder_counts_as_online_only(tmp_path):
    """Prima di macOS Sonoma iCloud lasciava al posto del file un segnaposto nascosto
    `.Nome.fits.icloud`: vale come solo online, col nome del file vero. Non contano: un
    segnaposto che non e' di un FITS, il gemello `._` che il Mac gli scrive accanto su una
    chiavetta o un NAS, e un segnaposto rimasto accanto al suo file vero -- quello e' sul disco,
    e contarlo due volte direbbe "solo online" di una posa che c'e'."""
    root = str(tmp_path)
    _touch(root, ".M42.FITS.icloud")
    _touch(root, ".nota.txt.icloud")
    _touch(root, "._.M42.FITS.icloud")
    _touch(root, "M43.fits")
    _touch(root, ".m43.FITS.icloud")
    solo_online = []
    assert names(walk_dir(root, online_only=solo_online)) == {"M43.fits"}
    assert solo_online == [os.path.join(root, "M42.FITS")]


def test_a_junction_is_not_followed_and_is_named(tmp_path, monkeypatch):
    """Una giunzione di Windows non si percorre -- verso un antenato farebbe girare il walk a
    vuoto, e per Python e' una cartella come le altre (`fits/walk._kind`) -- ma si nomina: le
    pose che stanno oltre non spariscono in silenzio."""
    root = str(tmp_path)
    _touch(root, "a.fits")
    _touch(root, "giunzione", "oltre.fits")
    fake_entries(
        monkeypatch, lambda _c, v: CartellaLegata(v, junction=True) if v.name == "giunzione" else v
    )
    trovate = []
    assert names(walk_dir(root, linked=trovate)) == {"a.fits"}
    assert names(trovate) == {"giunzione"}


def test_a_link_to_a_file_is_not_named_as_a_folder(tmp_path, monkeypatch):
    """Solo i collegamenti A CARTELLA non si seguono: un collegamento a un FITS e' un file, si
    raccoglie come gli altri e la ricevuta non lo nomina fra le cartelle lasciate fuori."""
    root = str(tmp_path)
    _touch(root, "a.fits")
    monkeypatch.setattr(walk, "PLATFORM", "linux")  # qui si prova il collegamento, non il segno

    class _CollegamentoAUnFile(VoceFinta):
        name = "collegamento.fits"

        def is_symlink(self):
            return True

    fake_entries(monkeypatch, lambda _c, v: _CollegamentoAUnFile() if v.name == "a.fits" else v)
    collegate = []
    assert names(walk_dir(root, linked=collegate)) == {"collegamento.fits"}
    assert collegate == []


def test_the_linked_folders_are_named_in_order(tmp_path, monkeypatch):
    """La ricevuta nomina le cartelle collegate in ordine anche dove il sistema le elenca come
    capita (i file system di Linux e dei NAS): due scansioni uguali danno la stessa ricevuta."""
    root = str(tmp_path)
    for nome in ("alfa", "beta"):
        os.makedirs(os.path.join(root, nome))
    real = os.scandir

    def al_contrario(p):
        with real(p) as vere:
            voci = sorted(vere, key=lambda v: v.name, reverse=True)
        return ScanFinta(CartellaLegata(v, junction=True) for v in voci)

    monkeypatch.setattr(walk.os, "scandir", al_contrario)
    collegate = []
    walk_dir(root, linked=collegate)
    assert [os.path.basename(p) for p in collegate] == ["alfa", "beta"]


def test_the_folders_to_choose_from_are_the_ones_the_walk_walks(tmp_path, monkeypatch):
    """L'elenco da cui si sceglie una cartella decide come il walk: niente nascoste, niente
    collegate, e una voce che non dice se e' una cartella non ferma l'elenco intero."""
    root = str(tmp_path)
    for nome in ("M31", ".cestino", "giunzione", "muta"):
        os.makedirs(os.path.join(root, nome))

    class _Muta(VoceAvvolta):
        def is_dir(self, follow_symlinks=True):
            raise PermissionError("accesso negato (mock)")

    finte = {"giunzione": lambda v: CartellaLegata(v, junction=True), "muta": _Muta}
    fake_entries(monkeypatch, lambda _c, v: finte[v.name](v) if v.name in finte else v)
    assert walk.subfolders(root) == ["M31"]


def test_an_entry_that_cannot_be_asked_is_not_taken_for_a_link(tmp_path, monkeypatch):
    """Chiedere a una voce se e' un collegamento puo' fallire (Python lo documenta per
    `is_symlink`): allora non si considera un collegamento e si tratta come le altre -- un FITS
    si raccoglie --, invece di fermare il walk su quella cartella."""
    root = str(tmp_path)
    _touch(root, "posa.fits")
    monkeypatch.setattr(walk, "PLATFORM", "linux")  # qui si prova il collegamento, non il segno

    class _Muta(VoceFinta):
        name = "posa.fits"

        def is_junction(self):
            raise OSError("attributi illeggibili (mock)")

    fake_entries(monkeypatch, lambda _c, v: _Muta() if v.name == "posa.fits" else v)
    collegate = []
    assert names(walk_dir(root, linked=collegate)) == {"posa.fits"}
    assert collegate == []


def test_the_walk_stops_at_its_deadline_and_says_what_it_left(tmp_path):
    """Chi ha fretta (la conta di Aggiungi cartella) da' una scadenza: il walk si ferma e dice
    quali cartelle non ha guardato, cosi' il chiamante sa che il conteggio non e' completo."""
    root = str(tmp_path)
    _touch(root, "sub", "a.fits")
    rimaste = []
    assert walk_dir(root, deadline=time.monotonic() - 1, unvisited=rimaste) == []
    assert rimaste == [root]
    rimaste = []
    assert names(walk_dir(root, deadline=time.monotonic() + 60, unvisited=rimaste)) == {"a.fits"}
    assert rimaste == []


def test_empty_and_missing_folders(tmp_path):
    assert walk_dir(str(tmp_path)) == []
    assert walk_dir(str(tmp_path / "nope")) == []


def test_order_is_deterministic(tmp_path):
    for n in ("c.fits", "a.fits", "b.fits"):
        _touch(str(tmp_path), n)
    found = walk_dir(str(tmp_path))
    assert found == sorted(found) and found == walk_dir(str(tmp_path))


def test_unreadable_subfolder_is_reported_not_swallowed(tmp_path, monkeypatch):
    root = str(tmp_path)
    _touch(root, "a.fits")
    sub = os.path.join(root, "sub")
    _touch(root, "sub", "deep.fits")
    unreadable_dir(monkeypatch, walk, sub)
    unreadable = []
    found = walk_dir(root, unreadable=unreadable)
    assert "a.fits" in names(found) and "deep.fits" not in names(found)
    assert len(unreadable) == 1 and os.path.normpath(unreadable[0]).endswith("sub")
    assert "a.fits" in names(walk_dir(root))  # senza lista: tollerata, non un crash


def test_deep_tree_does_not_recurse(tmp_path):
    _touch(str(tmp_path), *(["d"] * 40), "bottom.fits")
    assert "bottom.fits" in names(walk_dir(str(tmp_path)))


def test_paths_beyond_260_characters(tmp_path):
    """Una cartella di archivio profonda supera i 260 caratteri di Windows: si trova lo stesso."""
    deep = str(tmp_path)
    while len(deep) < 300:
        deep = os.path.join(deep, "Nebulosa della Testa di Cavallo - IC 434 - sessione lunga")
    os.makedirs(long_path(deep), exist_ok=True)
    with open(long_path(os.path.join(deep, "frame.fits")), "wb"):
        pass
    found = walk_dir(str(tmp_path))
    assert len(found) == 1 and found[0].endswith("frame.fits")


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
    assert len(walk_dir(str(tmp_path))) == 1
