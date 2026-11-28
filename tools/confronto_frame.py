"""The frames of two databases side by side: the bench of step 40.4 (ADR 0030). The scan that
writes `frames` changed hands, so the same archive is scanned and normalized with the code of tag
`prima-del-40` and with HEAD, and every frame is compared, paired by its first file.

Use:
  python tools/confronto_frame.py scansiona DB FOLDER... [--backend DIR]
  python tools/confronto_frame.py confronta A.db B.db [--stesso DA A]...

Frames pair by their first file: `--stesso` writes a link's target as the link.

No solver, no worker: only the scan and `normalize`, the stages whose columns the pages read
from `frames`. A frame on one side only is listed with its file; a column that differs is counted
with its first examples. HISTORY and COMMENT cards are left out of the header (accepted at 40.4).
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import confronto_pagine as cp

EXAMPLES = 5
# The scan's own bookkeeping, not what the frame says.
SKIP_COLUMNS = {"id", "frame_hash", "created_at"}
# Gear a frame points at, written by normalize: compared by name.
REFERENCES = {
    "filter_id", "rig_id", "filter_wheel_id", "focuser_id", "guide_camera_id", "mount_id",
    "reducer_id", "guide_scope_id", "oag_id",
}  # fmt: skip
# Notes, not facts (a blank key is commentary too, FITS 4.0 sec. 4.4.2.4): kept once per key.
NOTE_CARDS = {"HISTORY", "COMMENT", ""}


def _scan_one(conn: sqlite3.Connection, folder_id: int) -> Any:
    try:
        from astrolog.api.scan_door import scan_once  # HEAD: the new pipeline's scan
    except ImportError:
        from astrolog.spine.scan import scan_folder  # tag: the old scan

        return list(scan_folder(conn, folder_id))[-1]
    return scan_once(conn, folder_id)


def scan(folders: list[Path], db: Path) -> None:
    """The app's schema and folders, then one scan each and normalize, with the backend on the
    path. Several folders: the tag does not follow a link, so its target is given beside it."""
    if db.exists():
        raise SystemExit(f"{db}: exists, a scan starts from nothing")
    from astrolog.db.connect import connect
    from astrolog.spine.normalize import normalize_frames

    client = cp._client(db)
    ids = [cp._post(client, "/folders", {"root_path": str(f)}, 201)["id"] for f in folders]
    conn = connect(db)
    for folder_id in ids:
        sys.stderr.write(f"{db}: {_scan_one(conn, folder_id)}\n")
    list(normalize_frames(conn))


TAG_FILES = """SELECT p.frame_id, min(f.root_path || '/' || p.rel_path)
  FROM positions p JOIN folders f ON f.id = p.folder_id GROUP BY p.frame_id"""
HEAD_FILES = """SELECT p.frame_id, min(r.path || '/' || p.rel_path)
  FROM pipeline_files p JOIN pipeline_roots r ON r.id = p.root_id
  WHERE p.frame_id IS NOT NULL GROUP BY p.frame_id"""


def _paths(conn: sqlite3.Connection, same: list[tuple[str, str]]) -> dict[int, str]:
    """The first file of each frame, whole: positions in the tag, pipeline_files in HEAD.
    `same`: a root prefix written as another, a link's target as the link."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    out = {}
    for frame_id, path in conn.execute(TAG_FILES if "positions" in tables else HEAD_FILES):
        path = path.replace("\\", "/")
        for old, new in same:
            if path.startswith(old):
                path = new + path[len(old) :]
        out[frame_id] = path
    return out


def _header(raw: str) -> dict[str, Any]:
    pairs = json.loads(raw)
    items = pairs.items() if isinstance(pairs, dict) else pairs
    return {k: v for k, v in items if k not in NOTE_CARDS}


