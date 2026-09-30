"""Il **corredo** visto da chi dichiara: la sua impronta, la chiave con cui lo si nomina, e cio'
che l'utente gli scrive addosso.

Un corredo lo fa la spina dalle pose (ottica, camera, focale), o lo scrivi tu, e un'unione puo'
cancellarne la riga. Per questo il nome che gli dai non sta li' dentro ma fra le dichiarazioni, con
una chiave che gli sopravvive: quando `normalize` rifa' lo stesso corredo, o `restore_declared`
rifa' quello che hai scritto tu, il nome torna da solo.

Vincoli non ovvi:

* La chiave porta i **nomi** di ottica e camera, quindi una rinomina di uno dei due la sposta.
  Vale per quei due generi soltanto: gli altri nella chiave non ci sono, e seguirli riscriverebbe
  la chiave di un corredo che con loro non c'entra.
* **La montatura del corredo e' il suo nome**, non il numero della riga: una rinomina o
  un'unione la portano con se', e sulle pose la scrive `normalize`, che le rilavora.
* Il corredo si trova per impronta con le focali entro il +-5 % considerate la stessa: l'indice
  unico e' su uguaglianza esatta, quindi il raggruppamento vive qui, in Python, prima di scrivere.
"""

from ..clock import now_iso
from ..units import same_focal
from . import gear_usage, rigless
from .declarations import forget, rig_key, rig_key_parts, values_of, write_declaration
from .stages import invalidate

MOUNT = "mount"
DECLARED = "declared"


class NotAMountError(ValueError):
    """Si e' chiesto di montare su un corredo un pezzo che non e' una montatura."""


class WrongKindError(ValueError):
    """Un corredo si fa con un'ottica e una camera che possiedi: un altro pezzo non va."""


class RigExistsError(ValueError):
    """Quel corredo ce l'hai gia': stessa ottica, stessa camera, focale entro il 5 %."""


def rig_for(conn, optics_id, camera_id, focal_mm, now, *, detected=True):  # noqa: PLR0913
    """(id, creato?) del corredo con quell'impronta: una focale entro il +-5 % di una gia'
    vista e' la stessa focale, e il corredo e' quello.

    Il valore di `rigs.focal_mm` si fissa alla CREAZIONE e non si muove piu': una scansione
    successiva che porta focali vicine le aggancia a questo corredo senza ricalcolare il
    rappresentante. Spostarlo vorrebbe dire riscrivere un dato che l'utente ha gia' visto."""
    trovato = find_rig(conn, optics_id, camera_id, focal_mm)
    if trovato is not None:
        return trovato, False
    rig_id = conn.execute(
        "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES(?, ?, ?, ?, ?)",
        (optics_id, camera_id, focal_mm, int(detected), now),
    ).lastrowid
    return rig_id, True


def find_rig(conn, optics_id, camera_id, focal_mm):
    """Il corredo con quell'impronta, o `None`: la stessa regola della focale di `rig_for`."""
    for row in conn.execute(
        "SELECT id, focal_mm FROM rigs WHERE optics_id IS ? AND camera_id IS ?",
        (optics_id, camera_id),
    ).fetchall():
        if same_focal(row["focal_mm"], focal_mm):
            return row["id"]
    return None


# Cio' che un corredo porta alla chiave nuova delle sue pose; la risposta sull'ottica resta dov'e'.
CARRIED_FIELDS = ("name", MOUNT)


def carry_declarations(conn, old_key, rig_id, now):
    """Copia il nome e la montatura scritti sulla chiave `old_key` sul corredo `rig_id`, appena
    nato. Si **copiano**: a un cambio di idea il corredo nuovo li ritrova li'."""
    for campo in CARRIED_FIELDS:
        conn.execute(
            "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
            " SELECT entity_type, ?, field, value, ? FROM declarations"
            " WHERE entity_type = 'rig' AND entity_key = ? AND field = ?"
            " ON CONFLICT(entity_type, entity_key, field) DO NOTHING",
            (decl_key(_rig(conn, rig_id)), now, old_key, campo),
        )


def drop_empty(conn):
    """Cancella i corredi **rilevati** rimasti senza pose -- il residuo di una risposta che le ha
    spostate --, che in Attrezzatura sembrerebbero veri con zero ore. Uno scritto a mano resta."""
    conn.execute(
        "DELETE FROM rigs WHERE detected = 1"
        " AND NOT EXISTS (SELECT 1 FROM frames f WHERE f.rig_id = rigs.id)"
    )


