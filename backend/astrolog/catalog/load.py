"""The catalogue tables are fully derived: rebuilt from scratch on a new version, left alone on the
same one. They exist so identify can ask "what is in this patch of sky" with an indexed query."""

import json
import logging
import math
import sqlite3
from pathlib import Path
from typing import Any

from ..clock import now_iso
from . import bundle, designation

log = logging.getLogger(__name__)

PARSEC_LY = 3.2616  # [C IAU 2015 Resolution B2: 1 pc = 648000/pi au = 3.26156 ly]
# Full Moon's diameter at mean distance [C NASA Moon Fact Sheet: 3474.8 km at 384,400 km, 31.07']
MOON_ARCMIN = 31
MORE_MOONS = 1.5  # from here "more than N Moons" [D tavola v76, Riepilogo:132]
LIKE_THE_MOON = 0.9  # from here "like the full Moon" [D tavola v76, Riepilogo:132]
PARSEC_STEP = 10  # parsecs to the ten [D tavola v76, Riepilogo:156]
NO_PARSECS = 1_000_000  # from here only light years [D tavola v76, Riepilogo:156]


def unit_vector(ra_deg: float, dec_deg: float) -> tuple[float, float, float]:
    """On the unit sphere a cone search is a box on three indexed axes, and the right ascension
    wrap at 0/360 disappears instead of being a case to remember."""
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    return math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)


def loaded_version(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT version FROM catalog_version WHERE id = 1").fetchone()
    return row[0] if row else None


def _kinds(entry: dict[str, Any]) -> str | None:
    """Two fields in the file: `kind` is the main family and every entry has it, `k` holds only
    the extra ones, so both are read."""
    kinds = list(entry.get("k") or ())
    main = entry.get("kind")
    if main and main not in kinds:
        kinds.insert(0, main)
    return json.dumps(kinds) if kinds else None


def _designations(entry: dict[str, Any]) -> list[Any]:
    """Main designation first, each as `[catalogue, number]`."""
    return list(entry.get("n") or ())


def _entry_row(entry: dict[str, Any]) -> tuple[Any, ...]:
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
        extent_ly(entry.get("distance_ly"), entry.get("size_major_arcmin")),
        parsecs(entry.get("distance_ly")),
        *beside_the_moon(entry.get("size_major_arcmin")),
    )  # fmt: skip


def parsecs(distance_ly: float | None) -> float | None:
    """To the ten, half up as the board; none for the far ones, read in light years."""
    if distance_ly is None or distance_ly >= NO_PARSECS:
        return None
    return float(math.floor(distance_ly / PARSEC_LY / PARSEC_STEP + 0.5) * PARSEC_STEP)


def beside_the_moon(size_arcmin: float | None) -> tuple[str | None, int | None]:
    """`(more|like|less, whole Moons with more)` against the full Moon."""
    if not size_arcmin:
        return None, None
    moons = size_arcmin / MOON_ARCMIN
    if moons >= MORE_MOONS:
        return "more", math.floor(moons)
    return ("like" if moons >= LIKE_THE_MOON else "less"), None


def extent_ly(distance_ly: float | None, size_arcmin: float | None) -> float | None:
    """How big it really is, small angle, two figures: the catalog's numbers are not finer."""
    if not distance_ly or not size_arcmin:
        return None
    exact = distance_ly * math.radians(size_arcmin / 60)
    return round(exact, 1 - math.floor(math.log10(exact)))


def _name_rows(entries: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    """An unreadable code still loads but is logged, since its designations are unreachable. A
    designation claimed twice keeps the first; the primary is chosen after the drop, not before."""
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


def load_catalog(conn: sqlite3.Connection, file: str | Path | None = None) -> int:
    """Entries loaded: zero if this version is already in, or if the file is missing or unreadable,
    and the app starts anyway."""
    version, entries = bundle.read(file)
    if not version or loaded_version(conn) == version:
        return 0

    names = _name_rows(entries)
    now = now_iso()
    # By hand, not `db.transaction`: the layers in `backend/pyproject.toml` keep `db` out of reach.
    conn.execute("BEGIN")
    try:
        conn.execute("DELETE FROM catalog_names")
        conn.execute("DELETE FROM catalog_entries")
        conn.executemany(
            "INSERT INTO catalog_entries(slug, name, common_name, ra_deg, dec_deg, x, y, z,"
            " constellation, type_code, kinds_json, size_major_arcmin, size_minor_arcmin,"
            " position_angle_deg, magnitude, magnitude_band, surface_brightness, distance_ly,"
            " opacity, src_json, extent_ly, distance_pc, moon_compare, moon_count) VALUES("
            + ",".join("?" * 24)  # segnaposto-ok: twenty-four columns, not one per entry
            + ")",
            [_entry_row(e) for e in entries],
        )
        # No OR IGNORE: `_name_rows` already dropped the duplicates, so a conflict here is our bug.
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
