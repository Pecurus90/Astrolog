"""Le dichiarazioni dell'utente e le regole imparate: chi le scrive, e cosa rimette in coda.

Vincolo non ovvio: una dichiarazione si aggancia a una chiave che sopravvive a un
azzeramento del rilevato (il nome del pezzo, mai il numero di riga), e ogni scrittura che
cambia cio' che la spina ha dedotto passa da `invalidate`: e' l'unica via.

Anche la **lettura** del dichiarato sta qui, e non nello store di uno stadio: la usano piu'
stadi, e il contratto vieta a uno stadio di importare da un altro. Un fatto, una casa.
"""

from ..clock import now_iso
from ..vocab.header_value import normalize_header_value
from ..vocab.object_label import clean_object_name
from . import counts

CONFIRMED = "confirmed"

# Solo questi tipi possono avere una regola: `header_aliases.kind` e' un dominio chiuso, e il
# criterio e' **chi lo crea la spina**. Ci sta ogni genere che nasce da un header -- l'ottica e
# la camera, la montatura (che l'ASIAIR scrive in `TELESCOP`), e i tre che la posa nomina addosso
# a se' (`counts.ON_THE_FRAME`) -- perche' senza la regola, chi rinomina il suo pezzo se lo
# ritrova doppio alla prima notte nuova, con le ore spartite fra due righe.
# `filter` e `object` non stanno qui perche' non si UNISCONO due grafie fra loro: si dichiara
# dove va una grafia, e basta. Che questo elenco e il `CHECK` dello schema restino d'accordo lo
# prova `test_every_kind_that_learns_a_spelling_is_one_the_schema_accepts`.
ALIAS_KINDS = ("optics", "camera", "mount", *counts.ON_THE_FRAME)


class UnknownTargetError(ValueError):
    """La risposta punta a una voce di catalogo che non esiste."""


def declared(conn, entity_type, entity_key, field):
    """Il valore dichiarato dall'utente, o None. La presenza della riga vince sul rilevato."""
    if entity_key is None:
        return None
    row = conn.execute(
        "SELECT value FROM declarations WHERE entity_type = ? AND entity_key = ? AND field = ?",
        (entity_type, entity_key, field),
    ).fetchone()
    return None if row is None else row["value"]


def write_declaration(conn, entity_type, entity_key, field, value, now=None):  # noqa: PLR0913
    """Scrive una dichiarazione; riscriverla la aggiorna. Una casa sola per le scritture che
    sostituiscono il valore: chi dichiara sceglie tipo, chiave e campo."""
    conn.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES(?, ?, ?, ?, ?)"
        " ON CONFLICT(entity_type, entity_key, field) DO UPDATE SET value = excluded.value",
        (entity_type, entity_key, field, value, now or now_iso()),
    )


def forget(conn, entity_type, entity_key, field):
    """Toglie una dichiarazione, se c'e', e torna quante ne ha tolte: la domanda torna aperta."""
    return conn.execute(
        "DELETE FROM declarations WHERE entity_type = ? AND entity_key = ? AND field = ?",
        (entity_type, entity_key, field),
    ).rowcount


def alias_target(conn, kind, header_value):
    """La regola imparata per quel valore d'header, o None."""
    row = conn.execute(
        "SELECT target_key FROM header_aliases WHERE kind = ? AND header_value = ?",
        (kind, header_value),
    ).fetchone()
    return None if row is None else row["target_key"]


def instrument_name(conn, kind, raw):
    """Il nome del pezzo dietro un valore d'header -- regola imparata -> il nome com'e' scritto --
    o `None` se quel valore non dice niente.

    Sta qui e non in uno stadio perche' la leggono in due: `normalize` per attaccare la posa al
    pezzo, e `spine/rigless.py` per proporre a video l'ottica che le pose portano. Due letture
    diverse della stessa grafia vorrebbero dire proporre il nome vecchio di un pezzo rinominato, e
    farne nascere un secondo accanto a quello."""
    key = normalize_header_value(raw)
    if not key:
        return None
    return alias_target(conn, kind, key) or raw.strip()


def instrument_key(kind, name):
    return f"{kind}|{name}"


