"""Le schede dell'attrezzatura: cosa l'utente dichiara di possedere, e cosa succede dopo.

Strumenti e filtri; il corredo ha la sua casa in `rigs`. Un pezzo dichiarato non e' piu' una
scoperta della spina (`detected = 0`), rinominarlo o unirlo **impara la regola sulla grafia
vecchia** -- senza, la scansione dopo lo ricreerebbe com'era -- e cio' che cambia il senso di
una posa la rimette in coda.
"""

from ..db import idlist
from ..vocab.filters import NO_FILTER, UNKNOWN, model_by_id, passband_from_bands
from . import counts, unfiltered
from . import rigs as corredi
from .declarations import (
    ALIAS_KINDS,
    CAMERA_SPECS,
    declare_instrument_spec,
    follow_not_same_as,
    instrument_key,
    rename,
)
from .stages import invalidate

# Le schede sono chiuse come le chiavi delle preferenze: un campo che non e' qui non entra.
INSTRUMENT_FIELDS = (
    "name", "brand", "model", "camera_type", "pixel_size_um", "aperture_mm", "focal_mm",
    "reducer_factor", "weight_kg", "payload_kg", "slots", "backfocus_mm", "notes",
)  # fmt: skip
FILTER_FIELDS = ("name", "brand", "model", "catalog_id")


def _set_fields(conn, table, row_id, fields, allowed):
    chosen = {k: v for k, v in fields.items() if k in allowed}
    if not chosen:
        return False
    columns = ", ".join(f'"{k}" = ?' for k in chosen)
    conn.execute(
        f"UPDATE {table} SET {columns} WHERE id = ?",  # noqa: S608 - colonne da una lista chiusa
        [*chosen.values(), row_id],
    )
    return True


def instrument_id(conn, kind, name):
    """L'id del pezzo con quel tipo e quel nome, o None: il nome e' unico per tipo."""
    row = conn.execute(
        "SELECT id FROM instruments WHERE kind = ? AND name = ?", (kind, name)
    ).fetchone()
    return None if row is None else row["id"]