def create_declared(conn, optics_id, camera_id, focal_mm, now=None):
    """Un corredo scritto a mano, anche prima di averci ripreso: e' la sua impronta, quindi e' lo
    stesso che la scansione trovera'. Scritto anche fra le dichiarazioni, perche' un'unione della
    sua ottica o della sua camera cancella i corredi e `normalize` li rifa' solo dalle pose."""
    nomi = {}
    for kind, piece_id in (("optics", optics_id), ("camera", camera_id)):
        row = conn.execute(
            "SELECT name FROM instruments WHERE id = ? AND kind = ?", (piece_id, kind)
        ).fetchone()
        if row is None:
            raise WrongKindError(f"{piece_id} non e' un pezzo di genere {kind}")
        nomi[kind] = row["name"]
    if find_rig(conn, optics_id, camera_id, focal_mm) is not None:
        raise RigExistsError(f"{nomi['optics']} + {nomi['camera']} a {focal_mm} mm")
    rig_id, _ = rig_for(conn, optics_id, camera_id, focal_mm, now or now_iso(), detected=False)
    write_declaration(
        conn, "rig", rig_key(nomi["optics"], nomi["camera"], focal_mm), DECLARED, 1, now
    )
    return rig_id


def _pezzo_id(conn, kind, name):
    row = conn.execute(
        "SELECT id FROM instruments WHERE kind = ? AND name = ?", (kind, name)
    ).fetchone()
    return None if row is None else row["id"]


def restore_declared(conn, now=None):
    """Rifa' i corredi scritti da te che un'unione ha cancellato: la chiave li ha gia' seguiti
    sul pezzo tenuto (`follow_rename`), qui tornano la riga e la sua riga d'uso. I nomi si
    confrontano interi."""
    for chiave, _ in values_of(conn, "rig", DECLARED):
        parti = rig_key_parts(chiave)
        if parti is None:
            continue  # un nome con la sbarra dentro: come in `follow_rename`, non si tocca
        ottica, camera, focale = parti
        optics_id, camera_id = _pezzo_id(conn, "optics", ottica), _pezzo_id(conn, "camera", camera)
        if optics_id is None or camera_id is None:
            continue
        if find_rig(conn, optics_id, camera_id, focale) is None:
            quando = now or now_iso()
            rifatto, _ = rig_for(conn, optics_id, camera_id, focale, quando, detected=False)
            gear_usage.add_new(conn, "rig", rifatto)


RIG_ROWS = """
SELECT g.id, g.focal_mm, o.name AS optics, c.name AS camera
FROM rigs g LEFT JOIN instruments o ON o.id = g.optics_id
            LEFT JOIN instruments c ON c.id = g.camera_id
"""


def rigs_with_keys(conn):
    """Le righe dei corredi con la loro chiave: la chiave che si LEGGE e quella che si SCRIVE
    vengono tutte di qui, o il nome dato a un corredo finirebbe su un altro."""
    return [(decl_key(r), r) for r in conn.execute(RIG_ROWS).fetchall()]


def decl_key(row):
    return rig_key(row["optics"], row["camera"], row["focal_mm"])


def _rig(conn, rig_id):
    """La riga del corredo, o `LookupError`: la leggono tutti quelli che gli scrivono addosso."""
    row = conn.execute(RIG_ROWS + " WHERE g.id = ?", (rig_id,)).fetchone()
    if row is None:
        raise LookupError(f"corredo {rig_id}")
    return row


def declare_mount(conn, rig_id, mount_id, now=None):
    """La montatura con cui usi un corredo, o `None` per togliere la tua parola e tornare a
    quella dei file. Rimette le sue pose a `normalize`, che la scrive su ognuna: torna quali --
    nessuna, se non e' cambiato niente."""
    chiave = decl_key(_rig(conn, rig_id))
    if mount_id is None:
        tolta = forget(conn, "rig", chiave, MOUNT)
        if not tolta:
            return []
    else:
        nome = conn.execute(
            "SELECT name FROM instruments WHERE id = ? AND kind = ?", (mount_id, MOUNT)
        ).fetchone()
        if nome is None:
            raise NotAMountError(f"{mount_id} non e' una montatura")
        if declared_mount(conn, rig_id) == mount_id:
            return []
        write_declaration(conn, "rig", chiave, MOUNT, nome["name"], now)
    pose = [r[0] for r in conn.execute("SELECT id FROM frames WHERE rig_id = ?", (rig_id,))]
    invalidate(conn, pose, "normalize", now=now)
    return pose


