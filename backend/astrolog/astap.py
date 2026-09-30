"""Guidare ASTAP, il solver astrometrico: dove sta l'eseguibile, che comando gli si da',
quanto lo si aspetta, e come si legge cio' che ha scritto.

Vincolo non ovvio: **il lancio si passa come argomento** (`run=`), cosi' i test non chiamano
il solver e la suite veloce non dipende da un programma installato a parte. Due bandiere non
si usano MAI: `-update` riscriverebbe il FITS dell'utente, e `-extract` gli lascerebbe un CSV
**accanto al file**, ignorando sia `-o` sia la cartella di lavoro (verificato sul campo). E i
numeri che ASTAP stampa portano il separatore decimale della macchina: su un computer
italiano `HFD_MEDIAN=9,1`.
"""

import contextlib
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .fits.header_keys import as_float
from .fits.header_wcs import solved, wcs_rotation_deg, wcs_scale

log = logging.getLogger(__name__)

# `astap_cli` per primo: non apre finestre, ed e' l'unico che funziona su un NAS senza schermo.
EXE_NAMES = ("astap_cli", "astap")
ENV_EXE = "ASTROLOG_ASTAP"

# Dove si installa da se' sui tre bersagli, se non e' nel PATH.
CANDIDATES = (
    r"C:\Program Files\astap\astap_cli.exe",
    r"C:\Program Files (x86)\astap\astap_cli.exe",
    "/Applications/ASTAP.app/Contents/MacOS/astap_cli",
    "/opt/astap/astap_cli",
    "/usr/local/bin/astap_cli",
)

# Le sigle dei cataloghi stellari, lette dall'elenco dei download dell'autore: le attuali e le
# vecchie, che chi non le ha tolte ha ancora installate e che ASTAP legge lo stesso.
DB_KINDS = ("d05", "d20", "d50", "d80", "v05", "v50", "g05", "w08",
            "h17", "h18", "v17", "g17", "g18")  # fmt: skip

# Il nome di un file di catalogo: sigla, trattino basso, zona di cielo, punto -- `d80_0101.1476`.
# Si guarda il **nome** e non l'estensione, che cambia col formato (`.1476`, `.001`, i vecchi
# `.290`), e senza distinguere maiuscole. **La sigla si controlla contro l'elenco**: un `x99_1.zip`
# qualunque direbbe "catalogo stellare: x99", il "ce l'hai" falso che questa ricerca esiste per non
# fare. Il prezzo -- un catalogo nuovo risulta mancante finche' non entra qui -- e' quello scelto.
DB_NAME = re.compile(r"(" + "|".join(DB_KINDS) + r")_[0-9]+\.", re.IGNORECASE)

# Dieci volte il caso peggiore misurato (23 s, cieco, su 26 megapixel): oltre, e' piantato.
TIMEOUT_S = 60
# Col puntamento dell'header bastano pochi gradi, ma 30 assorbe una montatura scentrata
# senza costare: la leva della velocita' e' il campo, non il raggio (misurato).
SEARCH_RADIUS_DEG = 30
BLIND_RADIUS_DEG = 180

NO_STARS = "no_stars"  # nessuna stella: un file senza tipo e' una calibrazione (`typeless`)
# I motivi per cui una posa resta senza cielo: un elenco CHIUSO di codici, mai la frase di
# ASTAP -- le frasi cambiano da una versione all'altra e finirebbero a schermo in inglese.
REASONS = (NO_STARS, "no_solution", "timeout", "astap_missing", "file_missing",
           "no_star_database", "internal_error")  # fmt: skip

# Cosa dice ASTAP quando fallisce -> il nostro codice. Si confronta in minuscolo e per
# contenimento: il testo esatto cambia, la parola chiave no.
_ERROR_WORDS = (
    ("not enough stars", NO_STARS),
    ("file not found", "file_missing"),
    # ASTAP c'e' ma il suo catalogo no. E' un download separato da ~1 GB, ed e' l'errore di
    # installazione piu' comune -- in DUE modi, che ASTAP dice con due frasi diverse:
    # `No star database found.` (non scaricato, o cartella vuota) e `Error reading star
    # database.` (scaricato a meta', troncato, o unzip andato male). Interrotto a meta' e'
    # comune quanto non fatto, e prendere solo la prima frase lasciava il secondo caso nel
    # vicolo cieco. Frasi lette da ASTAP CLI-2025.11.19, non scritte a memoria: la prima con
    # `-d` su una cartella vuota, la seconda su un file di catalogo troncato.
    ("star database", "no_star_database"),
)


@dataclass(frozen=True)
class Solution:
    """L'esito di un solve: il cielo trovato, oppure il motivo per cui non c'e'."""

    ok: bool
    reason: str | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    scale_arcsec_px: float | None = None
    rotation_deg: float | None = None


# I quattro canali da cui l'eseguibile puo' arrivare, come codici e non come frasi: si mostrano
# a schermo, e una parola nuova ci arriverebbe non tradotta. Elenco chiuso, come `REASONS`.
SOURCES = ("declared", "env", "path", "known_place")