def declare_instrument(conn, instrument_id, fields, now=None):
    """La scheda di un pezzo. Rinominarlo scrive anche la regola sulla grafia vecchia,
    altrimenti la prossima scansione ricreerebbe il pezzo col nome dell'header. Pixel e colore
    di una camera vanno fra le dichiarazioni: la colonna e' dei file, e la spina la ricalcola."""
    row = conn.execute(
        "SELECT kind, name FROM instruments WHERE id = ?", (instrument_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"strumento {instrument_id}")
    new_name = fields.get("name")
    renamed = bool(new_name) and new_name != row["name"]
    if renamed and row["kind"] in ALIAS_KINDS:
        rename(conn, row["kind"], row["name"], new_name, now)
    specs = {k: v for k, v in fields.items() if k in CAMERA_SPECS and row["kind"] == "camera"}
    columns = [f for f in INSTRUMENT_FIELDS if f not in specs]
    changed = _set_fields(conn, "instruments", instrument_id, fields, columns) or bool(specs)
    for field, value in specs.items():
        declare_instrument_spec(conn, row["kind"], row["name"], field, value, now)
    if renamed:  # anche il nome del corredo, la cui chiave porta quello del pezzo
        _move_instrument_declarations(conn, row["kind"], row["name"], new_name, merging=False)
        corredi.follow_piece(conn, row["kind"], row["name"], new_name, now)
    if changed:
        # da adesso il pezzo l'ha detto l'utente, non la spina
        conn.execute("UPDATE instruments SET detected = 0 WHERE id = ?", (instrument_id,))
    return changed


def _move_instrument_declarations(conn, kind, old_name, new_name, *, merging):
    """Le dichiarazioni di un pezzo hanno la chiave del suo nome: quando il nome cambia, o il
    pezzo finisce dentro un altro, pixel, colore e risposte vanno con lui, o resterebbero orfani
    ad aspettare il prossimo pezzo con quel nome.

    Nella rinomina vince cio' che si sposta: sotto il nome nuovo non c'e' un pezzo vivo (il nome
    e' unico), solo resti. Nell'unione vince la scheda del pezzo tenuto, e quella dell'assorbito
    passa dove il tenuto non ha scritto niente."""
    old, new = instrument_key(kind, old_name), instrument_key(kind, new_name)
    if not merging:
        conn.execute(
            "DELETE FROM declarations WHERE entity_type = 'instrument' AND entity_key = ?", (new,)
        )
    conn.execute(
        "UPDATE OR IGNORE declarations SET entity_key = ?"
        " WHERE entity_type = 'instrument' AND entity_key = ?",
        (new, old),
    )
    conn.execute(
        "DELETE FROM declarations WHERE entity_type = 'instrument' AND entity_key = ?", (old,)
    )
    if kind == "camera":
        follow_not_same_as(conn, old_name, new_name)


def camera_specs(conn):
    """`{id: {campo: valore}}`: pixel e colore di ogni camera come la scheda li mostra. Campo
    per campo, cio' che l'utente ha scritto vince su cio' che dicono i file."""
    written = {}
    for r in conn.execute(
        "SELECT entity_key, field, value FROM declarations"
        " WHERE entity_type = 'instrument' AND field IN (?, ?)",
        CAMERA_SPECS,
    ):
        written.setdefault(r["entity_key"], {})[r["field"]] = r["value"]
    return {
        r["id"]: {
            f: written.get(instrument_key(r["kind"], r["name"]), {}).get(f, r[f])
            for f in CAMERA_SPECS
        }
        for r in conn.execute(
            "SELECT id, kind, name, camera_type, pixel_size_um FROM instruments"
            " WHERE kind = 'camera'"
        )
    }


def declare_filter(conn, filter_id, fields, bands=None, is_none=None, now=None):  # noqa: PLR0913
    """La scheda di un filtro, con le bande che lascia passare: la banda canonica si ricava
    da quelle. Torna i frame da rimettere in coda (la banda cambia le risposte a valle)."""
    row = conn.execute(
        "SELECT name, passband, is_none FROM filters WHERE id = ?", (filter_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"filtro {filter_id}")
    if fields.get("catalog_id") and model_by_id(fields["catalog_id"]) is None:
        raise LookupError(f"modello {fields['catalog_id']}")  # prima di scrivere
    new_name = fields.get("name")
    if new_name and new_name != row["name"] and not row["is_none"]:
        # La riga "nessun filtro" non ha grafie da imparare: il suo nome viene dal vocabolario, e
        # una regola su "none" deciderebbe per ogni camera al posto della sua risposta.
        rename(conn, "filter", row["name"], new_name, now)
        unfiltered.follow_filter(conn, row["name"], new_name)  # la camera tiene il NOME
    _set_fields(conn, "filters", filter_id, fields, FILTER_FIELDS)
    if is_none is not None:
        # "nessun filtro" E' una banda del dominio chiuso: l'interruttore da solo lascerebbe
        # la riga con la banda vecchia, due case per lo stesso fatto
        conn.execute(
            "UPDATE filters SET is_none = ?, passband = CASE WHEN ? THEN ? ELSE passband END"
            " WHERE id = ?",
            (int(is_none), int(is_none), NO_FILTER, filter_id),
        )
    if bands is not None:
        conn.execute("DELETE FROM filter_bands WHERE filter_id = ?", (filter_id,))
        for b in bands:
            conn.execute(
                "INSERT INTO filter_bands(filter_id, band, width_nm) VALUES(?, ?, ?)",
                (filter_id, b["band"], b.get("width_nm")),
            )
        conn.execute(
            "UPDATE filters SET passband = ? WHERE id = ?",
            (passband_from_bands([b["band"] for b in bands]), filter_id),
        )
    modello = model_by_id(fields.get("catalog_id")) if bands is None else None
    if modello:
        # il modello porta la sua banda: sceglierlo e' una risposta intera, non una marca
        conn.execute(
            "UPDATE filters SET passband = ? WHERE id = ?", (modello["passband"], filter_id)
        )
    after = conn.execute("SELECT passband FROM filters WHERE id = ?", (filter_id,)).fetchone()
    if after["passband"] == row["passband"]:
        # marca, modello o una nota non cambiano cosa vuol dire una posa: non si rilavora
        return []
    frames = [r[0] for r in conn.execute("SELECT id FROM frames WHERE filter_id = ?", (filter_id,))]
    invalidate(conn, frames, "normalize", now=now)
    return frames


def _rigs_using(conn, instrument_id):
    """I corredi in cui quel pezzo e' ottica o camera: quelli la cui chiave porta il suo nome."""
    return [
        r[0]
        for r in conn.execute(
            "SELECT id FROM rigs WHERE optics_id = ? OR camera_id = ?",
            (instrument_id, instrument_id),
        )
    ]


class MergeRefusedError(ValueError):
    """Un'unione che la spina non fa. Chi espone la rotta la traduce in 422: e' un rifiuto con la
    sua ragione, e solo questo -- un altro `ValueError` e' un guasto, e resta tale."""


def mergeable(src, dst):
    """Se `src` si unisce in `dst`: due pezzi DIVERSI dello stesso tipo, e un tipo con grafie da
    unire -- senza regola la scansione dopo ricreerebbe la grafia vecchia. Una casa sola per le
    due porte: la pagina offre solo queste unioni, e `merge_instrument` rifiuta le altre."""
    return src["id"] != dst["id"] and src["kind"] == dst["kind"] and src["kind"] in ALIAS_KINDS


def merge_instrument(conn, from_id, into_id, now=None):
    """Due grafie, un pezzo: si impara la regola, si toglie la riga assorbita e i corredi che
    la usavano, e le pose tornano in coda. `normalize` le riaggancia al pezzo giusto."""
    src = conn.execute("SELECT id, kind, name FROM instruments WHERE id = ?", (from_id,)).fetchone()
    dst = conn.execute("SELECT id, kind, name FROM instruments WHERE id = ?", (into_id,)).fetchone()
    if src is None or dst is None:
        raise LookupError(f"pezzo {from_id if src is None else into_id}")
    if not mergeable(src, dst):
        raise MergeRefusedError(f"{from_id} non si unisce in {into_id}: non e' `mergeable`")
    rename(conn, src["kind"], src["name"], dst["name"], now)
    corredi.follow_piece(conn, src["kind"], src["name"], dst["name"], now)
    _move_instrument_declarations(conn, src["kind"], src["name"], dst["name"], merging=True)
    rigs = _rigs_using(conn, from_id)
    frames = set(_detach_rigs(conn, rigs)) | _detach_from_frames(conn, from_id)
    conn.execute("DELETE FROM instruments WHERE id = ?", (from_id,))
    corredi.restore_declared(conn, now)
    invalidate(conn, frames, "normalize", now=now)
    return sorted(frames)


def _detach_from_frames(conn, instrument_id):
    """Stacca dalle pose il pezzo che sta per sparire, per i generi che la posa nomina **addosso a
    se'**. Senza, la riga non si cancella affatto -- il database la tiene per la chiave esterna --
    e l'Applica intera va a rotoli portandosi via anche le risposte buone."""
    staccate = set()
    for kind in counts.CARRIED:
        pose = [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE {kind}_id = ?",  # noqa: S608 - generi nostri
                (instrument_id,),
            )
        ]
        if pose:
            conn.execute(
                f"UPDATE frames SET {kind}_id = NULL WHERE {kind}_id = ?",  # noqa: S608
                (instrument_id,),
            )
            staccate.update(pose)
    return staccate


def band_unknown(row):
    """Se di quel filtro non si sa la banda: e' la domanda "che filtro e'?" di *Da confermare*."""
    return row["passband"] == UNKNOWN


def filter_target(row):
    """Se un filtro puo' ricevere un'unione, o essere scelto come "uno dei tuoi": uno con la banda
    nota, tranne la riga "nessun filtro". Una casa sola per le tendine e per chi unisce."""
    return not row["is_none"] and not band_unknown(row)


def filter_mergeable(src, dst):
    """Se il filtro `src` si unisce in `dst`: due filtri diversi, l'origine non e' "nessun filtro"
    -- la sua grafia diventerebbe una regola su "none", che risponderebbe per ogni camera -- e la
    destinazione e' uno dei tuoi. La pagina offre queste, `merge_filter` rifiuta le altre."""
    return src["id"] != dst["id"] and not src["is_none"] and filter_target(dst)


def merge_filter(conn, from_id, into_id, now=None):
    """Come per gli strumenti: la grafia assorbita diventa una regola verso il filtro tenuto."""
    riga = "SELECT id, name, is_none, passband FROM filters WHERE id = ?"
    src = conn.execute(riga, (from_id,)).fetchone()
    dst = conn.execute(riga, (into_id,)).fetchone()
    if src is None or dst is None:
        raise LookupError(f"filtro {from_id if src is None else into_id}")
    if not filter_mergeable(src, dst):
        raise MergeRefusedError("si unisce un filtro vero in un altro, con la banda nota")
    rename(conn, "filter", src["name"], dst["name"], now)
    unfiltered.follow_filter(conn, src["name"], dst["name"])  # "sono lo stesso filtro", anche li'
    frames = [r[0] for r in conn.execute("SELECT id FROM frames WHERE filter_id = ?", (from_id,))]
    conn.execute("UPDATE frames SET filter_id = NULL WHERE filter_id = ?", (from_id,))
    conn.execute("DELETE FROM filters WHERE id = ?", (from_id,))
    invalidate(conn, frames, "normalize", now=now)
    return frames


def _detach_rigs(conn, rig_ids):
    """Stacca le pose dai corredi che stanno per sparire e li cancella. I corredi sono
    rilevati: `normalize` li rifa' identici, o migliori, al giro dopo."""
    if not rig_ids:
        return []
    with idlist.holding(conn, rig_ids) as listed:
        frames = [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE rig_id IN {listed}"  # noqa: S608 - costante nostra
            )
        ]
        conn.execute(f"UPDATE frames SET rig_id = NULL WHERE rig_id IN {listed}")  # noqa: S608
        conn.execute(f"DELETE FROM rigs WHERE id IN {listed}")  # noqa: S608 - costante nostra
    return frames
