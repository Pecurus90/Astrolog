"""Everything the user said, in one file next to the database (ADR 0017): rewritten after every
write of theirs, offered back on a new database. Ids are never in it: names, paths, fingerprints."""

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Final, NamedTuple

from .. import place
from ..clock import now_iso
from ..db import config
from ..db.transaction import transaction
from . import rigs
from .folder_move import SAMPLE_FILES

log = logging.getLogger(__name__)

FILE_NAME: Final = "risposte.json"
VERSION: Final = 1

_INSTRUMENT = (
    "kind", "name", "brand", "model", "aperture_mm", "focal_mm", "reducer_factor", "weight_kg",
    "payload_kg", "slots", "backfocus_mm", "notes",
)  # fmt: skip
_SITE = (
    "name", "latitude", "longitude", "elevation_m", "elevation_source", "sky_sqm", "sky_source",
    "horizon_json", "is_default",
)  # fmt: skip
# Not in the export: a declared solver path beats the search, and wrong elsewhere it stops it.
_STAYS_HERE: Final = config.SECRETS | {"astap_path"}
_FILTER = ("name", "brand", "model", "catalog_id", "passband", "is_none", "color")
_SAMPLE = (
    "SELECT p.rel_path, f.frame_hash FROM positions p JOIN frames f ON f.id = p.frame_id"
    " WHERE p.folder_id = ? ORDER BY p.rel_path LIMIT ?"
)


class BackupError(ValueError):
    """The file is not a backup this app can read."""


def path_for(db_path: str | Path) -> Path:
    return Path(db_path).with_name(FILE_NAME)


def collect(conn: sqlite3.Connection, *, this_machine: bool) -> dict[str, Any]:
    """The declared tables by their stable keys; `this_machine=False` for a file that leaves the
    machine: the export carries no service keys and no solver path (ADR 0017)."""
    rows = lambda sql, *a: [dict(r) for r in conn.execute(sql, a)]  # noqa: E731
    return {
        "version": VERSION,
        "written_at": now_iso(),
        "config": {
            r["key"]: r["value"]
            for r in conn.execute("SELECT key, value FROM config")
            if this_machine or r["key"] not in _STAYS_HERE
        },
        "sites": rows(f"SELECT {', '.join(_SITE)} FROM sites ORDER BY name"),  # noqa: S608
        "folders": [_folder(conn, r) for r in conn.execute("SELECT * FROM folders ORDER BY id")],
        "instruments": rows(
            f"SELECT {', '.join(_INSTRUMENT)} FROM instruments"  # noqa: S608 - constant columns
            " WHERE detected = 0 ORDER BY kind, name"
        ),
        "filters": [_filter(conn, r) for r in conn.execute("SELECT * FROM filters ORDER BY name")],
        "header_aliases": rows(
            "SELECT kind, header_value, target_key FROM header_aliases ORDER BY kind, header_value"
        ),
        "declarations": rows(
            "SELECT entity_type, entity_key, field, value, created_at FROM declarations"
            " ORDER BY entity_type, entity_key, field"
        ),
    }


