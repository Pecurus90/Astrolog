"""**La cartella di una posa**: quella che contiene il file, e la chiave con cui una risposta per
cartella la ritrova. La legge la domanda che si fa per cartella -- i frame che non dicono che file
sono (`spine/typeless.py`), perche' la scansione salta i file nuovi senza tipo di una cartella
detta di calibrazione -- e la stessa chiave in SQL (`spine/stages.py`). Le domande sulla camera,
sull'ottica e sul nome ne prendono solo la giunzione sulle cartelle vive (`spine/rigless.py`,
`spine/rig_optics.py`, `spine/unnamed.py`).

Vincoli non ovvi:

* **La cartella che contiene i file, non la radice registrata**: una radice sola con l'albero di un
  software di acquisizione dentro darebbe un gruppo solo. Non e' una colonna, si ricava dal percorso
  della posizione; nella chiave le barre sono sempre in avanti, cosi' e' la stessa su Windows, su
  Mac e sul NAS.
* **Una posa sta in una cartella sola**: quella della sua prima posizione presente in una cartella
  non ritirata. Lo stesso file in due cartelle potrebbe ricevere due risposte diverse, e un file che
  non si trova piu' o una cartella ritirata non chiedono niente.
* **La chiave non si spezza mai**: radice e sottocartella viaggiano nella riga, e chi cerca la
  risposta di una posa la ricostruisce con `folder_key`. Un percorso contiene di tutto, e qualunque
  regola per rileggerlo dalla chiave sbaglia su un archivio vero, in silenzio.
"""

_FIRST_POSITION = """
  SELECT p2.id FROM positions p2 JOIN folders d2 ON d2.id = p2.folder_id
  WHERE p2.frame_id = f.id AND p2.status = 'present' AND d2.retired_at IS NULL
  ORDER BY p2.id LIMIT 1
"""

# La cartella dentro la radice: `rtrim` toglie da destra ogni carattere che NON e' una barra --
# cioe' il nome del file -- e lascia `notte/M51/`. Un file nella radice non ha barre e resta
# vuoto: la sua cartella e' la radice. Chi raggruppa per cartella mette `COLUMNS` nella SELECT e
# `JOIN` dopo `frames f`; chi cerca le pose di una cartella usa `frames_in`.
_SUB = "rtrim(p.rel_path, replace(p.rel_path, '/', ''))"
COLUMNS = f"d.root_path AS root, {_SUB} AS sub"
JOIN = f"JOIN positions p ON p.id = ({_FIRST_POSITION}) JOIN folders d ON d.id = p.folder_id"

# La stessa chiave di `folder_key`, ma in SQL: serve a chi deve confrontarla dentro una query
# (`spine/stages.py`, per sapere se quella cartella ha gia' una risposta). Le due lingue dicono
# la stessa cosa e un test le tiene incollate (`test_typeless.py`): qui la barra rovescia
# diventa dritta, la barra in coda cade, e una sottocartella vuota non aggiunge niente.
_ROOT_KEY = r"rtrim(replace(d.root_path, '\', '/'), '/')"
_DENTRO = f"trim({_SUB}, '/')"
KEY = f"{_ROOT_KEY} || CASE WHEN {_DENTRO} = '' THEN '' ELSE '/' || {_DENTRO} END"
# La chiave della cartella di `f`, da mettere dentro una query che ha gia' `frames f`.
KEY_OF_FRAME = (
    f"SELECT {KEY} FROM positions p"  # noqa: S608 - costanti
    f" JOIN folders d ON d.id = p.folder_id WHERE p.id = ({_FIRST_POSITION})"
)

# Le pose di una cartella si cercano **partendo dalla cartella**: per indice alle sue posizioni
# sotto quella sottocartella, poi la posa, poi se quella e' la sua prima posizione viva. Partire
# dalle pose ricomporrebbe la cartella di ognuna dell'archivio a ogni risposta.
_IN_FOLDER = (
    "SELECT f.id, f.image_type FROM folders d"  # noqa: S608 - costanti di questo file
    " CROSS JOIN positions p ON p.folder_id = d.id"
    " CROSS JOIN frames f ON f.id = p.frame_id"
    f" WHERE d.root_path = ? AND p.rel_path >= ? AND p.rel_path < ? AND {_SUB} = ?"
    f" AND p.id = ({_FIRST_POSITION})"
)
# Dove finiscono i percorsi sotto una sottocartella: `notte/` va da `notte/` a `notte0`, perche'
# `0` e' il carattere subito dopo la barra. Sotto la radice va tutto: la fine e' un BLOB vuoto,
# che per SQLite viene dopo ogni testo, qualunque carattere contenga.
_AFTER_EVERY_PATH = b""


def folder_key(root_path, sub=""):
    """Il percorso della cartella che contiene i file: la chiave del gruppo, ed e' anche cio' che si
    mostra. Le barre sono sempre in avanti -- Windows le accetta, e una chiave col separatore del
    sistema direbbe due cose diverse su due macchine."""
    root = root_path.replace("\\", "/").rstrip("/")
    dentro = sub.strip("/")
    return f"{root}/{dentro}" if dentro else root


def key_of_path(root_path, rel_path):
    """La chiave della cartella che conterrebbe quel file, senza passare dal DB: la vuole chi deve
    decidere **prima** di scrivere il frame (`spine/scan.py`). Sta qui, con `folder_key`, perche'
    "la cartella e' il percorso senza il nome del file" e' un fatto solo."""
    dritto = rel_path.replace("\\", "/")
    return folder_key(root_path, dritto.rsplit("/", 1)[0] if "/" in dritto else "")


def frames_in(conn, row):
    """Le pose della cartella di quel gruppo, **copie comprese**, col tipo di file: chi risponde
    sceglie quali rimettere in coda. Si cerca con radice e sottocartella della riga, mai spezzando
    la chiave."""
    sub = row["sub"]
    end = sub[:-1] + "0" if sub else _AFTER_EVERY_PATH
    return conn.execute(_IN_FOLDER, (row["root"], sub, end, sub)).fetchall()


def group_of(groups, row, **fields):
    """Il gruppo della cartella di questa riga in `groups`, creato con i campi `fields` la prima
    volta. Radice e sottocartella restano nel gruppo, perche' chi risponde ritrovi le pose senza
    spezzare la chiave."""
    key = folder_key(row["root"], row["sub"])
    return groups.setdefault(key, {"key": key, "root": row["root"], "sub": row["sub"], **fields})


def counted(conn, query, *, skip=None):
    """Le cartelle di una domanda che conta e basta, la piu' numerosa in cima.

    `skip` scarta una riga prima di contarla, dove la domanda non vale per tutte. Una cartella
    rimasta a zero non chiede niente: li' dentro ci sono solo copie, e una domanda su zero pose non
    si capisce."""
    groups = {}
    for row in conn.execute(query):
        if skip and skip(row):
            continue
        group_of(groups, row, frames=0)["frames"] += row["n"] or 0
    return sorted(
        (g for g in groups.values() if g["frames"]), key=lambda g: (-g["frames"], g["key"])
    )