# I campi della scheda di una camera che anche i file sanno dire. La parola dell'utente su di
# loro sta qui e non nella colonna: la colonna e' il rilevato, e la spina la ricalcola.
CAMERA_SPECS = ("camera_type", "pixel_size_um")
# I colori di una camera: le parole del CHECK di `instruments.camera_type`, e un test le tiene
# incollate allo schema e ai modelli. Qui si dice il SENSORE; cosa c'era davanti quando il file
# non lo scrive e' un altro campo sulla camera, `UNFILTERED` (`spine/unfiltered.py`).
CAMERA_MONO, CAMERA_COLOR = "mono", "color"
UNFILTERED = "unfiltered"
# Con la risposta "uno dei tuoi", quale: il NOME del filtro, in un campo suo, cosi' un filtro che
# l'utente chiama come una delle risposte non diventa quella risposta.
UNFILTERED_FILTER = "unfiltered_filter"

# La risposta "con che corredo sono state riprese queste pose" su un gruppo di pose che non dicono
# la CAMERA (`spine/rigless.py`): la chiave e' la notte con i valori dell'header che fanno il
# gruppo, e il campo porta i NOMI di ottica e camera con la focale. I tipi sono valori del `CHECK`
# di `entity_type`.
FRAME_GROUP, GROUP_RIG = "frame_group", "rig"
# Sullo stesso tipo, per le pose che non dicono l'OGGETTO e di cui il cielo non dice niente
# (`spine/unnamed.py`): il campo porta il bersaglio -- slug di catalogo o nome -- oppure "non e' un
# oggetto". Le due domande hanno chiavi fatte di valori diversi, e il campo le tiene distinte.
GROUP_OBJECT = "object"
# Le risposte sulla cartella che contiene i file: la chiave e' il suo percorso.
FOLDER = "folder"
# Sulla stessa cartella, per i frame che non dicono CHE FILE SONO (`spine/typeless.py`): il campo
# porta "light" o "calibration", cioe' una foto del cielo o un file di calibrazione.
FOLDER_TYPE = "image_type"
# Le due risposte, qui e non in `spine/typeless.py`, perche' le legge anche `spine/stages.py`
# per sapere chi e' pronto: tenerle nella sezione farebbe girare gli import in tondo.
TYPE_LIGHT, TYPE_CALIBRATION = "light", "calibration"

# La risposta su un mosaico (`spine/mosaic.py`): la chiave e' quella del mosaico, il campo uno
# solo. Il tipo e' un valore del `CHECK` di `entity_type`, e sta qui col resto del vocabolario.
MOSAIC, MOSAIC_FIELD = "mosaic", "answer"
# Le due risposte su un mosaico proposto. Un **no** e' una risposta come un si': senza, l'unico
# modo di far tacere una proposta sbagliata sarebbe accettarla. Il si' **non si scrive cosi'**: si
# scrive di cosa e' il mosaico (`object_answer.target_value`), perche' e' una domanda sola (Marco,
# 22/9/2026). `MOSAIC_NO` invece e' anche il valore scritto. Stanno qui e non in `mosaic.py`
# perche' le legge anche chi mostra le proposte, che la geometria non la deve importare.
MOSAIC_YES, MOSAIC_NO = "yes", "no"
MOSAIC_ANSWERS = (MOSAIC_YES, MOSAIC_NO)


# La risposta no a "sono lo stesso pezzo?" (`api/lookalike.py`), sulla camera chiesta: un campo per
# ogni altra camera -- una puo' dire no a piu' d'una -- col suo NOME nel campo e nel valore. Il
# nome la segue quando l'altra si rinomina o si unisce (`follow_not_same_as`).
NOT_SAME_AS = "not_same_as:"


def not_same_as(other_name):
    return NOT_SAME_AS + other_name


def follow_not_same_as(conn, old_name, new_name):
    """I no che nominano una camera la seguono quando cambia nome o finisce dentro un'altra: senza,
    la coppia tornerebbe a chiedere col nome nuovo. Chi aveva gia' un no verso il nome nuovo lo
    tiene, e quello vecchio va via."""
    conn.execute(
        "UPDATE OR IGNORE declarations SET field = ?, value = ?"
        " WHERE entity_type = 'instrument' AND field = ?",
        (not_same_as(new_name), new_name, not_same_as(old_name)),
    )
    conn.execute(
        "DELETE FROM declarations WHERE entity_type = 'instrument' AND field = ?",
        (not_same_as(old_name),),
    )


def declare_instrument_spec(conn, kind, name, field, value, now=None):  # noqa: PLR0913
    """Il pixel o il colore che l'utente ha scritto sulla scheda. Riscriverlo lo aggiorna."""
    write_declaration(conn, "instrument", instrument_key(kind, name), field, value, now)


def rig_key(optics_name, camera_name, focal_mm):
    return f"{optics_name or ''}|{camera_name or ''}|{'' if focal_mm is None else focal_mm}"


