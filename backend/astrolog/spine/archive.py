"""Una pagina dell'**Archivio**: cosa hai ripreso, cercato, filtrato e ordinato.

Vincoli non ovvi (il perche' di righe, filtri e ordini sta in `docs/domini/archivio.md`):

* **Una riga e' un gruppo di pose, non un oggetto**: un mosaico confermato e' una riga sola
  (`frames.mosaic_key`, letta e mai ricalcolata), e quella di un oggetto porta solo le pose che
  nessun mosaico ha preso. Si impaginano righe.
* **Un filtro della barra fa passare il gruppo se una delle sue pose passa**, ognuno per conto suo:
  i pannelli sono oggetti di cataloghi diversi, e filtrando le pose la riga direbbe meno ore.
* **Righe e conta usano la stessa condizione**, e cio' che arriva da fuori non diventa mai SQL.
* **La ricerca guarda ogni nome e ogni designazione**, senza spazi e con la cassa piegata solo
  sull'ASCII, dai due lati: `LOWER()` di SQLite non tocca l'Unicode.
"""

from ..db import idlist
from . import counts
from .declarations import MOSAIC, MOSAIC_FIELD
from .object_answer import CATALOG, NAME
from .objects import NAME_COLUMNS, subjects_of, subjects_sql, together

# Le righe portano solo **chi sono**; le ore si contano fuori (`counts.counts_on("row")`), dopo il
# filtro: dentro l'unione si conterebbero per ogni riga, anche per la sola conta.
# La riga di un oggetto: un oggetto le cui pose stanno tutte in un mosaico non ne ha una -- le sue
# ore sono in quella del mosaico; uno senza pose ce l'ha. Il `NOT IN` non e' correlato e usa
# l'indice parziale `frames_mosaic`: a mani vuote non guarda nessuna posa. `object_id IS NOT NULL`
# perche' un solo NULL dentro un `NOT IN` lo fa fallire per tutti.
_OGGETTI = f"""
SELECT 'o:' || o.id AS chiave, o.id, NULL AS mosaic_key, o.catalog_slug, {NAME_COLUMNS},
       e.constellation, e.type_code, c.catalog, c.designation, NULL AS panels
FROM objects o
LEFT JOIN catalog_entries e ON e.slug = o.catalog_slug
LEFT JOIN catalog_names c ON c.slug = o.catalog_slug AND c.is_primary = 1
WHERE o.id NOT IN (SELECT f.object_id FROM frames f WHERE f.mosaic_key IS NOT NULL
                   AND f.copy_of IS NULL AND f.object_id IS NOT NULL)
   OR EXISTS (SELECT 1 FROM frames f WHERE f.object_id = o.id AND f.copy_of IS NULL
              AND {counts.ALONE})"""  # noqa: S608 - frammenti costanti della spina

# Il bersaglio della risposta sul mosaico, letto dal suo valore (`object_answer.target_value`):
# lo slug di catalogo o il nome scritto. E' il nome che l'utente ha dato, non una proposta. Come
# in `read_target`, un bersaglio vuoto o di soli spazi non e' un bersaglio.
_SLUG, _NOME = f"substr(d.value, {len(CATALOG) + 1})", f"substr(d.value, {len(NAME) + 1})"
_DEL_SLUG = f"CASE WHEN d.value LIKE '{CATALOG}%' AND TRIM({_SLUG}) <> '' THEN {_SLUG} END"
_DEL_NOME = f"CASE WHEN d.value LIKE '{NAME}%' AND TRIM({_NOME}) <> '' THEN {_NOME} END"

