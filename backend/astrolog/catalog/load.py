"""Portare il catalogo dal file impacchettato alle tabelle del database.

Vincolo non ovvio: le tabelle del catalogo sono **derivate al 100%**. Si rifanno da capo a
ogni versione nuova -- le voci vecchie se ne vanno, non si sommano -- e non si rifanno affatto
se la versione caricata e' gia' quella: ventiduemila voci sono un lavoro che non ha senso
ripetere a ogni avvio. Il catalogo sta nel database e non solo nel file perche' `identify`
deve poter chiedere "cosa c'e' in questo pezzo di cielo" con una query, non leggendo
ventiduemila voci per ogni posa.
"""

import json
import logging
import math

from ..clock import now_iso
from . import bundle, designation

log = logging.getLogger(__name__)


def unit_vector(ra_deg, dec_deg):
    """Le coordinate sulla sfera unitaria. E' cio' che rende la ricerca per cono un riquadro
    su tre assi -- che un indice sa fare -- e fa sparire il salto dell'ascensione retta a
    0/360, invece di lasciarlo li' come caso da ricordarsi."""
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    return math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)


def loaded_version(conn):
    row = conn.execute("SELECT version FROM catalog_version WHERE id = 1").fetchone()
    return row[0] if row else None


def _kinds(entry) -> str | None:
    """Le famiglie d'uso di una voce, per i filtri. Sono DUE campi nel file: `kind` e' la
    principale e ce l'hanno tutte, `k` sono quelle in piu' e ce l'hanno cinquecento. Leggere
    solo `k` lasciava la colonna vuota per il 97,7% del catalogo."""
    kinds = list(entry.get("k") or ())
    main = entry.get("kind")
    if main and main not in kinds:
        kinds.insert(0, main)
    return json.dumps(kinds) if kinds else None


def _designations(entry) -> list:
    """Le designazioni di una voce, la principale per prima. Ognuna e' `[catalogo, numero]`."""
    return list(entry.get("n") or ())


def _entry_row(entry):
    x, y, z = unit_vector(entry["ra"], entry["dec"])
    return (
        entry["slug"], entry["name"], entry.get("common_name"),
        entry["ra"], entry["dec"], x, y, z,
        entry.get("constellation"), entry.get("type_code"),
        _kinds(entry),
        entry.get("size_major_arcmin"), entry.get("size_minor_arcmin"),
        entry.get("position_angle_deg"), entry.get("magnitude"), entry.get("magnitude_band"),
        entry.get("surface_brightness"), entry.get("distance_ly"), entry.get("opacity"),
        json.dumps(entry["src"]) if entry.get("src") else None,
    )  # fmt: skip


def _name_rows(entries):
    """Una riga per designazione, con la chiave gia' normalizzata: e' la chiave che `lookup`
    cerca, e normalizzarla qui e' cio' che permette all'indice di lavorare.

    Un codice di catalogo che `designation` non conosce entra lo stesso -- la voce vale anche
    senza quella sigla -- ma **si dice**: la sua chiave non e' una che il lettore produrra' mai,
    quindi quella sigla e' irraggiungibile. E' lo stesso guasto delle 313 Sharpless, e senza
    l'avviso il prossimo catalogo lo rifarebbe in silenzio.

    Due voci che rivendicano la stessa sigla sono un difetto del file impacchettato, non
    dell'app: la prima vince e il conto lo dice, invece di far fallire l'avvio per un dato che
    l'utente non puo' correggere. La scelta della **principale** viene dopo lo scarto, non
    prima: chi perdesse cosi' la sua prima sigla resterebbe senza principale, e la principale
    e' quel che si mostra quando un oggetto non ha un nome comune."""
    rows, seen, unknown, dropped = [], set(), set(), 0
    for entry in entries:
        primary = True
        for catalog, number in _designations(entry):
            key = designation.key(f"{catalog} {number}")
            if key is None:
                unknown.add(catalog)
                key = f"{catalog}|{number}".upper()
            if key in seen:
                dropped += 1
                continue
            seen.add(key)
            rows.append((catalog, number, key, entry["slug"], 1 if primary else 0))
            primary = False
    if unknown:
        log.warning(
            "catalogo: %d codici che non si sanno leggere, le loro sigle non si cercheranno: %s",
            len(unknown),
            ", ".join(sorted(unknown)),
        )
    if dropped:
        log.warning("catalogo: %d sigle rivendicate da piu' voci, tenuta la prima", dropped)
    return rows


def load_catalog(conn, file=None):
    """Carica il catalogo nelle tabelle. Torna quante voci sono entrate: **zero** se era gia'
    caricato, o se il file manca o non si capisce -- e in quel caso l'app parte lo stesso."""
    version, entries = bundle.read(file)
    if not version or loaded_version(conn) == version:
        return 0

    names = _name_rows(entries)
    now = now_iso()
    conn.execute("BEGIN")
    try:
        # da capo: un catalogo nuovo sostituisce il vecchio, non ci si somma
        conn.execute("DELETE FROM catalog_names")
        conn.execute("DELETE FROM catalog_entries")
        conn.executemany(
            "INSERT INTO catalog_entries(slug, name, common_name, ra_deg, dec_deg, x, y, z,"
            " constellation, type_code, kinds_json, size_major_arcmin, size_minor_arcmin,"
            " position_angle_deg, magnitude, magnitude_band, surface_brightness, distance_ly,"
            " opacity, src_json) VALUES("
            + ",".join("?" * 20)  # segnaposto-ok: venti colonne, non una riga per voce
            + ")",
            [_entry_row(e) for e in entries],
        )
        # Senza OR IGNORE: i doppioni li ha gia' tolti `_name_rows`, che sa anche rimettere a
        # posto la principale. Qui un conflitto sarebbe un difetto nostro, e va visto.
        conn.executemany(
            "INSERT INTO catalog_names(catalog, designation, key, slug, is_primary)"
            " VALUES(?, ?, ?, ?, ?)",
            names,
        )
        conn.execute(
            "INSERT INTO catalog_version(id, version, entries, loaded_at) VALUES(1, ?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET version = excluded.version,"
            " entries = excluded.entries, loaded_at = excluded.loaded_at",
            (version, len(entries), now),
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    log.info("catalogo: caricate %d voci, versione %s", len(entries), version)
    return len(entries)
