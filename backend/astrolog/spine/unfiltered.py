"""Le pose che non dicono il filtro, raggruppate per **camera** (Marco, 2026-09-11): la domanda,
le sue risposte e cosa rimettono in coda.

E' la casa comune fra lo stadio che le lascia col filtro vuoto (`normalize`) e la pagina che le
chiede: la sezione di Da confermare legge di qui, e la risposta si scrive come dichiarazione sulla
camera.

Vincoli non ovvi:

* **Una camera a colori non si chiede** (Marco, 23/9/2026): se la scheda o il voto dei file la
  dicono a colori, le sue pose senza filtro sono OSC. Un duo-banda che il file non scrive, su una
  camera a colori, non lo vede nessuno.
* **Senza `BAYERPAT` una mono e una camera a colori non si distinguono**: "FILTER assente" e
  "FILTER=none" sono la stessa domanda, che camera e'. Si chiede per camera, mai per posa ne' per
  cartella: la risposta e' un fatto sulla camera, e vale per le pose che verranno.
* **Tre risposte** (Marco, 25/9/2026): a colori, nessun filtro, oppure uno dei tuoi filtri, che si
  scrive col suo **nome** e ne segue le rinomine e le unioni (`follow_filter`). Chi cambiava
  filtri senza scriverli non ha una risposta: quelle pose restano senza filtro.
* **Il gruppo si riconosce dal grezzo, non dal filtro gia' dato**: un gruppo a cui si e' risposto
  resta in pagina con la risposta, anche quando le sue pose hanno ormai un filtro.
"""

from ..vocab.filters import NO_FILTER, normalize_filter, passband_of
from . import declarations as decl
from . import objects as obj
from .stages import WAITING_SQL, invalidate

# Le risposte. "A colori" E' il colore della scheda, la stessa parola; le altre due hanno un campo
# loro sulla camera (`declarations.UNFILTERED`), e "uno dei tuoi" dice quale in un altro
# (`declarations.UNFILTERED_FILTER`).
COLOR, NO_FILTER_ANSWER, FILTER_ANSWER = decl.CAMERA_COLOR, "no_filter", "filter"
ANSWERS = (COLOR, NO_FILTER_ANSWER, FILTER_ANSWER)

# Una riga per camera e oggetto, non una per posa. Le copie riscritte non si contano:
# non sono un'altra posa. Nemmeno quelle con la matrice: sono OSC, e la risposta non le sposta. Ne'
# chi aspetta di sapere che file e' (`spine/typeless.py`): puo' essere un dark.
_BY_CAMERA = f"""
SELECT i.name, {obj.SUBJECT} AS subject, COUNT(*) AS n
FROM frames f JOIN rigs r ON r.id = f.rig_id JOIN instruments i ON i.id = r.camera_id
{obj.SUBJECT_JOIN}
WHERE f.copy_of IS NULL AND f.bayer_pattern IS NULL AND f.asks_filter = 1 AND NOT ({WAITING_SQL})
GROUP BY i.id, subject
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente

_COLOUR = "SELECT camera_type FROM instruments WHERE kind = 'camera' AND name = ?"

_OF_CAMERA = """
SELECT f.id FROM frames f JOIN rigs r ON r.id = f.rig_id
WHERE r.camera_id = ? AND f.bayer_pattern IS NULL
"""


def _voted_colour(conn, camera_name):
    """Se sono i FILE a dire quella camera a colori: la colonna del rilevato, che vota a fine
    corsa (`spine/camera_specs.py`). Non c'entra cio' che l'utente ha scritto sulla scheda."""
    row = conn.execute(_COLOUR, (camera_name,)).fetchone()
    return row is not None and row["camera_type"] == COLOR


def is_colour(conn, camera_name, voted=None):
    """Se quella camera e' a colori: prima cio' che l'utente ha scritto sulla scheda, poi cio' che
    i file hanno votato -- la stessa precedenza con cui la pagina mostra la scheda
    (`gear.camera_specs`). `voted` e' il voto che la normalizzazione fa prima del giro
    (`camera_specs.ahead`); senza, quello scritto sulla camera.

    E' un fatto sulla CAMERA, non sulla posa: il programma che non scrive `BAYERPAT` non fa una
    posa mono in mezzo alle altre."""
    if not camera_name:
        return False
    written = written_colour(conn, camera_name)
    if written is not None:
        return written == COLOR
    if voted is not None:
        return voted.get(camera_name) == COLOR
    return _voted_colour(conn, camera_name)


