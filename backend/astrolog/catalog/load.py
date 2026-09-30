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
    )  # fmt: skip


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
            " opacity, src_json) VALUES("
            + ",".join("?" * 20)  # segnaposto-ok: twenty columns, not one per entry
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