# La riga di un mosaico confermato: tutte le sue pose, col nome e il catalogo del bersaglio, e
# quanti pannelli ha, senza geometria. Si raggruppa **prima**, e la risposta si ritrova con la
# chiave del mosaico sull'indice di `declarations`.
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
LEFT JOIN catalog_names c ON c.slug = t.slug AND c.is_primary = 1"""  # noqa: S608 - frammenti costanti della spina

_RIGHE = f"({_OGGETTI} UNION ALL {_MOSAICI}) r"
_ORE = counts.counts_on("row")

# I tre ordini che la barra offre. **Per nome** non e' l'alfabeto nudo -- `M 13` finirebbe dopo
# `M 103` -- si legge catalogo e poi numero, e chi un catalogo non ce l'ha va in fondo.
# `COLLATE NOCASE` o `vdB` finirebbe dopo `WR`. La chiave della riga chiude sempre, o due pagine
# consecutive potrebbero mostrare la stessa riga due volte o saltarne una.
ORDINI = {
    "name": (
        "ORDER BY (r.catalog_slug IS NULL), r.catalog COLLATE NOCASE,"
        " CAST(r.designation AS INTEGER), r.designation COLLATE NOCASE,"
        " r.primary_name COLLATE NOCASE, r.chiave"
    ),
    "hours": f"{counts.ORDER_BY_TIME}, r.chiave",
    "frames": "ORDER BY frames DESC, integration_s DESC, r.chiave",
}

# Le pose di una riga `r`, e gli oggetti a cui appartengono: le due cose su cui la barra chiede.
# Gli oggetti di una riga oggetto sono lui solo -- anche senza pose, o un filtro sul catalogo lo
# perderebbe -- e i pannelli si cercano solo per un mosaico: per tutte le altre righe sarebbe una
# ricerca fra le pose che non trova niente di nuovo.
_POSE_DELLA_RIGA = f"f.copy_of IS NULL AND {counts.of('row')}"
_PANNELLI = (
    "r.mosaic_key IS NOT NULL AND o2.id IN (SELECT f.object_id FROM frames f"  # noqa: S608
    f" WHERE f.copy_of IS NULL AND {counts.of('mosaic')})"
)
_OGGETTI_DELLA_RIGA = f"(o2.id = r.id OR ({_PANNELLI}))"

# Una posa della riga ripresa con quel filtro. Basta **una**: la domanda della tendina e' "cosa ho
# ripreso in Ha", non "cosa ho ripreso prevalentemente in Ha".
_CON_IL_FILTRO = (
    "EXISTS (SELECT 1 FROM frames f JOIN filters x ON x.id = f.filter_id"  # noqa: S608
    f" WHERE {_POSE_DELLA_RIGA} AND x.name = ?)"
)
# La riga, o uno dei pannelli del mosaico, di quel catalogo o in quella costellazione. Per una
# riga oggetto `r.catalog` e `r.constellation` sono gia' quelli del suo oggetto; per un mosaico si
# parte dalle sue pose (`CROSS JOIN` fissa l'ordine), o SQLite partirebbe dalle migliaia di voci
# del catalogo scelto, per ogni mosaico.
_DAI_PANNELLI = (
    "r.mosaic_key IS NOT NULL AND EXISTS (SELECT 1 FROM frames f CROSS JOIN objects o2"  # noqa: S608
    " CROSS JOIN {tabella} WHERE f.copy_of IS NULL AND " + counts.of("mosaic") +
    " AND o2.id = f.object_id AND {legame} AND {colonna} = ?)"
)  # fmt: skip
_DEL_CATALOGO = (
    "(r.catalog = ? OR ("
    + _DAI_PANNELLI.format(  # noqa: S608 - costanti
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

# La tavola con cui si piega la cassa: **solo l'ASCII**, come fa `LOWER()` di SQLite. Sta qui
# e non dentro la funzione perche' si costruisce una volta, e perche' e' la meta' di una regola
# che vive su due lati -- chi la cambia deve vedere accanto il perche'.
_MINUSCOLE_ASCII = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

# Un nome come lo confronta la ricerca: senza spazi, con la cassa piegata da SQLite.
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


def _cercando(q):
    """Il pezzo di `WHERE` per cio' che l'utente ha scritto, coi suoi valori -- o niente.

    Uno spazio o il campo svuotato **non sono una ricerca**: si toglie il contorno e gli spazi
    prima di confrontare, o cancellare cio' che si era scritto lascerebbe un `LIKE '%   %'` che non
    trova niente. `%` e `_` sono i jolly di `LIKE`, e chi li scrive sta cercando **quei segni**."""
    scritto = (q or "").strip().translate(_MINUSCOLE_ASCII).replace(" ", "")
    if not scritto:
        return "", []
    scudato = scritto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return _CERCATO, [f"%{scudato}%"] * _CERCATO.count("LIKE ?")


def _dove(q=None, catalog=None, constellation=None, filter_name=None, mosaic=False):
    """La condizione di questa pagina, coi suoi valori. Una sola, usata dalle righe **e** dalle
    conte: due copie vorrebbero dire una pagina che dice "3 oggetti" e ne mostra 4."""
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


def page(conn, *, limit, offset, sort="name", **criteri):
    """Le righe di questa pagina **e quante righe passano il filtro**; `criteri` sono quelli di
    `_dove`.

    La conta viaggia con le righe e non a parte perche' e' la stessa domanda: con un filtro acceso
    dire quante righe hai in archivio sarebbe un numero che mente, ed e' anche il numero su cui la
    pagina decide se ce n'e' un'altra."""
    ordine = ORDINI[sort]  # da un elenco chiuso: cio' che arriva da fuori non diventa `ORDER BY`
    dove, valori = _dove(**criteri)
    righe = conn.execute(
        f"SELECT r.*, {_ORE} FROM {_RIGHE} WHERE {dove} {ordine} LIMIT ? OFFSET ?",  # noqa: S608
        (*valori, limit, offset),
    )
    quanti = conn.execute(
        f"SELECT COUNT(*) FROM {_RIGHE} WHERE {dove}",  # noqa: S608 - `dove` sono segnaposto
        valori,
    ).fetchone()[0]
    return [dict(r) for r in righe], quanti


