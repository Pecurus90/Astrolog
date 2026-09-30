"""I frame che non dicono **che file sono**, raggruppati per **cartella** (Marco, 17/9/2026): la
domanda, la sua risposta, e perche' restano fermi prima dell'oggetto.

Un header senza `IMAGETYP` non dice "light": lo lasciano muto i programmi che non lo scrivono, e
quel file puo' essere una foto del cielo come un dark. Lo dice il cielo (Marco, 23/9/2026):
risolto e' una foto, senza stelle e' una calibrazione. Si chiede, per cartella, solo dove il cielo
non sa dire: ha rinunciato per qualunque altro motivo (nessuna soluzione, tempo scaduto, un errore).

Vincoli non ovvi:

* **Finche' non si sa che file e', non c'e' oggetto.** La regola sta in `spine/stages.py` e il suo
  esito e' scritto sulla posa (`frames.asks_type`), non fra gli stati degli stadi, che la prima
  `invalidate` cancellerebbe: quei frame non entrano ne' in `ready` ne' nel residuo di cio' che
  viene dopo il cielo. Una risposta lo riscrive per ogni posa senza tipo. Quindi non diventano
  ore e non finiscono fra i **Frame senza nome**, dove la domanda e' "cosa hai ripreso" e non
  "che file e'": rispondere li' con un oggetto trasformerebbe una calibrazione in ore.
* **"E' un file di calibrazione" non toglie il frame dall'archivio.** I file di calibrazione nuovi
  non entrano affatto (`spine/scan.py` li salta alla porta, e la ricevuta li conta per motivo), ma
  quelli gia' in archivio restano, anche quando ci arrivano spostati da un'altra cartella (una
  copia resta della cartella dell'originale finche' l'originale resta dov'era, in una cartella che
  l'app legge): cancellarli farebbe sparire il gruppo dalla pagina, e una risposta si deve poter
  cambiare. Restano pero' **staccati** da cio' che il cielo aveva scritto quando il cielo o una
  risposta li avevano mandati avanti: senza, le loro ore resterebbero attaccate a un oggetto che
  non rifara' mai i conti.
* **Il gruppo si riconosce dal GREZZO** -- `frames.image_type` resta `unknown` anche dopo la
  risposta -- o un gruppo risposto sparirebbe dalla pagina e cambiare idea sarebbe impossibile.
* **Un frame che non sta piu' in nessuna cartella viva** (il file non c'e' piu', o la cartella e'
  stata ritirata) non ha una chiave: nessuna risposta vale per lui, e conta solo il cielo. Se il
  cielo non l'ha riconosciuto -- o il cielo che aveva gliel'ha tolto uno stacco -- aspetta, e
  sparisce insieme dalla pagina e dal residuo: nessuno lo chiede e nessuno lo aspetta. Niente gli
  si stacca e niente torna in fila dal cielo. Se il file ricompare, torna tutto da se'.
"""

from ..fits.frame_type import UNKNOWN
from . import declarations as decl
from . import frame_folder as folder
from .stages import refresh_waiting

# Le due risposte. Le parole vivono in `spine/declarations.py` col resto del vocabolario delle
# dichiarazioni, perche' le legge anche `spine/stages.py` per sapere chi e' pronto: qui si
# rinominano soltanto, cosi' chi legge questo modulo non deve andarle a cercare.
LIGHT, CALIBRATION = decl.TYPE_LIGHT, decl.TYPE_CALIBRATION
ANSWERS = (LIGHT, CALIBRATION)


# Le cartelle scritte (`spine/typeless_folders.py`), con la risposta letta dalla sua casa.
_WRITTEN = f"""
SELECT t.key, t.root, t.sub, t.frames, dc.value AS answer FROM typeless_folders t
LEFT JOIN declarations dc ON dc.entity_type = '{decl.FOLDER}' AND dc.field = '{decl.FOLDER_TYPE}'
  AND dc.entity_key = t.key
"""  # noqa: S608 - un frammento costante di questo file, non un valore dell'utente


def by_folder(conn, only=None):
    """Le cartelle con frame che non dicono che file sono e che il cielo non sa dire, la piu'
    numerosa in cima: quanti frame e la risposta gia' data. Una cartella gia' risposta resta, e
    ognuna conta tutti i suoi frame senza tipo, perche' la risposta li sposta tutti. Si leggono
    come le ha scritte `typeless_folders.write`, che dice quando.

    `only` tiene una cartella sola: chi risponde vuole quella riga."""
    where, args = (" WHERE t.key = ?", (only,)) if only is not None else ("", ())
    rows = conn.execute(_WRITTEN + where + " ORDER BY t.position", args)
    return [
        {"key": r["key"], "root": r["root"], "sub": r["sub"], "frames": r["frames"],
         "answer": r["answer"] if r["answer"] in ANSWERS else None}
        for r in rows
    ]  # fmt: skip


def row_of(conn, key):
    """La riga di quel gruppo come la pagina la mostra, o `None` se non c'e' piu': e' cosi' che una
    risposta ritrova il gruppo, senza rileggere la chiave a pezzi."""
    return next(iter(by_folder(conn, only=key)), None)


def declare(conn, key, kind, now=None):
    """La risposta su una cartella, riscrivibile: si cambia idea rispondendo di nuovo. Si scrive la
    parola, non un numero di riga: la dichiarazione deve sopravvivere a un azzeramento del
    rilevato, e la cartella e' la sua chiave."""
    if kind not in ANSWERS:  # una parola fuori vocabolario non e' una risposta a meta': e' un bug
        raise ValueError(f"risposta che non esiste: {kind!r}")
    decl.write_declaration(conn, decl.FOLDER, key, decl.FOLDER_TYPE, kind, now)
    refresh_waiting(conn)


def answer(conn, key):
    """La risposta data per quella cartella, o `None`. Una riga storta vale **nessuna risposta**: i
    frame restano fermi invece di diventare ore su un'ipotesi."""
    value = decl.declared(conn, decl.FOLDER, key, decl.FOLDER_TYPE) if key else None
    return value if value in ANSWERS else None


def answer_at(conn, root_path, rel_path):
    """La risposta della cartella che conterrebbe quel file, o `None`. La scansione deve saperlo
    **prima** di scrivere il frame: la chiave si compone dal percorso, senza passare dal DB."""
    return answer(conn, folder.key_of_path(root_path, rel_path))


def frames_of(conn, row):
    """Gli id dei frame di quel gruppo che non dicono che file sono, **copie comprese**: anche una
    copia ha il suo cielo, e a video invece non si conta, come in ogni conteggio."""
    return [r["id"] for r in folder.frames_in(conn, row) if r["image_type"] == UNKNOWN]