def find_exe(declared=None, env=None, which=shutil.which, candidates=CANDIDATES):
    """Il percorso dell'eseguibile, o `None` se non c'e'. E' `where_exe` senza il canale: chi
    deve solo lanciarlo non ha bisogno di sapere da dove viene.

    **Chiama `_cerca`, non `where_exe`**: le due pubbliche le sostituisce il recinto della suite
    (`tests/conftest.py`), e una che passasse per l'altra raccoglierebbe lo stub anche quando e'
    stata catturata apposta prima."""
    return _cerca(declared, env, which, candidates)[0]


def where_exe(declared=None, env=None, which=shutil.which, candidates=CANDIDATES):
    """Il percorso dell'eseguibile **e da quale dei quattro canali arriva**, o `(None, None)`.

    Il canale serve a schermo: "trovato" senza dire da dove non si puo' smentire, e la ricerca
    automatica sbaglia proprio quando trova **qualcosa** -- un ASTAP vecchio rimasto nel PATH, o
    quello di un altro utente in un posto noto.

    Chi ha gia' il suo ASTAP lo dichiara e vince su tutto: e' la via d'uscita quando la
    ricerca automatica sbaglia. Dichiarato ma inesistente vale `None`, non un ripiego di
    nascosto: chi ha scritto quel percorso deve accorgersi che e' sbagliato. E deve essere un
    **file**: una cartella esiste eccome, e indicare la cartella di installazione invece del
    programma che sta dentro e' l'errore piu' facile da fare -- accettarlo vorrebbe dire
    provare a lanciare una directory a ogni posa.

    Due modi di dichiararlo, e l'ordine conta: la **preferenza dell'utente** (`declared`, che
    arriva dal primo avvio o dalle Impostazioni) viene prima della variabile d'ambiente, che e'
    di chi lancia l'app -- su Docker la mette chi gestisce il NAS, e non deve poter zittire
    quello che l'utente ha scritto guardando lo schermo."""
    return _cerca(declared, env, which, candidates)


def _cerca(declared, env, which, candidates):
    """La ricerca vera, che le due funzioni pubbliche si dividono. Sta sotto di loro perche' il
    recinto della suite sostituisce quelle, non questa."""
    env = os.environ if env is None else env
    scritto, canale = (declared, "declared") if declared else (env.get(ENV_EXE), "env")
    if scritto:
        # Come lo incolla l'utente: *Copia come percorso* di Windows mette le **virgolette**
        # intorno, ed e' il modo piu' comune di prendere un percorso senza riscriverlo. Con le
        # virgolette dentro, il file non si trova mai e l'avviso accuserebbe la cosa sbagliata.
        scritto = scritto.strip().strip("\"'")
        # Un percorso scritto e sbagliato **ferma la ricerca**: ripiegare di nascosto sul PATH
        # direbbe "trovato" a chi ha scritto male, e il canale mentirebbe due volte.
        return (scritto, canale) if Path(scritto).is_file() else (None, None)
    for name in EXE_NAMES:
        found = which(name)
        if found:
            return found, "path"
    for candidate in candidates:
        if Path(candidate).is_file():
            return str(candidate), "known_place"
    return None, None


def star_databases(exe):
    """I cataloghi stellari **accanto all'eseguibile**, per nome e in ordine. Senza, ASTAP parte e
    non riconosce niente (`docs/domini/sito.md`).

    Solo li', e **non** anche nelle cartelle d'installazione note: su una macchina che ha ASTAP,
    un eseguibile indicato altrove risulterebbe col catalogo di un altro programma -- "tutto a
    posto" proprio nel caso che questa funzione esiste per prendere. Il collegamento si scioglie
    prima: se quel che si trova e' un collegamento, la cartella giusta e' dove punta.

    **Si guarda, non si chiede**: interrogare ASTAP vorrebbe dire lanciarlo."""
    if exe is None:
        return ()
    with contextlib.suppress(OSError):  # cartella sparita, disco staccato, permessi negati
        nomi = (DB_NAME.match(f.name) for f in Path(exe).resolve().parent.iterdir())
        return tuple(sorted({m.group(1).lower() for m in nomi if m}))
    return ()


def _run(cmd, timeout_s):
    """L'unico posto che lancia davvero un processo. Chi lo sostituisce nei test passa `run`."""
    done = subprocess.run(  # noqa: S603 - argomenti nostri, nessuna shell
        cmd, capture_output=True, text=True, timeout=timeout_s, check=False
    )
    return done.returncode, done.stdout


def _number(text):
    """Un numero come ASTAP lo stampa: la virgola decimale della macchina vale quanto il
    punto. `None` per cio' che non e' un numero -- mai uno zero di ripiego."""
    if text is None:
        return None
    return as_float(str(text).strip().replace(",", "."))