def found(conn, **criteri):
    """Quante delle righe che passano il filtro sono oggetti e quanti mosaici: la conta a schermo
    non chiama "oggetto" un mosaico. Stessa condizione delle righe (`_dove`)."""
    dove, valori = _dove(**criteri)
    sql = (
        "SELECT COALESCE(SUM(r.mosaic_key IS NULL), 0), COALESCE(SUM(r.mosaic_key IS NOT NULL), 0)"  # noqa: S608 - `dove` sono segnaposto
        f" FROM {_RIGHE} WHERE {dove}"
    )
    oggetti, mosaici = conn.execute(sql, valori).fetchone()
    return {"objects": oggetti, "mosaics": mosaici}


# I filtri che hanno ripreso un oggetto, per la tendina: per ogni filtro basta la prima posa buona,
# e l'indice su `frames.filter_id` tiene breve anche la ricerca di chi non ne ha. Un `JOIN` con
# `DISTINCT` le legge tutte.
FILTERS_USED = (
    "SELECT x.name FROM filters x WHERE EXISTS (SELECT 1 FROM frames f WHERE f.filter_id = x.id"
    " AND f.object_id IS NOT NULL AND f.copy_of IS NULL) ORDER BY x.name COLLATE NOCASE"
)


def choices(conn):
    """Cosa offrono le tendine: **cio' che c'e' in archivio**, non cio' che il catalogo
    conosce. Ordinate come le righe, `COLLATE NOCASE`: senza, `vdB` uscirebbe dopo `WR` qui e
    prima di la', cioe' la stessa pagina ordinerebbe la stessa cosa in due modi -- e i nomi dei
    filtri li scrive l'utente, quindi li' capita di sicuro, non per ipotesi.

    Le sigle e le costellazioni del catalogo sono molte piu' di quelle che un archivio tocca --
    quante, lo conta la prova qui accanto -- e offrirle tutte a chi ne usa due e' una tendina che
    fa perdere tempo. E' la stessa regola delle ore per genere: per archivio, non per elenco
    fisso."""
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
        # i filtri che hanno ripreso **un oggetto**: uno posseduto e mai usato non stringe niente
        "filters": _elenco(conn, FILTERS_USED),
        # "solo i mosaici" si offre a chi ne ha uno confermato: l'indice parziale lo dice subito
        "mosaics": conn.execute(
            "SELECT EXISTS (SELECT 1 FROM frames WHERE mosaic_key IS NOT NULL)"
        ).fetchone()[0]
        == 1,
    }


# I pannelli di un mosaico confermato: le sue pose per inquadratura, col centro che ha scritto chi
# le ha raggruppate (`panels`). Si contano come ogni riga, dal pannello con piu' tempo.
_PANNELLI = f"""
SELECT f.mosaic_key, f.panel_id, p.ra_deg, p.dec_deg, {counts.AGGREGATE}, {counts.UNTIMED}
FROM frames f JOIN panels p ON p.id = f.panel_id
WHERE f.mosaic_key IN {{dentro}} AND f.copy_of IS NULL
GROUP BY f.mosaic_key, f.panel_id
{counts.ORDER_BY_TIME}, f.panel_id"""  # noqa: S608 - frammenti costanti, `dentro` e' un segnaposto
_OGGETTI_DEI_PANNELLI = subjects_sql("f.panel_id", where="AND f.mosaic_key IN {dentro}")


def panels(conn, keys):
    """`{chiave del mosaico: [pannello]}` per i mosaici di una pagina, in due domande per tutta la
    pagina. Un pannello senza oggetto ha `object` nullo: un nome non s'inventa."""
    if not keys:
        return {}  # la pagina di chi non ha mosaici, cioe' quasi tutte: nessuna domanda
    with idlist.holding(conn, keys) as elencate:
        oggetti = subjects_of(conn.execute(_OGGETTI_DEI_PANNELLI.format(dentro=elencate)))
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


def _elenco(conn, sql):
    return [r[0] for r in conn.execute(sql)]
