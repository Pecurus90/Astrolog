"""Raccoglie i file FITS di una cartella, in profondita'.

Vincolo non ovvio: iterativo (niente ricorsione su alberi profondi), ordinato (scansioni
ripetibili), collegamenti e giunzioni non seguiti (niente cicli); cio' che resta fuori --
cartelle illeggibili, nascoste, collegate, file solo online -- si riporta al chiamante invece di
sparire. Le estensioni ammesse sono una decisione di prodotto (`docs/domini/spina.md`).
"""

import math
import os
import re
import stat
import sys
import time

FITS_EXTENSION_RE = re.compile(r"\.(fits|fit)$", re.IGNORECASE | re.ASCII)

# Il sistema su cui gira decide quale segno si guarda. Una costante sola: i test la impostano
# per provare tutti e tre i rami su qualunque macchina.
PLATFORM = sys.platform

# Un file "solo online" (OneDrive, Dropbox, iCloud) sul disco e' un segnaposto, e aprirlo lo
# scarica. Il sistema lo dice con un segno che il modulo `stat` di Python non conosce.
# Windows, *File Attribute Constants* (Microsoft): RECALL_ON_DATA_ACCESS e' "not fully present
# locally", RECALL_ON_OPEN "only appears in directory enumeration classes" -- ed e' per questo
# che il segno si legge dall'elenco della cartella e non con uno stat a parte --, OFFLINE e' il
# dato spostato su un archivio remoto. Mac, *TN3150* (Apple): SF_DATALESS in `st_flags`, che in
# `bsd/sys/stat.h` di xnu vale 0x40000000. Linux non ha il segno.
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
SF_DATALESS = 0x40000000
# Prima di macOS Sonoma iCloud Drive non metteva il segno: al posto del file lasciava un
# segnaposto nascosto di pochi byte, `.Nome.fits.icloud` (The Eclectic Light Company, *How
# iCloud Drive works in macOS Sonoma*). Si riconosce dal nome, su qualunque sistema lo si legga.
ICLOUD_STUB_RE = re.compile(r"^\.(.+\.(?:fits|fit))\.icloud$", re.IGNORECASE | re.ASCII)

# Dove guardare, per sistema: il campo dello stat e i bit che vogliono dire "non sul disco".
_NOT_ON_DISK = {
    "win32": (
        "st_file_attributes",
        FILE_ATTRIBUTE_RECALL_ON_OPEN
        | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
        | stat.FILE_ATTRIBUTE_OFFLINE,
    ),
    "darwin": ("st_flags", SF_DATALESS),
}

# Il limite di Windows e' 260 caratteri; questo e' il margine oltre il quale si passa alla
# forma `\\?\`, che non ha limite. Una cartella di archivio profonda lo supera davvero, e
# sotto la soglia la forma normale resta leggibile nei messaggi e nei log.
LONG_PATH_THRESHOLD = 240


def long_path(path):
    """Il percorso in una forma che il sistema apre anche oltre i 260 caratteri (Windows).

    Una **cartella di rete** vuole la sua forma: `\\\\?\\UNC\\server\\share\\...`, non
    `\\\\?\\\\\\server\\share` -- e' scritto nella documentazione di Windows (*Maximum Path
    Length Limitation*), e col prefisso sbagliato la cartella non si apre. La stessa pagina
    dice che col prefisso le barre in avanti **non** valgono come separatore: si normalizza."""
    p = str(path)
    if os.name != "nt" or len(p) <= LONG_PATH_THRESHOLD or p.startswith("\\\\?\\"):
        return p
    intero = os.path.abspath(p)  # su Windows normalizza anche le barre in avanti
    if intero.startswith("\\\\"):  # \\server\share -> \\?\UNC\server\share
        return "\\\\?\\UNC" + intero[1:]
    return "\\\\?\\" + intero


def _apple_double(name):
    """Il gemello che macOS scrive accanto a ogni file su una chiavetta o un NAS: `._M42.fits`
    accanto a `M42.fits`. Sono i metadati del Finder, non un FITS -- pochi KB che la lettura
    non apre. Senza questa riga, un archivio passato da un Mac dice "1.200 file non letti" su
    1.200 pose sane."""
    return name.startswith("._")


def _hidden(entry):
    """La cartella e' nascosta: il cestino e le cartelle di servizio lo sono su tutti e tre i
    sistemi (`.Trashes` e `.Spotlight-V100` su Mac, `$RECYCLE.BIN` e `System Volume
    Information` su Windows con l'attributo nascosto, il cestino di un NAS via SMB). Dentro un
    cestino ci sono le pose che l'utente ha CANCELLATO: rientrerebbero in archivio.

    Si guarda la proprieta', non una lista di nomi: un nome scritto a memoria copre il NAS che
    conosciamo e nessun altro. La radice che l'utente indica non passa da qui e non si salta
    mai, anche se nascosta: si filtrano solo le sottocartelle che si incontrano."""
    if entry.name.startswith("."):
        return True
    if PLATFORM != "win32":  # l'attributo esiste solo la': altrove sarebbe una lstat per cartella
        return False
    try:
        attributi = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributi & stat.FILE_ATTRIBUTE_HIDDEN)