def read_ini_text(text):
    """Le righe `CHIAVE=valore` di un testo: ASTAP le scrive cosi' nel file di esito e le
    stampa cosi' a schermo, quindi il lettore e' uno solo."""
    out = {}
    for line in (text or "").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip():
            out[key.strip().upper()] = value.strip()
    return out


def read_ini(path):
    """Il file di esito come dizionario. Le sue chiavi sono quelle di un header FITS
    (`PLTSOLVD`, `CRVAL1`, la matrice `CD`), percio' il lettore del WCS che gia' esiste lo
    legge senza modifiche. Un file che non c'e' e' un dizionario vuoto."""
    try:
        return read_ini_text(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def _reason_of(ini):
    """Il codice del fallimento, dalla frase che ASTAP ha scritto."""
    message = str(ini.get("ERROR", "")).lower()
    for words, code in _ERROR_WORDS:
        if words in message:
            return code
    return "no_solution"


def command(fits_path, out_base, *, exe, field_deg=None, ra_deg=None, dec_deg=None):  # noqa: PLR0913
    """Il comando, senza lanciarlo: e' qui che si prova che le due bandiere vietate non ci
    sono e che le unita' sono quelle che ASTAP vuole."""
    cmd = [
        exe,
        "-f",
        str(fits_path),
        "-o",
        str(out_base),
        # Il campo inquadrato e' la leva: col campo giusto 0,2 s, con `0` (cerca da se') 2,3 s
        # sullo stesso frame. Dove l'header non dice focale o pixel si paga la differenza.
        "-fov",
        f"{field_deg:.3f}" if field_deg else "0",
        "-z",
        "0",
        "-wcs",
    ]
    if ra_deg is not None and dec_deg is not None:
        # ASTAP vuole le ORE per l'ascensione retta e la distanza dal polo SUD per la
        # declinazione: sbagliarle non da' errore, da' il cielo di un altro punto del mondo.
        cmd += ["-ra", f"{ra_deg / 15.0:.5f}", "-spd", f"{dec_deg + 90.0:.4f}", "-r",
                str(SEARCH_RADIUS_DEG)]  # fmt: skip
    else:
        cmd += ["-r", str(BLIND_RADIUS_DEG)]
    return cmd


def solve(fits_path, out_base, *, field_deg=None, ra_deg=None, dec_deg=None, exe=None, run=None,  # noqa: PLR0913
          timeout_s=TIMEOUT_S):  # fmt: skip
    """Risolve un frame sul cielo. Scrive `<out_base>.ini` e `<out_base>.wcs` -- dove diciamo
    noi, mai accanto al FITS dell'utente.

    Non solleva mai per colpa del solver: un ASTAP assente, piantato o che non trova stelle
    e' una posa senza cielo col suo motivo, e l'archivio va avanti."""
    if not exe:
        return Solution(ok=False, reason="astap_missing")
    cmd = command(fits_path, out_base, exe=exe, field_deg=field_deg, ra_deg=ra_deg, dec_deg=dec_deg)
    try:
        (run or _run)(cmd, timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError):
        log.info("astap: tempo scaduto", extra={"file": str(fits_path)})
        return Solution(ok=False, reason="timeout")
    except OSError as err:
        log.warning("astap: non si e' potuto lanciare", extra={"error": str(err)})
        return Solution(ok=False, reason="astap_missing")

    return from_ini(read_ini(f"{out_base}.ini"))


def from_ini(ini):
    """Il cielo trovato, dal file di esito. E' anche la via della cache: un frame gia' risolto
    non si ri-risolve, si rilegge da qui.

    Un esito a meta' (ASTAP ucciso mentre scriveva, disco pieno) puo' dire `PLTSOLVD=T` e non
    avere i numeri: senza questa guardia finirebbe nel database come un cielo con dei buchi,
    e ci resterebbe. Vale come nessuna soluzione, cosi' chi legge la cache la butta e
    ri-risolve."""
    if not solved(ini):
        return Solution(ok=False, reason=_reason_of(ini))
    found = Solution(
        ok=True,
        ra_deg=as_float(ini.get("CRVAL1")),
        dec_deg=as_float(ini.get("CRVAL2")),
        scale_arcsec_px=wcs_scale(ini),
        rotation_deg=wcs_rotation_deg(ini),
    )
    if None in (found.ra_deg, found.dec_deg, found.scale_arcsec_px):
        return Solution(ok=False, reason="no_solution")
    return found


def analyse(fits_path, *, exe=None, run=None, timeout_s=TIMEOUT_S):
    """`(HFD mediana, stelle)` da una seconda passata di ASTAP, o `(None, None)`.

    E' l'unica strada per questi due numeri che non lasci file nella cartella dell'utente:
    `-extract` scriverebbe un CSV accanto al FITS. Costa ~0,3 s a posa."""
    if not exe:
        return None, None
    try:
        _code, out = (run or _run)([exe, "-f", str(fits_path), "-analyse", "30"], timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError, OSError):
        return None, None
    values = read_ini_text(out)
    stars = _number(values.get("STARS"))
    return _number(values.get("HFD_MEDIAN")), None if stars is None else int(stars)