def written_colour(conn, camera_name):
    """Il colore che l'utente ha scritto sulla scheda di quella camera, o `None`: dove c'e', il
    voto dei file non conta."""
    key = decl.instrument_key("camera", camera_name)
    return decl.declared(conn, "instrument", key, "camera_type")


def declare(conn, camera_name, answer, filter_name=None, now=None):
    """La risposta su una camera. Le due risposte che non sono "a colori" scrivono anche mono sulla
    scheda, ma **solo se non sono i file a dirla a colori**: un "a colori" scritto prima lo
    riscrivono, o cambiare idea non sposterebbe niente; il colore che viene dai file no, perche'
    li' la risposta parla del filtro e il sensore lo dicono loro."""
    if answer == COLOR:
        decl.declare_instrument_spec(conn, "camera", camera_name, "camera_type", COLOR, now)
        return
    if not _voted_colour(conn, camera_name):
        spec = decl.CAMERA_MONO
        decl.declare_instrument_spec(conn, "camera", camera_name, "camera_type", spec, now)
    key = decl.instrument_key("camera", camera_name)
    decl.write_declaration(conn, "instrument", key, decl.UNFILTERED, answer, now)
    if answer == FILTER_ANSWER:
        decl.write_declaration(conn, "instrument", key, decl.UNFILTERED_FILTER, filter_name, now)


def said(conn, camera_name):
    """Cosa l'utente ha risposto su quella camera se non e' a colori: `(risposta, filtro)`, dove il
    filtro c'e' solo con "uno dei tuoi"; `(None, None)` senza risposta. "A colori" si scrive sulla
    scheda, e una camera a colori non si chiede."""
    if not camera_name:
        return None, None
    key = decl.instrument_key("camera", camera_name)
    risposta = decl.declared(conn, "instrument", key, decl.UNFILTERED)
    if risposta != FILTER_ANSWER:
        return risposta, None
    return risposta, decl.declared(conn, "instrument", key, decl.UNFILTERED_FILTER)


def follow_filter(conn, old_name, new_name):
    """Porta la risposta "uno dei tuoi filtri" sul nome nuovo, quando quel filtro cambia nome o
    finisce dentro un altro: senza, le pose di quella camera perderebbero il filtro."""
    conn.execute(
        "UPDATE declarations SET value = ? WHERE entity_type = 'instrument' AND field = ?"
        " AND value = ?",
        (new_name, decl.UNFILTERED_FILTER, old_name),
    )


def says_no_filter(filter_raw):
    """Il filtro scritto non dice niente: manca, e' spazzatura, o dice "nessuno"."""
    canonical = normalize_filter(filter_raw, bayer=False)
    return canonical is None or passband_of(canonical) == NO_FILTER


def by_camera(conn):
    """Le camere non a colori con pose che non dicono il filtro, la piu' numerosa in cima: quante
    pose, la risposta gia' data e, per "uno dei tuoi", l'id del filtro (`None` se non c'e' piu')."""
    colore = {}
    gruppi = {}
    for r in conn.execute(_BY_CAMERA):
        if r["name"] not in colore:
            colore[r["name"]] = is_colour(conn, r["name"])
        if not colore[r["name"]]:
            gruppo = gruppi.setdefault(r["name"], {"key": r["name"], "frames": 0})
            gruppo["frames"] += r["n"]
            obj.count_subject(gruppo, r["subject"], r["n"])
    out = []
    for g in obj.subjects(conn, gruppi.values()):
        risposta, filtro = said(conn, g["key"])
        riga = conn.execute("SELECT id FROM filters WHERE name = ?", (filtro,)).fetchone()
        out.append({**g, "answer": risposta, "filter_id": riga and riga["id"]})
    return sorted(out, key=lambda g: (-g["frames"], g["key"]))


def requeue(conn, camera_id):
    """Rimette in coda le pose che una risposta su quella camera puo' cambiare, e le torna: quelle
    **senza** matrice di Bayer, comprese le copie e quelle a cui una risposta precedente aveva gia'
    dato un filtro -- o cambiare idea non sposterebbe niente.

    Una posa con la matrice non c'e': la risposta **per camera** non puo' spostarla -- e' OSC
    qualunque cosa dica -- quindi rilavorarla sarebbe lavoro che nasce morto (misurato: 3.000
    rimesse in coda e 0 cambiate) e riaprirebbe anche `identify` e `group`."""
    frames = [r[0] for r in conn.execute(_OF_CAMERA, (camera_id,))]
    invalidate(conn, frames, "normalize")
    return frames
