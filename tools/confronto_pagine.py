"""The pages' API answers of two databases side by side: the bench of step 40 (ADR 0030). Each
slice that retires an old stage builds a copy with the code of tag `prima-del-40` and with HEAD,
exports both and lists every difference; each one needs a written reason.

Use:
  python tools/confronto_pagine.py costruisci FOLDER DB [--backend DIR] [--sito LAT LON QUOTA_M]
  python tools/confronto_pagine.py esporta DB OUT.json [--backend DIR]
  python tools/confronto_pagine.py confronta A.json B.json

`--backend` runs another checkout's code, a worktree of the tag (`git worktree add T prima-del-40`).
Point `costruisci` at a copy of the archive: it runs the app's own scan, real ASTAP included, and
waits for the worker and for the new pipeline behind it. Export both sides on the same day: the
calendar's last month is tonight's. Lists compare by position: one item less shifts the ones after
it; compare by key when a slice's real difference drowns in that noise.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
API = "/api/v1"
PAGE = 500  # the routes' own cap on `limit`
# Numeric ids follow insertion order and merges: two equal archives may number them apart.
ID_SUFFIXES = ("_id", "_ids")
# The calendar's "now": tonight at home moves with the clock, not with the archive.
NOW_FIELDS = {"tonight", "last_month"}
BACKUP = "risposte.json"

Get = Callable[[str], Any]


def _use_backend(backend: str | None) -> None:
    sys.path.insert(0, str(Path(backend).resolve() if backend else HERE.parent / "backend"))


def _client(db: Path) -> Any:
    """No `with`: the lifespan (scheduler, weather, tonight's sky) does not start. No data root:
    folders anywhere, as on a desktop, and a stale schema is an error, never set aside."""
    from fastapi.testclient import TestClient

    from astrolog.api.app import create_app

    os.environ.pop("ASTROLOG_DATA_ROOT", None)
    return TestClient(create_app(db), base_url="http://localhost")


def _getter(client: Any) -> Get:
    def get(path: str) -> Any:
        r = client.get(API + path)
        if r.status_code != 200:
            raise SystemExit(f"GET {path}: {r.status_code} {r.text[:300]}")
        return r.json()

    return get


def _post(client: Any, path: str, body: Any, code: int) -> Any:
    r = client.post(API + path, json=body)
    if r.status_code != code:
        raise SystemExit(f"POST {path}: {r.status_code} {r.text[:300]}")
    return r.json()


def _idle(state: Any) -> None:
    """The worker's last stage kicks the new pipeline: worker, then behind, until both rest."""
    while True:
        state.worker.join()
        state.behind.join()
        if not state.worker.is_running():
            return


def build(folder: Path, db: Path, site: list[float] | None = None) -> None:
    """The archive as the app builds it: the home site (no night without one), the folder added,
    one scan, everything behind it done. The elevation given: no service asked. With a site,
    every place the header coordinates ask about is answered home, as a user would."""
    if db.exists():
        raise SystemExit(f"{db}: exists, a build starts from nothing")
    if (db.parent / BACKUP).exists():  # the app's backup sits beside its database
        raise SystemExit(f"{db.parent}: holds another build's {BACKUP}, one folder per build")
    os.environ["ASTROLOG_DATA_DIR"] = str(db.parent / f"dati-{db.stem}")  # ASTAP's work, cache
    client = _client(db)
    home = None
    if site:
        lat, lon, elevation = site
        body = {"name": "Casa", "latitude": lat, "longitude": lon, "elevation_m": elevation}
        home = _post(client, "/sites", body, 201)["id"]
        _post(client, f"/sites/{home}/default", None, 200)
    _post(client, "/folders", {"root_path": str(folder)}, 201)
    _post(client, "/scan", None, 202)
    _idle(client.app.state)
    unclear = _getter(client)("/review")["unclear"] if home else []
    if unclear:
        answers = [{"key": u["key"], "site_id": home} for u in unclear]
        _post(client, "/review/apply", {"unclear": answers}, 200)
        _idle(client.app.state)
    snap = client.app.state.worker.snapshot()
    nights = _getter(client)("/nights?limit=1")
    sys.stderr.write(f"{db}: worker {snap.state}, error {snap.error}, {nights['total']} nights\n")
    if not nights["total"]:  # e.g. a copy without its dates: every file "still writing"
        raise SystemExit(f"{db}: no night built, nothing to compare ({nights['empty']})")


def _pages(get: Get, path: str) -> tuple[Any, list[Any]]:
    """The first page whole and every item of all pages."""
    sep = "&" if "?" in path else "?"
    first = get(f"{path}{sep}limit={PAGE}&offset=0")
    items = list(first["items"])
    while len(items) < first["total"]:
        items += get(f"{path}{sep}limit={PAGE}&offset={len(items)}")["items"]
    return first, items


def _nights(get: Get) -> dict[str, Any]:
    first, items = _pages(get, "/nights")
    out: dict[str, Any] = {"list": {**first, "items": items}, "nights": {}, "calendar": {}}
    for night in items:
        key = f"{night['night_date']} {night['site']}"
        out["nights"][key] = {
            "detail": get(f"/nights/{night['id']}"),
            "measures": get(f"/nights/{night['id']}/measures"),
        }
    for month in first["months"]:
        out["calendar"][month["month"]] = get(f"/nights/calendar?month={month['month']}")
    return out


def _tabs(row: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """The object window's tabs: the whole row, each production, each panel."""
    yield "all", ""
    for p in row.get("productions") or []:
        o, c = p["optics_id"], p["camera_id"]
        o, c = "none" if o is None else o, "none" if c is None else c
        yield f"production {p['optics']} / {p['camera']}", f"?production={o}:{c}"
    for p in row.get("panel_list") or []:
        yield f"panel {p['object']} {p['ra_deg']:.4f} {p['dec_deg']:.4f}", f"?panel={p['id']}"


def _archive(get: Get) -> dict[str, Any]:
    out: dict[str, Any] = {"objects": {}}
    for sort in ("name", "hours", "recent"):
        first, items = _pages(get, f"/archive?sort={sort}")
        out[f"list {sort}"] = {**first, "items": items}
    for row in out["list name"]["items"]:
        key = row["key"]
        tabs = out["objects"][key] = {}
        for name, query in _tabs(row):
            tabs[name] = {
                "detail": get(f"/objects/{key}{query}"),
                "measures": get(f"/objects/{key}/measures{query}"),
            }
    return out


def _review(get: Get) -> dict[str, Any]:
    first, items = _pages(get, "/review/objects/settled")
    return {
        "page": get("/review"),
        "filter models": get("/vocab/filter-models"),
        "settled": {**first, "items": items},
    }


def export(db: Path) -> dict[str, Any]:
    """On a copy: the app writes on open (catalogue, WAL) and the archive stays as built."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / db.name
        for suffix in ("", "-wal", "-shm"):
            if Path(f"{db}{suffix}").exists():
                shutil.copy(f"{db}{suffix}", f"{copy}{suffix}")
        os.environ["ASTROLOG_DATA_DIR"] = str(Path(tmp) / "dati")
        get = _getter(_client(copy))
        pages = {
            "Notti": _nights(get),
            "Archivio e Oggetti": _archive(get),
            "Attrezzatura": get("/gear"),
            "Da confermare": _review(get),
        }
    return without_volatile(pages)


def without_volatile(node: Any) -> Any:
    """Numeric ids and the clock's fields out: what is left is what the pages say."""
    if isinstance(node, dict):
        return {
            k: without_volatile(v)
            for k, v in node.items()
            if k != "id" and not k.endswith(ID_SUFFIXES) and k not in NOW_FIELDS
        }
    if isinstance(node, list):
        return [without_volatile(v) for v in node]
    return node


def differences(a: Any, b: Any, path: str = "") -> Iterator[str]:
    """Every leaf that differs, with its path; a missing key or item is a difference too."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(a.keys() | b.keys()):
            here = f"{path}/{k}"
            if k not in a:
                yield f"{here}: only in B"
            elif k not in b:
                yield f"{here}: only in A"
            else:
                yield from differences(a[k], b[k], here)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{path}: {len(a)} items in A, {len(b)} in B"
        for i, (x, y) in enumerate(zip(a, b, strict=False)):
            yield from differences(x, y, f"{path}[{i}]")
    elif a != b:
        yield f"{path}: {json.dumps(a, ensure_ascii=False)} -> {json.dumps(b, ensure_ascii=False)}"


def compare(a: Path, b: Path) -> int:
    found = list(
        differences(
            json.loads(a.read_text(encoding="utf-8")), json.loads(b.read_text(encoding="utf-8"))
        )
    )
    for line in found:
        sys.stdout.write(line + "\n")
    sys.stderr.write(f"{len(found)} differences\n")
    return 1 if found else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="The pages' API answers of two databases")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("costruisci")
    b.add_argument("folder", type=Path)
    b.add_argument("db", type=Path)
    b.add_argument("--backend")
    b.add_argument("--sito", nargs=3, type=float, metavar=("LAT", "LON", "QUOTA_M"))
    e = sub.add_parser("esporta")
    e.add_argument("db", type=Path)
    e.add_argument("out", type=Path)
    e.add_argument("--backend")
    c = sub.add_parser("confronta")
    c.add_argument("a", type=Path)
    c.add_argument("b", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "confronta":
        # Greek filter names break a cp1252 pipe on Windows mid-list.
        sys.stdout.reconfigure(encoding="utf-8")
        return compare(args.a, args.b)
    _use_backend(args.backend)
    if args.cmd == "costruisci":
        build(args.folder.resolve(), args.db.resolve(), args.sito)
        return 0
    pages = export(args.db.resolve())
    args.out.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