def _folder(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    """With the files that tell it apart on another machine; a folder not yet read keeps the
    sample it came back with."""
    sample = [list(r) for r in conn.execute(_SAMPLE, (row["id"], SAMPLE_FILES))]
    if not sample and row["sample_json"]:
        sample = json.loads(row["sample_json"])
    return {
        "root_path": row["root_path"],
        "name": row["name"],
        "retired_at": row["retired_at"],
        "sample": sample,
    }


def _filter(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    bands = conn.execute(
        "SELECT band, width_nm FROM filter_bands WHERE filter_id = ? ORDER BY band", (row["id"],)
    )
    return {**{c: row[c] for c in _FILTER}, "bands": [dict(b) for b in bands]}


def write(conn: sqlite3.Connection, db_path: str | Path) -> None:
    """Whole and atomic: a crash mid-write leaves the previous file, never half of one."""
    target = path_for(db_path)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json_text(collect(conn, this_machine=True)), encoding="utf-8")
    os.replace(tmp, target)


def write_quietly(conn: sqlite3.Connection, db_path: str | Path) -> None:
    """After the user's answer is saved: a backup that cannot be written is logged, and the answer
    stands."""
    try:
        write(conn, db_path)
    except (OSError, sqlite3.Error):
        log.exception("backup delle risposte: il file non si e' potuto scrivere")


def json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def checked(data: object) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("version") != VERSION:
        raise BackupError("non e' un file di risposte di questa versione")
    return data


def load(text: str) -> dict[str, Any]:
    try:
        return checked(json.loads(text))
    except ValueError as e:
        raise BackupError("non e' un file di risposte") from e


def read(path: Path) -> dict[str, Any] | None:
    """`None` when there is no file; a file that is not a backup raises."""
    if not path.exists():
        return None
    return load(path.read_text(encoding="utf-8"))


def has_answers(data: dict[str, Any]) -> bool:
    return any(data.get(k) for k in _ANSWERS)


_ANSWERS: Final = (
    "config", "sites", "folders", "instruments", "filters", "header_aliases", "declarations",
)  # fmt: skip


def summary(data: dict[str, Any]) -> dict[str, Any]:
    """What the offer says: when, and how many of each."""
    return {
        "written_at": data.get("written_at"),
        "sites": len(data.get("sites", [])),
        "folders": len(data.get("folders", [])),
        "instruments": len(data.get("instruments", [])),
        "filters": len(data.get("filters", [])),
        "answers": len(data.get("declarations", [])) + len(data.get("header_aliases", [])),
    }


def restore(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    """Adds and updates, never deletes; ids re-linked by name. Rigs are not in the file: the scan
    rebuilds them and the declared ones come back by name at the end."""
    now = now_iso()
    with transaction(conn):
        for key, value in data.get("config", {}).items():
            # a solver path of another machine (a Windows path inside Docker) would stop the search
            if key in config.KEYS and (key != "astap_path" or (value and os.path.exists(value))):
                conn.execute(
                    "INSERT INTO config(key, value, updated_at) VALUES(?, ?, ?)"
                    " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                    " updated_at = excluded.updated_at",
                    (key, value, now),
                )
        for site in data.get("sites", []):
            _restore_site(conn, site, now)
        for folder in data.get("folders", []):
            _restore_folder(conn, folder, now)
        for instrument in data.get("instruments", []):
            _upsert(conn, _Table("instruments", _INSTRUMENT, ("kind", "name")), instrument, now)
        for f in data.get("filters", []):
            _restore_filter(conn, f, now)
        for a in data.get("header_aliases", []):
            conn.execute(
                "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
                " VALUES(?, ?, ?, ?) ON CONFLICT(kind, header_value)"
                " DO UPDATE SET target_key = excluded.target_key",
                (a["kind"], a["header_value"], a["target_key"], now),
            )
        for d in data.get("declarations", []):
            conn.execute(
                "INSERT OR REPLACE INTO declarations(entity_type, entity_key, field, value,"
                " created_at) VALUES(?, ?, ?, ?, ?)",
                (d["entity_type"], d["entity_key"], d["field"], d["value"], d["created_at"]),
            )
        rigs.restore_declared(conn, now)


class _Table(NamedTuple):
    name: str
    columns: tuple[str, ...]
    key: tuple[str, ...]


def _upsert(conn: sqlite3.Connection, t: _Table, row: dict[str, Any], now: str) -> int:
    table, key = t.name, t.key
    cols = [c for c in t.columns if c in row]
    sets = ", ".join(f"{c} = excluded.{c}" for c in cols if c not in key)
    conn.execute(
        f"INSERT INTO {table}({', '.join(cols)}, created_at)"  # noqa: S608 - constant tables
        f" VALUES({', '.join('?' * len(cols))}, ?)"  # segnaposto-ok: the columns, not the rows
        f" ON CONFLICT({', '.join(key)}) DO UPDATE SET {sets}",
        (*(row[c] for c in cols), now),
    )
    where = " AND ".join(f"{k} = ?" for k in key)
    found = conn.execute(f"SELECT id FROM {table} WHERE {where}", tuple(row[k] for k in key))  # noqa: S608
    return found.fetchone()[0]


def _restore_site(conn: sqlite3.Connection, site: dict[str, Any], now: str) -> None:
    """The zone is computed again, offline: it follows the coordinates, which are in the file."""
    if site.get("is_default"):
        conn.execute("UPDATE sites SET is_default = 0 WHERE is_default = 1 AND name <> ?",
                     (site["name"],))  # fmt: skip
    _upsert(conn, _Table("sites", _SITE, ("name",)), site, now)
    conn.execute(
        "UPDATE sites SET timezone = ? WHERE name = ?",
        (place.timezone_of(site["latitude"], site["longitude"]), site["name"]),
    )


def _restore_folder(conn: sqlite3.Connection, folder: dict[str, Any], now: str) -> None:
    """Back even if the path is not here: on another machine the move recognises it by its
    sample (`folder_move.same_files`)."""
    conn.execute(
        "INSERT INTO folders(root_path, name, retired_at, sample_json, created_at)"
        " VALUES(?, ?, ?, ?, ?) ON CONFLICT(root_path) DO UPDATE SET name = excluded.name,"
        " retired_at = excluded.retired_at, sample_json = excluded.sample_json",
        (folder["root_path"], folder["name"], folder["retired_at"],
         json.dumps(folder.get("sample", [])), now),
    )  # fmt: skip


def _restore_filter(conn: sqlite3.Connection, f: dict[str, Any], now: str) -> None:
    if f.get("is_none"):
        conn.execute("UPDATE filters SET is_none = 0 WHERE is_none = 1 AND name <> ?", (f["name"],))
    filter_id = _upsert(conn, _Table("filters", _FILTER, ("name",)), f, now)
    conn.execute("DELETE FROM filter_bands WHERE filter_id = ?", (filter_id,))
    conn.executemany(
        "INSERT INTO filter_bands(filter_id, band, width_nm) VALUES(?, ?, ?)",
        [(filter_id, b["band"], b["width_nm"]) for b in f.get("bands", [])],
    )
