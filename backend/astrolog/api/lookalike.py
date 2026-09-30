"""La domanda "sono lo stesso pezzo?" di Da confermare: due grafie della stessa camera, e l'app lo
fa notare. Si' e' l'unione (`instrument_answer.merge`), no una dichiarazione che la spegne.

Vincolo non ovvio: un'unione non si disfa, quindi si propone solo con una **prova positiva** (lo
stesso sensore), mai per la sola somiglianza del nome. E l'app non puo' saperlo da sola (Marco,
25/9/2026): due camere dello stesso modello sono due pezzi, e i file non lo dicono.
"""

import json
import re

from ..spine import counts, gear
from ..spine import declarations as decl
from ..vocab.header_value import normalize_header_value
from . import instrument_answer as strumento
from .models_review import LookalikeOut

# Quante pose vere hanno le camere di un elenco JSON: lo stesso legame dell'Attrezzatura
# (`counts.of`), e una copia riscritta non e' un'altra posa. Nella forma coi corredi gia' nel
# `FROM`: quella con la sotto-select cerca i corredi per ogni coppia (posa, camera), e la prova sta
# in `test_the_cameras_do_not_search_the_rigs_row_by_row`.
_CAMERAS = f"""
SELECT i.id, COUNT(f.id) AS frames
FROM instruments i
LEFT JOIN (frames f LEFT JOIN rigs g ON g.id = f.rig_id)
       ON f.copy_of IS NULL AND {counts.of("instrument", rigs_joined=True)}
WHERE i.id IN (SELECT value FROM json_each(?))
GROUP BY i.id
"""  # noqa: S608 - frammento della spina, non valori dell'utente


def _frames_of(conn, ids):
    """`{id: pose vere}` per quelle camere."""
    return {r["id"]: r["frames"] for r in conn.execute(_CAMERAS, (json.dumps(sorted(ids)),))}


def lookalikes(conn):
    """Per ogni camera che ha tutta l'aria di essere un'altra scritta in un altro modo, la domanda
    verso il pezzo in cui si unirebbe (Marco, 15/9/2026: `ATR2600M` e `ATR2600M(USB2.0)` sono la
    stessa camera vista da due driver).

    Un'unione non si disfa, quindi serve una **prova positiva**, non l'assenza di differenze: la
    regola larga proponeva `Canon EF (50mm)` con `(200mm)` e `Atik 460EX (Mono)` con `(Color)`.
    Somigliano due camere con:
    - **lo stesso nome**, tolti maiuscole, spazi, segni e cio' che sta **fra parentesi** -- li' il
      driver scrive un'annotazione. "Comincia come l'altro" non basta: `QHY268M` e `QHY268MC` sono
      due sensori;
    - **lo stesso pixel, noto per tutte e due** dai file o dall'utente: e' la prova che il sensore
      e' uno. Quello ricavato dal cielo no: porta l'errore della focale;
    - **lo stesso colore**, dove il colore che manca vale mono: una mono letta dai file non lo
      porta mai, e se fosse un valore a se' dire "mono" su una sola grafia separerebbe le due.
    Si chiede in **una direzione**, verso chi ha piu' pose (a pari pose il primo arrivato). Un no
    vale per quella coppia in tutte e due le direzioni, perche' chi ha piu' pose puo' cambiare."""
    specs = gear.camera_specs(conn)
    distinct = _answered_no(conn)
    groups = {}
    for r in conn.execute("SELECT id, name FROM instruments WHERE kind = 'camera'"):
        p = {**dict(r), **specs.get(r["id"], {})}
        name = _bare_name(p["name"])
        if name and p["pixel_size_um"] is not None:
            same = (name, p["pixel_size_um"], p["camera_type"] or decl.CAMERA_MONO)
            groups.setdefault(same, []).append(p)
    # si contano le pose solo dei gruppi con una coppia ancora da chiedere: una camera sola, o un
    # gruppo in cui ogni coppia ha gia' avuto un no, non e' una domanda qualunque sia la piu' usata
    groups = [g for g in groups.values() if _still_asks(g, distinct)]
    frames = _frames_of(conn, [p["id"] for g in groups for p in g]) if groups else {}
    for p in (p for g in groups for p in g):
        p["frames"] = frames[p["id"]]
    out = []
    for group in groups:
        kept = max(group, key=lambda p: (p["frames"], -p["id"]))
        out += [
            LookalikeOut(
                id=p["id"],
                name=p["name"],
                frames=p["frames"],
                into_id=kept["id"],
                into_name=kept["name"],
                into_frames=kept["frames"],
            )
            for p in group
            if p is not kept and frozenset((p["name"], kept["name"])) not in distinct
        ]
    out.sort(key=lambda q: (-(q.frames + q.into_frames), q.name))
    return out


def answer_all(conn, edits, now):
    """Le risposte di un Applica, e le pose da rimettere in coda. Si' unisce le due grafie; no si
    scrive sulla camera chiesta, col **nome** dell'altra e non col suo numero di riga, che
    un'unione cancella. Una coppia che non e' piu' chiesta e' una pagina vecchia, e si dice prima
    di scrivere.

    Le coppie si calcolano una volta, e di nuovo **solo dopo un'unione**: un'unione sposta pose e
    puo' cambiare quale grafia resta nella coppia dopo, un no non sposta niente."""
    requeued, domande = set(), None
    for edit in edits:
        if domande is None:
            domande = {(q.id, q.into_id): q for q in lookalikes(conn)}
        coppia = domande.pop((edit.id, edit.into_id), None)
        if coppia is None:
            raise LookupError(f"coppia {edit.id} {edit.into_id}")
        if edit.same:
            requeued |= strumento.merge(conn, edit.id, edit.into_id, now)
            domande = None
            continue
        decl.write_declaration(
            conn,
            "instrument",
            decl.instrument_key("camera", coppia.name),
            decl.not_same_as(coppia.into_name),
            coppia.into_name,
            now,
        )
    return requeued


def _still_asks(group, distinct):
    """Se nel gruppo c'e' almeno una coppia di camere a cui non si e' risposto no."""
    nomi = [p["name"] for p in group]
    return any(frozenset((a, b)) not in distinct for i, a in enumerate(nomi) for b in nomi[i + 1 :])


def _answered_no(conn):
    """Le coppie a cui si e' risposto no, come insiemi di due nomi: la direzione non conta."""
    return {
        frozenset((r["entity_key"].split("|", 1)[1], r["value"]))
        for r in conn.execute(
            "SELECT entity_key, value FROM declarations WHERE entity_type = 'instrument'"
            " AND substr(field, 1, ?) = ?",
            (len(decl.NOT_SAME_AS), decl.NOT_SAME_AS),
        )
    }


def _bare_name(name):
    """Il nome senza annotazioni fra parentesi, ridotto a lettere e cifre."""
    return re.sub(r"\([^)]*\)|[^a-z0-9]", "", normalize_header_value(name))