def rig_key_parts(key):
    """(ottica, camera, focale) di una chiave di `rig_key`, coi vuoti a `None`, o `None` se non si
    legge: un nome con la sbarra dentro fa piu' di tre pezzi, e non si indovina dove tagliare."""
    parti = key.split("|")
    if len(parti) != 3:
        return None
    ottica, camera, focale = parti
    return ottica or None, camera or None, float(focale) if focale else None


def values_of(conn, entity_type, field):
    """Tutte le risposte di quel genere su quel campo, come coppie (chiave, valore)."""
    return conn.execute(
        "SELECT entity_key, value FROM declarations WHERE entity_type = ? AND field = ?",
        (entity_type, field),
    ).fetchall()


def confirmed_keys(conn, entity_type):
    """Le chiavi gia' confermate: cio' che non e' qui dentro e' "nuovo"."""
    return {chiave for chiave, _ in values_of(conn, entity_type, CONFIRMED)}


def confirm(conn, entity_type, key, now=None):
    conn.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES(?, ?, ?, 1, ?) ON CONFLICT(entity_type, entity_key, field) DO NOTHING",
        (entity_type, key, CONFIRMED, now or now_iso()),
    )


# Il campo con cui l'utente dice da quale luogo sono state riprese le pose di un POSTO: la
# chiave e' le coordinate arrotondate (`place.coordinates_key`), il valore l'id del sito dichiarato.
# E' un fatto sul posto e non su una notte, quindi vale anche per le notti che verranno.
COORDINATES_SITE = "site"


def declare_coordinates(conn, coordinates_key, site_name, now=None):
    """ "Le pose riprese a queste coordinate sono di questo sito". Riscriverla la aggiorna.

    Si scrive il **nome** del sito e non il suo numero di riga: gli id si riusano (un sito senza
    notti si puo' cancellare, e il prossimo eredita il suo id), e una risposta scritta su un id
    finirebbe addosso a un altro luogo in silenzio. Il nome e' unico ed e' cio' che l'utente
    vede; se lo rinomina la risposta non aggancia piu' e l'app torna a chiedere, che e' la
    direzione sicura."""
    write_declaration(conn, "coordinates", coordinates_key, COORDINATES_SITE, site_name, now)


def site_for_coordinates(conn, coordinates_key):
    """Il **nome** del sito dichiarato per quelle coordinate, o `None` se nessuno ha risposto."""
    value = declared(conn, "coordinates", coordinates_key, COORDINATES_SITE)
    return value if isinstance(value, str) and value else None


def learn(conn, kind, header_value, target_key, now=None):
    """La regola: "quando l'header dice X, e' Y". Riscrivere la stessa grafia la aggiorna.

    La grafia si **normalizza** qui, una volta: lo schema dichiara `header_value` normalizzato, e
    chi cerca la regola normalizza a sua volta. Scriverla grezza voleva dire una regola che non
    aggancia mai -- due chiavi diverse per la stessa domanda."""
    if kind == "object":
        # La chiave di una regola sugli oggetti e' la grafia RIPULITA dalle parole di tavolozza,
        # perche' e' quella con cui `identify` la cerca: `M31 LRGB` e `M31` sono la stessa cosa.
        # Sta qui e non nei chiamanti cosi' che scrittura e lettura non possano divergere.
        header_value = clean_object_name(header_value)
    key = normalize_header_value(header_value)
    if kind not in (*ALIAS_KINDS, "filter", "object") or not key:
        return
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES(?, ?, ?, ?) ON CONFLICT(kind, header_value)"
        " DO UPDATE SET target_key = excluded.target_key",
        (kind, key, target_key, now or now_iso()),
    )


def rename(conn, kind, old_name, new_name, now=None):
    """ "Il pezzo che si chiamava X adesso si chiama Y": la grafia vecchia diventa una regola, **e
    le regole che portavano a X seguono**.

    La seconda meta' e' il motivo per cui questa non e' `learn`: una regola porta a un **nome**, e
    un nome cambia: una regola lasciata indietro punta a un nome che non e' piu' di nessuno
    (cosa succede poi sta in `docs/domini/spina.md`).

    Vale per la rinomina e per l'unione, che dal lato delle regole sono lo stesso gesto: la grafia
    assorbita e le sue vanno tutte sul pezzo tenuto."""
    learn(conn, kind, old_name, new_name, now)
    conn.execute(
        "UPDATE header_aliases SET target_key = ? WHERE kind = ? AND target_key = ?",
        (new_name, kind, old_name),
    )
