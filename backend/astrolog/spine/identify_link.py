"""The archive object a decision links to, existing or new. Its primary name is the first FREE
one: the catalog's names for an object may already belong to another."""

import logging
import sqlite3
from typing import Any

from ..catalog import lookup
from . import identify_decide as rule
from . import identify_store as store

log = logging.getLogger(__name__)


def entry_for(
    conn: sqlite3.Connection,
    slug: str | None,
    hit: dict[str, Any] | None,
    cands: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """The catalog entry the decision picked, taken from what is already in hand."""
    if slug is None:
        return None
    if hit and hit["slug"] == slug:
        return hit
    fra_i_candidati = next((c for c in cands if c["slug"] == slug), None)
    # Neither the name nor a candidate: only a user's declaration picks that, so fetch it.
    return fra_i_candidati or lookup.by_slug(conn, slug)


def hang(  # noqa: PLR0913
    conn: sqlite3.Connection,
    decision: dict[str, Any],
    raw: str | None,
    entry: dict[str, Any] | None,
    now: str,
    counts: dict[str, int],
) -> tuple[int, bool]:
    """`(object id, locked)`, where the lock is the user's own word."""
    slug = decision["slug"]
    if slug:
        existing = store.object_by_slug(conn, slug)
    else:
        existing = store.object_by_name(conn, decision["name"])
    lucchettato = decision["method"] == "user" or (
        existing is not None and existing["identity_method"] == "user"
    )

    if existing is None:
        object_id = store.create_object(
            conn,
            slug=slug,
            method=decision["method"],
            confidence=decision["confidence"],
            now=now,
        )
        counts["name_taken"] += _name_it(conn, object_id, decision, entry)
        counts["new_objects"] += 1
    else:
        object_id = existing["id"]
        _restate(conn, existing, decision, now)

    if raw and not store.add_name(conn, object_id, raw, origin="raw"):
        counts["name_taken"] += 1
        log.info("identify: nome gia' di un altro oggetto", extra={"nome": raw, "obj": object_id})
    return object_id, lucchettato


def _name_it(
    conn: sqlite3.Connection,
    object_id: int,
    decision: dict[str, Any],
    entry: dict[str, Any] | None,
) -> int:
    """Names a newborn object; returns how many of its names another object already owns."""
    if entry is None:
        # A corrected name is the user's word, not a header label: its origin says so.
        origine = "user" if decision["method"] == "user" else "raw"
        candidati = [(decision["name"], origine)]
    else:
        candidati = [(entry["name"], "catalog")]
        if entry.get("common_name"):
            candidati.append((entry["common_name"], "catalog"))

    primario, rifiutati = True, 0
    for nome, origine in candidati:
        if store.add_name(conn, object_id, nome, origin=origine, is_primary=int(primario)):
            primario = False
        else:
            rifiutati += 1
    if primario:
        # Tolerable only because the object has `catalog_slug`: an out-of-catalog
        # object never reaches here without its own name.
        log.warning("identify: oggetto senza nomi propri", extra={"obj": object_id})
    return rifiutati


def _restate(
    conn: sqlite3.Connection, existing: dict[str, Any], decision: dict[str, Any], now: str
) -> None:
    """Confidence when another frame links: an existing `user` lock is never touched;
    otherwise a `user` carried by the NEW frame is always written."""
    if existing["identity_method"] == "user":
        return
    if decision["method"] == "user":
        store.set_identity(conn, existing["id"], method="user", confidence="user", now=now)
        return
    kept = rule.confidence_after(existing["identity_confidence"], decision["confidence"])
    if kept == existing["identity_confidence"]:
        return
    store.set_identity(conn, existing["id"], method=decision["method"], confidence=kept, now=now)