def _online_only(entry):
    """Il file e' il segnaposto di un servizio di sincronizzazione. Il segno arriva con l'elenco
    della cartella -- su Windows gratis, sul Mac con una lstat --, e dove il sistema non ce l'ha
    non si chiede. Se il segno non si legge il file si considera sul disco, come sempre."""
    sign = _NOT_ON_DISK.get(PLATFORM)
    if sign is None:
        return False
    field, mask = sign
    try:
        return bool(getattr(entry.stat(follow_symlinks=False), field, 0) & mask)
    except OSError:
        return False


# Cosa il walk fa di una voce d'elenco. Una decisione sola, per il walk e per l'elenco da cui si
# sceglie una cartella: se fossero due, prima o poi direbbero due cose diverse.
LINKED, HIDDEN, WALKED, FILE = "linked", "hidden", "walked", "file"


def _kind(entry):
    """La percorre (`WALKED`), la lascia fuori perche' collegata o nascosta, o la guarda come
    file. Un collegamento o una giunzione di Windows non si segue: per Python la giunzione e' una
    cartella qualunque -- `is_dir(follow_symlinks=False)` vero, `is_symlink` falso, provato su
    Windows --, e solo `is_junction` la distingue. Una voce che non risponde si guarda come file."""
    try:
        if entry.is_junction() or (entry.is_symlink() and entry.is_dir()):
            return LINKED
        is_dir = entry.is_dir()  # qui non e' un collegamento: seguirlo o no e' lo stesso
    except OSError:
        return FILE
    if not is_dir:
        return FILE
    return HIDDEN if _hidden(entry) else WALKED


def subfolders(path):
    """I nomi delle sottocartelle che si possono scegliere sotto `path`, ordinati: quelle che il
    walk percorrerebbe. Se la cartella non si apre, l'errore sale a chi chiama."""
    with os.scandir(long_path(path)) as scan:
        return sorted(e.name for e in scan if _kind(e) == WALKED)


def walk_dir(  # noqa: PLR0913
    root,
    found=None,
    unreadable=None,
    hidden=None,
    online_only=None,
    linked=None,
    deadline=math.inf,
    unvisited=None,
):
    """I percorsi assoluti dei FITS sotto `root`, ordinati. Una radice inesistente da' la
    lista vuota (o l'accumulatore `found` com'era): il pre-controllo della radice e' del
    chiamante, che sa distinguere una cartella sparita da un disco staccato.

    Accanto, se il chiamante le vuole, cio' che resta fuori: le cartelle che non si sono aperte
    (`unreadable`), le sottocartelle nascoste (`hidden`) e quelle raggiunte da un collegamento
    (`linked`), i FITS solo online (`online_only`). Con una scadenza (`deadline`, sull'orologio
    di `time.monotonic`) il walk si ferma e mette in `unvisited` le cartelle che non ha guardato."""
    found, unreadable, hidden, online_only, linked, unvisited = (
        [] if items is None else items
        for items in (found, unreadable, hidden, online_only, linked, unvisited)
    )
    stack = [root]
    while stack:
        if time.monotonic() >= deadline:
            unvisited.extend(stack)
            break
        current = stack.pop()
        try:
            scan = os.scandir(long_path(current))
        except OSError:
            unreadable.append(current)
            continue
        subdirs, fits_here, stubs = [], set(), []
        folders_by_kind = {LINKED: linked, HIDDEN: hidden, WALKED: subdirs}
        with scan:
            for entry in scan:
                full = os.path.join(current, entry.name)
                kind = _kind(entry)
                if kind != FILE:
                    folders_by_kind[kind].append(full)
                elif _apple_double(entry.name):
                    continue  # anche il gemello di un segnaposto: non e' un file in piu'
                elif FITS_EXTENSION_RE.search(entry.name):
                    fits_here.add(entry.name.casefold())
                    (online_only if _online_only(entry) else found).append(full)
                elif stub := ICLOUD_STUB_RE.match(entry.name):
                    stubs.append(stub.group(1))
        # un segnaposto accanto al suo file vero non e' un secondo file: quello e' sul disco
        online_only.extend(
            os.path.join(current, name) for name in stubs if name.casefold() not in fits_here
        )
        stack.extend(subdirs)
    for items in (found, hidden, online_only, linked):
        items.sort()
    return found
