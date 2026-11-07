"""The Nights' criteria (`docs/domini/notti.md`): the nights that pass, each choice counted with
the others applied. One choice per criterion is enough; all criteria hold."""

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..levels import Verdict
from . import filters_used, rigs
from .archive import NAMED, folded


class Key(StrEnum):
    """In the sheet's order (Notti.dc.html 249)."""

    YEAR = "year"
    SITE = "site"
    SETUP = "setup"
    FILTER = "filter"
    CONSTELLATION = "constellation"
    SKY = "sky"


SKY_UNKNOWN = "unknown"
# frames whose header names no filter: a choice of their own, last (sheet: "nessun filtro")
NO_FILTER = "__no_filter__"
_SKY_ORDER = [Verdict.GO, Verdict.MARGINAL, Verdict.NOGO, SKY_UNKNOWN]

_FRAMED = "f.night_id IS NOT NULL AND f.copy_of IS NULL"
# Constant fragments, hence the `noqa`; the sky's `?` is the history's weather kind.
_FACTS: dict[Key, str] = {
    Key.YEAR: "SELECT n.id, substr(n.night_date, 1, 4) FROM nights n",
    Key.SITE: "SELECT n.id, CAST(n.site_id AS TEXT) FROM nights n",
    Key.SETUP: f"SELECT DISTINCT f.night_id, CAST(f.rig_id AS TEXT) FROM frames f"  # noqa: S608
    f" WHERE {_FRAMED} AND f.rig_id IS NOT NULL",
    Key.FILTER: f"SELECT DISTINCT f.night_id, COALESCE(x.name, '{NO_FILTER}') FROM frames f"  # noqa: S608
    f" LEFT JOIN filters x ON x.id = f.filter_id WHERE {_FRAMED}",
    Key.CONSTELLATION: f"SELECT DISTINCT f.night_id, e.constellation FROM frames f"  # noqa: S608
    " JOIN objects o ON o.id = f.object_id JOIN catalog_entries e ON e.slug = o.catalog_slug"
    f" WHERE {_FRAMED}",
    Key.SKY: "SELECT n.id, COALESCE(json_extract(w.summary_json, '$.verdict'),"  # noqa: S608
    f" '{SKY_UNKNOWN}') FROM nights n LEFT JOIN weather_nights w ON w.site_id = n.site_id"
    " AND w.night_date = n.night_date AND w.kind = ?",
}

_ORDERED = "SELECT id FROM nights ORDER BY night_date DESC, id DESC"
_SEARCHED = (
    "SELECT DISTINCT f.night_id FROM frames f JOIN objects o2 ON o2.id = f.object_id"  # noqa: S608
    f" WHERE {_FRAMED} AND " + NAMED.format(o="o2")
)
_SITES = "SELECT CAST(id AS TEXT), name FROM sites"
_FILTERS = "SELECT x.name, x.passband FROM filters x ORDER BY " + filters_used.order_by("x")  # noqa: S608


@dataclass(frozen=True)
class Chosen:
    """What the page asks: the object's text and the choices per criterion."""

    q: str | None = None
    by: Mapping[Key, Sequence[str]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Selection:
    """The nights that pass, newest first, and the criteria with their counted options."""

    ids: list[int]
    criteria: list[dict[str, Any]]


def _facts(conn: sqlite3.Connection, kind: str) -> dict[Key, dict[int, set[str]]]:
    out: dict[Key, dict[int, set[str]]] = {}
    for key, sql in _FACTS.items():
        rows = conn.execute(sql, (kind,) if key == Key.SKY else ())
        per: dict[int, set[str]] = {}
        for night_id, value in rows:
            per.setdefault(night_id, set()).add(value)
        out[key] = per
    return out


def _searched(conn: sqlite3.Connection, q: str | None) -> set[int] | None:
    pattern = folded(q)
    if pattern is None:
        return None
    return {r[0] for r in conn.execute(_SEARCHED, [pattern] * _SEARCHED.count("LIKE ?"))}


def _labels(conn: sqlite3.Connection) -> dict[Key, dict[str, dict[str, Any]]]:
    """What a value shows besides itself: a site's name, a setup's name and parts, a filter's
    band. The order of the dict is the order of the options where the criterion has one."""
    names = rigs.rig_names(conn)
    setups = {
        str(r["id"]): {"name": names.get(key), "optics": r["optics"], "camera": r["camera"]}
        for key, r in rigs.rigs_with_keys(conn)
    }
    return {
        Key.SITE: {r[0]: {"name": r[1]} for r in conn.execute(_SITES)},
        Key.SETUP: setups,
        Key.FILTER: {r[0]: {"passband": r[1]} for r in conn.execute(_FILTERS)},
    }


def _ordered(key: Key, values: set[str], labels: Mapping[str, dict[str, Any]]) -> list[str]:
    if key == Key.YEAR:
        return sorted(values, reverse=True)
    if key == Key.SKY:
        return [v for v in _SKY_ORDER if v in values] + sorted(values - set(_SKY_ORDER))
    if key == Key.FILTER:
        rest = sorted(values - labels.keys() - {NO_FILTER})
        return [v for v in labels if v in values] + rest + [NO_FILTER] * (NO_FILTER in values)
    if key in (Key.SITE, Key.SETUP):

        def shown(v: str) -> str:
            m = labels.get(v, {})
            return (m.get("name") or m.get("optics") or m.get("camera") or "").casefold()

        # an address may carry a non-number: it sorts last, at zero, never a 500
        return sorted(
            values, key=lambda v: (not v.isdigit(), shown(v), int(v) if v.isdigit() else 0, v)
        )
    return sorted(values, key=str.casefold)


def select(conn: sqlite3.Connection, chosen: Chosen, kind: str) -> Selection:
    """Every night's facts in six queries, counted here: a few hundred nights, a few dozen
    values. A chosen value no night holds stays listed, chosen, at zero."""
    facts = _facts(conn, kind)
    found = _searched(conn, chosen.q)
    wanted = {k: set(v) for k, v in chosen.by.items() if v}
    ordered = [r[0] for r in conn.execute(_ORDERED)]

    def passes(night_id: int, skip: Key | None) -> bool:
        if found is not None and night_id not in found:
            return False
        return all(
            facts[k].get(night_id, set()) & values for k, values in wanted.items() if k != skip
        )

    labels = _labels(conn)
    criteria = []
    for key in Key:
        values = {v for vs in facts[key].values() for v in vs} | wanted.get(key, set())
        open_ids = [i for i in ordered if passes(i, key)]
        options = []
        for value in _ordered(key, values, labels.get(key, {})):
            n = sum(1 for i in open_ids if value in facts[key].get(i, set()))
            meta = labels.get(key, {}).get(value, {})
            options.append(
                {"value": value, "nights": n, "chosen": value in wanted.get(key, set()), **meta}
            )
        criteria.append({"key": key, "options": options})
    return Selection([i for i in ordered if passes(i, None)], criteria)