def _names(conn: sqlite3.Connection) -> dict[str, dict[int, str]]:
    """Ids follow insertion order: a reference compares by what it names."""
    gear = dict(conn.execute("SELECT id, kind || ' ' || name FROM instruments").fetchall())
    rigs = conn.execute(
        "SELECT r.id, coalesce(o.name, '-') || ' / ' || coalesce(c.name, '-') || ' ' || "
        "coalesce(r.focal_mm, '-') FROM rigs r LEFT JOIN instruments o ON o.id = r.optics_id "
        "LEFT JOIN instruments c ON c.id = r.camera_id"
    )
    return {
        "instruments": gear,
        "filters": dict(conn.execute("SELECT id, name FROM filters").fetchall()),
        "rigs": dict(rigs.fetchall()),
    }


def _named(d: dict[str, Any], names: dict[str, dict[int, str]]) -> None:
    for col in REFERENCES & d.keys():
        table = {"filter_id": "filters", "rig_id": "rigs"}.get(col, "instruments")
        if d[col] is not None:
            d[col] = names[table].get(d[col], f"? {d[col]}")


def frames(db: Path, same: list[tuple[str, str]]) -> dict[str, dict[str, Any]]:
    """Every frame by its first file: the fingerprint changed form at 40.4 (D1), the file did
    not. Its columns, references by name, its header without notes."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    paths = _paths(conn, same)
    names = _names(conn)
    out = {}
    for row in conn.execute("SELECT * FROM frames"):
        d = dict(row)
        _named(d, names)
        d["header"] = _header(d.pop("header_json"))
        d["file"] = paths.get(d["id"], f"(no file) {d['frame_hash']}")
        out[d["file"]] = d
    return out


def report(a: dict[str, dict[str, Any]], b: dict[str, dict[str, Any]]) -> list[str]:
    """Lines: frames on one side only, columns on one side only, each differing column."""
    lines = [f"frames: {len(a)} in A, {len(b)} in B, {len(a.keys() & b.keys())} in both"]
    for name, mine, other in (("A", a, b), ("B", b, a)):
        only = sorted(mine.keys() - other.keys(), key=lambda h: str(mine[h]["file"]))
        kinds = Counter(str(mine[h]["image_type"]) for h in only)
        lines.append(f"only in {name}: {len(only)} {dict(kinds)}")
        lines += [f"  {mine[h]['file']} ({mine[h]['image_type']})" for h in only]
    common = sorted(a.keys() & b.keys())
    if not common:
        return lines
    cols_a, cols_b = set(a[common[0]]), set(b[common[0]])
    for name, cols in (("A", cols_a - cols_b), ("B", cols_b - cols_a)):
        if cols:
            lines.append(f"columns only in {name}: {sorted(cols)}")
    diffs: dict[str, list[str]] = defaultdict(list)
    for h in common:
        for col in sorted((cols_a & cols_b) - SKIP_COLUMNS - {"header", "file"}):
            if a[h][col] != b[h][col]:
                diffs[col].append(f"{a[h]['file']}: {a[h][col]!r} -> {b[h][col]!r}")
        for d in cp.differences(a[h]["header"], b[h]["header"]):
            diffs["header"].append(f"{a[h]['file']} {d}")
    for col, found in sorted(diffs.items()):
        lines.append(f"{col}: {len(found)} differ")
        lines += [f"  {x}" for x in found[:EXAMPLES]]
    return lines


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="The frames of two databases")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scansiona")
    s.add_argument("db", type=Path)
    s.add_argument("folders", type=Path, nargs="+")
    s.add_argument("--backend")
    c = sub.add_parser("confronta")
    c.add_argument("a", type=Path)
    c.add_argument("b", type=Path)
    c.add_argument("--stesso", nargs=2, action="append", default=[], metavar=("DA", "A"))
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "scansiona":
        cp._use_backend(args.backend)
        scan([f.resolve() for f in args.folders], args.db.resolve())
        return 0
    same = [(old.replace("\\", "/"), new.replace("\\", "/")) for old, new in args.stesso]
    for line in report(frames(args.a, same), frames(args.b, same)):
        sys.stdout.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
