"""An Archive page: a row is a group of frames, a confirmed mosaic being one row. Rows and count
share one condition, and nothing from outside becomes SQL (`docs/domini/archivio.md`)."""

import sqlite3
from typing import Any

from ..db import idlist
from . import counts
from .declarations import MOSAIC, MOSAIC_FIELD
from .object_answer import CATALOG, NAME
from .objects import NAME_COLUMNS, subjects_of, subjects_sql, together

# Rows say only who they are; hours are counted after the filter, or the count would pay for them.
# The `NOT IN` uses the partial index; `object_id IS NOT NULL` since one NULL in it fails them all.
_OGGETTI = f"""
SELECT 'o:' || o.id AS chiave, o.id, NULL AS mosaic_key, o.catalog_slug, {NAME_COLUMNS},
       e.constellation, e.type_code, c.catalog, c.designation, NULL AS panels
FROM objects o
LEFT JOIN catalog_entries e ON e.slug = o.catalog_slug
LEFT JOIN catalog_names c ON c.slug = o.catalog_slug AND c.is_primary = 1
WHERE o.id NOT IN (SELECT f.object_id FROM frames f WHERE f.mosaic_key IS NOT NULL
                   AND f.copy_of IS NULL AND f.object_id IS NOT NULL)
   OR EXISTS (SELECT 1 FROM frames f WHERE f.object_id = o.id AND f.copy_of IS NULL
              AND {counts.ALONE})"""  # noqa: S608 - constant fragments of the spine

# The user's target, slug or written name; as in `read_target`, a blank target is not one.
_SLUG, _NOME = f"substr(d.value, {len(CATALOG) + 1})", f"substr(d.value, {len(NAME) + 1})"
_DEL_SLUG = f"CASE WHEN d.value LIKE '{CATALOG}%' AND TRIM({_SLUG}) <> '' THEN {_SLUG} END"
_DEL_NOME = f"CASE WHEN d.value LIKE '{NAME}%' AND TRIM({_NOME}) <> '' THEN {_NOME} END"

# Grouped first, so the answer is found by mosaic key on the `declarations` index.
_MOSAICI = f"""
SELECT 'm:' || g.mosaic_key AS chiave, NULL AS id, g.mosaic_key, t.slug AS catalog_slug,
       t.nome AS primary_name, e.name AS catalog_name,
       e.constellation, e.type_code, c.catalog, c.designation, g.panels
FROM (SELECT f.mosaic_key, COUNT(DISTINCT f.panel_id) AS panels FROM frames f
      WHERE f.mosaic_key IS NOT NULL AND f.copy_of IS NULL GROUP BY f.mosaic_key) g
LEFT JOIN (SELECT d.entity_key, d.field, {_DEL_SLUG} AS slug, {_DEL_NOME} AS nome
           FROM declarations d WHERE d.entity_type = '{MOSAIC}' AND d.field = '{MOSAIC_FIELD}') t
       ON t.entity_key = g.mosaic_key
LEFT JOIN catalog_entries e ON e.slug = t.slug
LEFT JOIN catalog_names c ON c.slug = t.slug AND c.is_primary = 1"""  # noqa: S608 - constant fragments of the spine

_RIGHE = f"({_OGGETTI} UNION ALL {_MOSAICI}) r"
_ORE = counts.counts_on("row")

# By name is catalog then number, or `M 13` would follow `M 103`; `NOCASE` or `vdB` follows `WR`.
# The row key always closes, or two consecutive pages could repeat or skip a row.
ORDINI = {
    "name": (
        "ORDER BY (r.catalog_slug IS NULL), r.catalog COLLATE NOCASE,"
        " CAST(r.designation AS INTEGER), r.designation COLLATE NOCASE,"
        " r.primary_name COLLATE NOCASE, r.chiave"
    ),
    "hours": f"{counts.ORDER_BY_TIME}, r.chiave",
    "frames": "ORDER BY frames DESC, integration_s DESC, r.chiave",
}

# An object row's objects are itself, even without frames, or a catalog filter would lose it;
# panels are looked up only for a mosaic, elsewhere the search would find nothing new.
_POSE_DELLA_RIGA = f"f.copy_of IS NULL AND {counts.of('row')}"
_PANNELLI = (
    "r.mosaic_key IS NOT NULL AND o2.id IN (SELECT f.object_id FROM frames f"  # noqa: S608
    f" WHERE f.copy_of IS NULL AND {counts.of('mosaic')})"
)
_OGGETTI_DELLA_RIGA = f"(o2.id = r.id OR ({_PANNELLI}))"

