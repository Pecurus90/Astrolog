"""Quanto e' servito ogni pezzo, corredo e filtro: i conti dell'Attrezzatura, fatti da chi scrive.

Una lettura non calcola mai (Marco, 22/9/2026): i conti si fanno a fine giro di ogni stadio che
cambia le pose -- corredo, filtro, cielo, oggetto, notte -- e si scrivono in `gear_usage`; la
pagina li legge (`spine/inventory.py`). Ore e frame vengono da `counts`, gli stessi dell'Archivio e
delle Notti.

Vincoli non ovvi:

* **Le ore che l'app non puo' sapere si scrivono `NULL`, non zero**: ogni genere che **in questo
  archivio** nessuna posa porta -- la montatura, finche' nessun file la nomina e nessun corredo
  ne ha una.
* **Quanto inquadra un corredo si MISURA**: la mediana di cio' che il riconoscitore ha visto
  (`frame_wcs`), non il conto teorico su focale e pixel.
"""

import json

from ..db import idlist
from ..db.replace_table import replace_rows
from ..units import hundredths, median
from . import counts
from . import objects as obj

# Ottica e camera le ore ce l'hanno sempre: passano dal corredo, che la spina deriva da ogni
# posa. Per gli altri dipende dall'archivio, e lo dice `_con_le_ore`.
_SEMPRE = ("optics", "camera")

# Tutti i pezzi, corredi e filtri insieme, **raggruppando** le pose una volta per elenco: i
# sotto-select correlati, riga per riga, erano la parte cara su un archivio grande. Il legame e'
# quello di `counts` (le coppie di `PIECE_FRAMES` per i pezzi), e le notti con lo stesso legame
# delle ore: due definizioni della stessa riga direbbero due numeri diversi.
_CONTI = f"{counts.AGGREGATE}, {counts.UNTIMED}, COUNT(DISTINCT f.night_id) AS nights"
_USATI = """COALESCE(u.frames, 0) AS frames, COALESCE(u.integration_s, 0) AS integration_s,
       COALESCE(u.untimed, 0) AS untimed, COALESCE(u.nights, 0) AS nights"""

_STRUMENTI = f"""
SELECT i.id, i.kind, {_USATI}
FROM instruments i LEFT JOIN (
  SELECT l.piece AS id, {_CONTI}
  FROM ({counts.PIECE_FRAMES}) l JOIN frames f ON f.id = l.frame
  WHERE f.copy_of IS NULL GROUP BY l.piece
) u ON u.id = i.id
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente

_CORREDI = f"""
SELECT g.id, {_USATI}
FROM rigs g LEFT JOIN (
  SELECT f.rig_id AS id, {_CONTI} FROM frames f
  WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL GROUP BY f.rig_id
) u ON u.id = g.id
{counts.ORDER_BY_TIME}, g.id
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente

_FILTRI = f"""
SELECT x.id, {_USATI}
FROM filters x LEFT JOIN (
  SELECT f.filter_id AS id, {_CONTI} FROM frames f
  WHERE f.copy_of IS NULL AND f.filter_id IS NOT NULL GROUP BY f.filter_id
) u ON u.id = x.id
WHERE x.is_none = 0
{counts.ORDER_BY_TIME}, x.name
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente

# Cosa hai ripreso con ogni pezzo, dal piu' ripreso. Tre query con lo stesso corpo e una chiave
# diversa: il corredo e il filtro li dice la posa; un pezzo ci arriva per le due strade di
# `counts` -- dai corredi che lo portano, o dalla colonna che la posa gli dedica.
_OGGETTI = f"""
SELECT {{chiave}} AS chiave, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id {{giunzione}}
WHERE {{campo}} IN {{{{dentro}}}} AND f.copy_of IS NULL
GROUP BY chiave, o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente

_OGGETTI_DEL_CORREDO = _OGGETTI.format(chiave="f.rig_id", giunzione="", campo="f.rig_id")
_OGGETTI_DEL_FILTRO = _OGGETTI.format(chiave="f.filter_id", giunzione="", campo="f.filter_id")
# Anche qui il legame e' quello di `counts`, non una terza scrittura: le ore, le notti e gli
# oggetti di una riga devono venire dalle stesse pose, o la riga racconta tre archivi diversi.
# I corredi entrano nel `FROM` e il legame li usa di la'. La forma con la sotto-select, qui,
# costerebbe una ricerca correlata per ogni coppia (posa, pezzo): che il piano non la faccia lo
# prova `test_the_objects_of_a_piece_do_not_search_the_rigs_row_by_row`. La `LEFT` non e'
# decorativa: una posa che nomina una ruota puo' non avere corredo, e con una giunzione secca
# sparirebbe.
_OGGETTI_DEL_PEZZO = _OGGETTI.format(
    chiave="i.id",
    giunzione=(
        "LEFT JOIN rigs g ON g.id = f.rig_id JOIN instruments i ON "
        + counts.of("instrument", rigs_joined=True)
    ),
    campo="i.id",
)

