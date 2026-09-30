"""La domanda **quale ottica era**: le pose i cui file non nominano l'ottica.

Con l'ASIAIR `TELESCOP` e' la montatura (`vocab.software.telescope_is_mount`), e altri file
`TELESCOP` non lo scrivono affatto: quelle pose hanno un corredo senza ottica. Si chiede una volta
per camera e focale, e la risposta vale per ogni posa che l'ottica non la nomina, anche per quelle
che arriveranno: `normalize` la legge per ogni posa senza ottica, come la montatura del corredo
(`normalize_rig.rig_for_frame`).

Vincoli non ovvi:

* **La risposta sta sulla chiave del corredo senza ottica** (`|camera|focale`), campo `optics`,
  col NOME dell'ottica: una rinomina della camera sposta la chiave, una dell'ottica il valore
  (`rigs.follow_piece`), e un'unione di pezzi passa di li'.
* **La focale si confronta con la regola dei corredi** (`units.same_focal`): la risposta data a
  800 mm vale per la posa a 803.
* **La domanda si riconosce dalle pose, non dal corredo**: risposta, le pose stanno nel corredo
  che ha l'ottica, e la domanda resta in pagina con la sua risposta, per cambiare idea.
"""

import json

from ..units import same_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import telescope_is_mount
from . import counts
from . import frame_folder as folder
from . import objects as obj
from .declarations import rig_key, rig_key_parts, values_of, write_declaration
from .stages import invalidate

OPTICS = "optics"

# Le pose vive per corredo e oggetto, fra quelle il cui file non nomina l'ottica
# (`frames.names_optics`, scritto dalla scansione con `names_the_optics`).
_BY_RIG = f"""
SELECT f.rig_id, {obj.SUBJECT} AS subject,
       c.name AS camera, g.focal_mm, o.name AS optics, {counts.AGGREGATE}, {counts.UNTIMED}
FROM frames f {folder.JOIN}
JOIN rigs g ON g.id = f.rig_id JOIN instruments c ON c.id = g.camera_id
LEFT JOIN instruments o ON o.id = g.optics_id
{obj.SUBJECT_JOIN}
WHERE f.copy_of IS NULL AND f.names_optics = 0
GROUP BY f.rig_id, subject
"""  # noqa: S608 - frammenti costanti

# Le pose dei corredi di una domanda, copie comprese: un corredo ce l'hanno anche loro.
_POSES_OF_RIGS = """
SELECT id, telescope_raw, software FROM frames
WHERE rig_id IN (SELECT value FROM json_each(?))
"""


def names_the_optics(software, telescope_raw):
    """Se il file nomina l'ottica: `TELESCOP` scritto, e da un software che li' non mette la
    montatura. E' la stessa lettura di `normalize_rig.rig_for_frame`."""
    return not telescope_is_mount(software) and bool(normalize_header_value(telescope_raw))


def _answer_for(answers, camera, focal_mm):
    """(chiave, ottica, focale) della risposta per quella camera a quella focale, o `None`."""
    for chiave, ottica in answers:
        letta = rig_key_parts(chiave)
        if letta is not None and letta[1] == camera and same_focal(letta[2], focal_mm):
            return chiave, ottica, letta[2]
    return None


def declared(conn, camera, focal_mm):
    """(chiave, ottica) della risposta per quella camera a quella focale, o `None`. La chiave e'
    quella del corredo senza ottica: chi la usa ci ritrova il nome e la montatura dati a lui."""
    trovata = _answer_for(values_of(conn, "rig", OPTICS), camera, focal_mm)
    return None if trovata is None else trovata[:2]


def by_rig(conn, only=None):
    """Le domande, la piu' ripresa in cima: la camera, la focale, le pose, le ore, cosa ci hai
    ripreso e la risposta gia' data. Un corredo che ha l'ottica da un'altra risposta -- quella sulla
    camera -- non si chiede. `only` tiene una domanda sola: e' la riga di chi risponde."""
    risposte = values_of(conn, "rig", OPTICS)
    domande = {}
    for r in conn.execute(_BY_RIG):
        trovata = _answer_for(risposte, r["camera"], r["focal_mm"])
        if trovata is None and r["optics"] is not None:
            continue
        chiave = trovata[0] if trovata else rig_key(None, r["camera"], r["focal_mm"])
        if only is not None and chiave != only:
            continue
        chiave, ottica, focale = trovata or (chiave, None, r["focal_mm"])
        domanda = domande.setdefault(chiave, {
            "key": chiave, "camera": r["camera"], "focal_mm": focale,
            "frames": 0, "integration_s": 0.0, "untimed": 0, "answer": ottica, "rigs": set(),
        })  # fmt: skip
        for campo in ("frames", "integration_s", "untimed"):
            domanda[campo] += r[campo] or 0
        obj.count_subject(domanda, r["subject"], r["frames"])
        domanda["rigs"].add(r["rig_id"])
    out = obj.subjects(conn, list(domande.values()))
    return sorted(out, key=lambda d: (-d["frames"], d["key"]))


def row_of(conn, key):
    """La domanda con quella chiave, o `None` se non c'e' piu'."""
    return next(iter(by_rig(conn, only=key)), None)


def declare(conn, key, optics, now=None):
    """La risposta, riscrivibile: si cambia idea rispondendo di nuovo. Si scrive il NOME: il pezzo
    nasce da li' al giro dopo, come da un header (`normalize_rig.instrument_named`)."""
    write_declaration(conn, "rig", key, OPTICS, optics, now)


def requeue(conn, row):
    """Rimette in coda le pose di quella domanda e le torna: quelle dei suoi corredi che l'ottica
    non la nominano. Le altre di quei corredi -- chi l'ottica la scrive -- restano dove sono."""
    pose = conn.execute(_POSES_OF_RIGS, (json.dumps(sorted(row["rigs"])),)).fetchall()
    frames = [p["id"] for p in pose if not names_the_optics(p["software"], p["telescope_raw"])]
    invalidate(conn, frames, "normalize")
    return frames