_MONTATURE = """
SELECT d.entity_key, i.id FROM declarations d
JOIN instruments i ON i.kind = 'mount' AND i.name = d.value
WHERE d.entity_type = 'rig' AND d.field = 'mount'
"""


def rig_mounts(conn):
    """Le montature che l'utente ha dato ai corredi, per chiave: `{chiave: id}`."""
    return {r["entity_key"]: r["id"] for r in conn.execute(_MONTATURE)}


def declared_mount(conn, rig_id):
    """La montatura che l'utente ha dato a quel corredo, o `None`. La chiede `normalize` per ogni
    posa: una ricerca per chiave, non tutte le dichiarazioni."""
    row = conn.execute(RIG_ROWS + " WHERE g.id = ?", (rig_id,)).fetchone()
    if row is None:
        return None
    trovata = conn.execute(_MONTATURE + " AND d.entity_key = ?", (decl_key(row),)).fetchone()
    return None if trovata is None else trovata["id"]


def rig_names(conn):
    """I nomi che l'utente ha dato ai corredi, per chiave: `{chiave: nome}`."""
    return dict(values_of(conn, "rig", "name"))


def declare_rig(conn, rig_id, name, now=None):
    """Il nome di un corredo. Non sta nella riga di `rigs`, che e' rilevata e che un'unione
    puo' cancellare: sta fra le dichiarazioni, con la chiave che sopravvive. Cosi' il nome
    torna da solo quando `normalize` ricostruisce lo stesso corredo."""
    row = _rig(conn, rig_id)
    if not name:
        return False
    write_declaration(conn, "rig", decl_key(row), "name", name, now)
    return True


# I generi nella **chiave di un corredo** (`ottica|camera|focale`): solo per loro una rinomina
# sposta le chiavi. `follow_rename` guarda i nomi e non il genere, e i `GUIDECAM` veri portano
# nomi della famiglia delle camere: chiamata per una camera di guida, riscriverebbe chiavi altrui.
KEY_KINDS = ("optics", "camera")


# I pezzi che una dichiarazione sul corredo porta **nel valore**, col genere come campo: la
# montatura che gli dai, e l'ottica che dici alla camera a una focale (`spine/rig_optics.py`).
VALUE_KINDS = (MOUNT, "optics")


def follow_piece(conn, kind, old_name, new_name, now=None):
    """Un pezzo che cambia nome, visto dai corredi: la loro chiave, se e' ottica o camera; il
    valore che lo nomina, se e' una montatura o un'ottica. Gli altri generi non li toccano."""
    if kind in KEY_KINDS:
        follow_rename(conn, old_name, new_name, now)
        rigless.follow_piece(conn, kind, old_name, new_name, now)  # e le risposte sui gruppi
    if kind in VALUE_KINDS:
        conn.execute(
            "UPDATE declarations SET value = ?"
            " WHERE entity_type = 'rig' AND field = ? AND value = ?",
            (new_name, kind, old_name),
        )


def follow_rename(conn, old_name, new_name, now=None):
    """Le dichiarazioni sui corredi hanno la chiave (ottica, camera, focale): se un pezzo
    cambia nome, la chiave cambia con lui, o il nome che l'utente ha dato al corredo resta
    orfano e il corredo rifatto torna senza nome."""
    for r in conn.execute(
        "SELECT entity_type, entity_key, field, value FROM declarations WHERE entity_type = 'rig'"
    ).fetchall():
        parti = rig_key_parts(r["entity_key"])
        if parti is None or old_name not in parti[:2]:
            continue
        ottica, camera = (new_name if p == old_name else p for p in parti[:2])
        nuova = rig_key(ottica, camera, parti[2])
        forget(conn, r["entity_type"], r["entity_key"], r["field"])
        conn.execute(
            "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
            " VALUES(?, ?, ?, ?, ?) ON CONFLICT(entity_type, entity_key, field)"
            " DO NOTHING",  # se il corredo di destinazione ha gia' una risposta, vince la sua
            (r["entity_type"], nuova, r["field"], r["value"], now or now_iso()),
        )