# Quanto inquadra davvero un corredo: si prendono le pose risolte e si guarda quella di mezzo.
_CIELO = """
SELECT f.rig_id AS chiave, w.scale_arcsec_px, w.width_deg, w.height_deg
FROM frames f JOIN frame_wcs w ON w.frame_id = f.id
WHERE f.rig_id IN {dentro} AND f.copy_of IS NULL
"""

# I quattro numeri dell'uso di ogni riga.
USAGE = ("frames", "integration_s", "untimed", "nights")
_COLONNE = (
    "subject", "subject_id", *USAGE, "scale_arcsec_px", "width_deg", "height_deg",
    "objects_json", "position",
)  # fmt: skip


def write(conn):
    """Rifa' e scrive l'uso di tutto: una riga per pezzo, corredo e filtro. Si rifa' intero perche'
    una posa che cambia corredo sposta i numeri di quattro righe, e seguirle una per una vorrebbe
    dire sbagliarne una; tutto o niente (`db.replace_table.replace_rows`). L'ordine della pagina lo
    decide chi conta (`counts.ORDER_BY_TIME`), e si scrive come posizione."""
    righe = [
        (r["subject"], r["id"], *(r[c] for c in _COLONNE[2:-1]), n)
        for elenco in (_strumenti(conn), _corredi(conn), _filtri(conn))
        for n, r in enumerate(elenco)
    ]
    replace_rows(conn, "gear_usage", _COLONNE, righe)


def add_piece(conn, instrument_id, kind):
    """La riga di un pezzo appena scritto a mano, che non ha ancora ripreso niente: zero, o nulla
    per un genere le cui ore l'app non puo' sapere. Solo la sua: ricontare tutto l'archivio dentro
    la richiesta di chi lo crea costerebbe secondi."""
    _nuova(conn, "instrument", instrument_id, conta=kind in _con_le_ore(conn))


def add_new(conn, subject, row_id):
    """La riga di un filtro o di un corredo appena scritti a mano: zero, perche' le loro ore si
    sanno sempre -- la posa dice il suo filtro e il suo corredo."""
    _nuova(conn, subject, row_id, conta=True)


def _nuova(conn, subject, row_id, *, conta):
    """In fondo al suo elenco, che va dal piu' usato: con zero ore, in cima sarebbe falso."""
    conn.execute(
        "INSERT OR REPLACE INTO gear_usage(subject, subject_id, frames, integration_s, untimed,"
        " nights, objects_json, position) VALUES(?, ?, ?, ?, ?, ?, '[]',"
        " (SELECT COALESCE(MAX(position) + 1, 0) FROM gear_usage WHERE subject = ?))",
        (subject, row_id, *((0, 0.0, 0, 0) if conta else (None,) * 4), subject),
    )


def _con_le_ore(conn):
    """I generi le cui ore si sanno **in questo archivio**. Un genere che la posa nomina addosso a
    se' entra solo se **almeno una posa lo nomina**: la ruota che ti sei scritto a mano, se nessun
    file ne ha mai scritta una, non ha fatto zero ore, ha ore che l'app non puo' sapere."""
    generi: set[str] = set(_SEMPRE)
    for kind in counts.CARRIED:
        detto = conn.execute(
            f"SELECT 1 FROM frames WHERE {kind}_id IS NOT NULL LIMIT 1"  # noqa: S608 - generi nostri
        ).fetchone()
        if detto is not None:
            generi.add(kind)
    return generi


def _riga(subject, r, oggetti, *, conta=True, cielo=None):
    uso: dict = {c: r[c] for c in USAGE} if conta else dict.fromkeys(USAGE)
    cielo = cielo or {}
    return {
        "subject": subject,
        "id": r["id"],
        **uso,
        "scale_arcsec_px": cielo.get("scale_arcsec_px"),
        "width_deg": cielo.get("width_deg"),
        "height_deg": cielo.get("height_deg"),
        "objects_json": json.dumps(oggetti.get(r["id"], []) if conta else []),
    }


def _strumenti(conn):
    righe = conn.execute(_STRUMENTI).fetchall()
    con_le_ore = _con_le_ore(conn)
    ids = [r["id"] for r in righe if r["kind"] in con_le_ore]
    oggetti = idlist.grouped(conn, _OGGETTI_DEL_PEZZO, ids, "chiave", obj.counted)
    return [_riga("instrument", r, oggetti, conta=r["kind"] in con_le_ore) for r in righe]


def _corredi(conn):
    righe = conn.execute(_CORREDI).fetchall()
    ids = [r["id"] for r in righe]
    oggetti = idlist.grouped(conn, _OGGETTI_DEL_CORREDO, ids, "chiave", obj.counted)
    visto = idlist.grouped(conn, _CIELO, ids, "chiave", dict)
    return [
        _riga(
            "rig",
            r,
            oggetti,
            cielo={
                campo: hundredths(median([v[campo] for v in visto.get(r["id"], [])]))
                for campo in ("scale_arcsec_px", "width_deg", "height_deg")
            },
        )
        for r in righe
    ]


def _filtri(conn):
    righe = conn.execute(_FILTRI).fetchall()
    oggetti = idlist.grouped(
        conn, _OGGETTI_DEL_FILTRO, [r["id"] for r in righe], "chiave", obj.counted
    )
    return [_riga("filter", r, oggetti) for r in righe]