# One frame is enough: the question is "what did I shoot in Ha", not "mostly in Ha".
_CON_IL_FILTRO = (
    "EXISTS (SELECT 1 FROM frames f JOIN filters x ON x.id = f.filter_id"  # noqa: S608
    f" WHERE {_POSE_DELLA_RIGA} AND x.name = ?)"
)
# For a mosaic, start from its frames (`CROSS JOIN` fixes the order), or SQLite would start from
# the chosen catalog's thousands of entries, for every mosaic.
_DAI_PANNELLI = (
    "r.mosaic_key IS NOT NULL AND EXISTS (SELECT 1 FROM frames f CROSS JOIN objects o2"  # noqa: S608
    " CROSS JOIN {tabella} WHERE f.copy_of IS NULL AND " + counts.of("mosaic") +
    " AND o2.id = f.object_id AND {legame} AND {colonna} = ?)"
)  # fmt: skip
_DEL_CATALOGO = (
    "(r.catalog = ? OR ("
    + _DAI_PANNELLI.format(  # noqa: S608 - constants
        tabella="catalog_names c2",
        legame="c2.slug = o2.catalog_slug AND c2.is_primary = 1",
        colonna="c2.catalog",
    )
    + "))"
)
_NELLA_COSTELLAZIONE = (
    "(r.constellation = ? OR ("
    + _DAI_PANNELLI.format(  # noqa: S608
        tabella="catalog_entries e2", legame="e2.slug = o2.catalog_slug", colonna="e2.constellation"
    )
    + "))"
)

# ASCII only, as SQLite's `LOWER()`: half of a rule that lives on both sides.
_MINUSCOLE_ASCII = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

_PIEGATO = "REPLACE(LOWER({}), ' ', '') LIKE ? ESCAPE '\\'"
_CERCATO = (
    "(EXISTS (SELECT 1 FROM objects o2 WHERE " + _OGGETTI_DELLA_RIGA +  # noqa: S608
    "   AND (EXISTS (SELECT 1 FROM object_names n WHERE n.object_id = o2.id AND "
    + _PIEGATO.format("n.name") + ")"
    "   OR EXISTS (SELECT 1 FROM catalog_names k WHERE k.slug = o2.catalog_slug AND "
    + _PIEGATO.format("k.catalog || k.designation") + ")))"
    " OR " + _PIEGATO.format("r.primary_name") +
    " OR EXISTS (SELECT 1 FROM catalog_names k WHERE k.slug = r.catalog_slug AND "
    + _PIEGATO.format("k.catalog || k.designation") + "))"
)  # fmt: skip


def _cercando(q: str | None) -> tuple[str, list[str]]:
    """Blanks or an emptied field are no search, or a `LIKE '%   %'` would find nothing. `%` and
    `_` are escaped: who types them is looking for those signs."""
    scritto = (q or "").strip().translate(_MINUSCOLE_ASCII).replace(" ", "")
    if not scritto:
        return "", []
    scudato = scritto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return _CERCATO, [f"%{scudato}%"] * _CERCATO.count("LIKE ?")


def _dove(
    q: str | None = None,
    catalog: str | None = None,
    constellation: str | None = None,
    filter_name: str | None = None,
    mosaic: bool = False,
) -> tuple[str, list[str]]:
    """One condition for rows and counts: two copies would say "3 objects" and show 4."""
    pezzi, valori = ["1 = 1"], []
    if mosaic:
        pezzi.append("r.mosaic_key IS NOT NULL")
    cercato, suoi = _cercando(q)
    if cercato:
        pezzi.append(cercato)
        valori += suoi
    for pezzo, valore in ((_DEL_CATALOGO, catalog), (_NELLA_COSTELLAZIONE, constellation)):
        if valore:
            pezzi.append(pezzo)
            valori += [valore, valore]
    if filter_name:
        pezzi.append(_CON_IL_FILTRO)
        valori.append(filter_name)
    return " AND ".join(pezzi), valori


def page(
    conn: sqlite3.Connection, *, limit: int, offset: int, sort: str = "name", **criteri: Any
) -> tuple[list[dict[str, Any]], int]:
    """The rows and how many pass the filter, `criteri` being `_dove`'s: with a filter on, the
    archive's total would lie, and the page decides on it whether another follows."""
    ordine = ORDINI[sort]  # from a closed list: nothing from outside becomes `ORDER BY`
    dove, valori = _dove(**criteri)
    righe = conn.execute(
        f"SELECT r.*, {_ORE} FROM {_RIGHE} WHERE {dove} {ordine} LIMIT ? OFFSET ?",  # noqa: S608
        (*valori, limit, offset),
    )
    quanti = conn.execute(
        f"SELECT COUNT(*) FROM {_RIGHE} WHERE {dove}",  # noqa: S608 - `dove` are placeholders
        valori,
    ).fetchone()[0]
    return [dict(r) for r in righe], quanti


def found(conn: sqlite3.Connection, **criteri: Any) -> dict[str, int]:
    """Objects and mosaics apart: the on-screen count does not call a mosaic an object."""
    dove, valori = _dove(**criteri)
    sql = (
        "SELECT COALESCE(SUM(r.mosaic_key IS NULL), 0), COALESCE(SUM(r.mosaic_key IS NOT NULL), 0)"  # noqa: S608 - `dove` are placeholders
        f" FROM {_RIGHE} WHERE {dove}"
    )
    oggetti, mosaici = conn.execute(sql, valori).fetchone()
    return {"objects": oggetti, "mosaics": mosaici}


# The first good frame per filter is enough, and the `frames.filter_id` index keeps the search
# short; a `JOIN` with `DISTINCT` would read them all.
FILTERS_USED = (
    "SELECT x.name FROM filters x WHERE EXISTS (SELECT 1 FROM frames f WHERE f.filter_id = x.id"
    " AND f.object_id IS NOT NULL AND f.copy_of IS NULL) ORDER BY x.name COLLATE NOCASE"
)


def choices(conn: sqlite3.Connection) -> dict[str, Any]:
    """What the archive holds, not what the catalog knows; `NOCASE` like the rows, or `vdB` would
    sort apart here and there, and the user's filter names mix case for sure."""
    return {
        "catalogs": _elenco(
            conn,
            "SELECT DISTINCT c.catalog FROM objects o"
            " JOIN catalog_names c ON c.slug = o.catalog_slug AND c.is_primary = 1"
            " ORDER BY c.catalog COLLATE NOCASE",
        ),
        "constellations": _elenco(
            conn,
            "SELECT DISTINCT e.constellation FROM objects o"
            " JOIN catalog_entries e ON e.slug = o.catalog_slug"
            " ORDER BY e.constellation COLLATE NOCASE",
        ),
        # filters that shot an object: one owned and never used narrows nothing
        "filters": _elenco(conn, FILTERS_USED),
        # offered to whoever has a confirmed mosaic: the partial index says so at once
        "mosaics": conn.execute(
            "SELECT EXISTS (SELECT 1 FROM frames WHERE mosaic_key IS NOT NULL)"
        ).fetchone()[0]
        == 1,
    }


# By framing, with the centre `group` wrote, counted like every row, longest first.
_PANNELLI = f"""
SELECT f.mosaic_key, f.panel_id, p.ra_deg, p.dec_deg, {counts.AGGREGATE}, {counts.UNTIMED}
FROM frames f JOIN panels p ON p.id = f.panel_id
WHERE f.mosaic_key IN {{listed}} AND f.copy_of IS NULL
GROUP BY f.mosaic_key, f.panel_id
{counts.ORDER_BY_TIME}, f.panel_id"""  # noqa: S608 - constant fragments, `listed` a placeholder
_OGGETTI_DEI_PANNELLI = subjects_sql("f.panel_id", where="AND f.mosaic_key IN {listed}")


def panels(conn: sqlite3.Connection, keys: list[str]) -> dict[Any, list[Any]]:
    """`{mosaic key: [panel]}`, two queries for the whole page. A panel without an object has a
    null `object`: a name is not invented."""
    if not keys:
        return {}  # the page of whoever has no mosaics, nearly all: no query
    with idlist.holding(conn, keys) as elencate:
        oggetti = subjects_of(conn.execute(_OGGETTI_DEI_PANNELLI.format(listed=elencate)))
    return idlist.grouped(
        conn,
        _PANNELLI,
        keys,
        "mosaic_key",
        lambda r: {
            "object": together(oggetti.get(r["panel_id"], [])) or None,
            "ra_deg": r["ra_deg"],
            "dec_deg": r["dec_deg"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
        },
    )


def _elenco(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [r[0] for r in conn.execute(sql)]
