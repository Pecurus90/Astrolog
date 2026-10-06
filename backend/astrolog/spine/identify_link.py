"""The archive object a decision links to, existing or new. Its primary name is the first FREE
one: the catalog's names for an object may already belong to another."""

import logging
import sqlite3
from typing import Any, cast

from ..catalog import CatalogEntry, NamedEntry, lookup
from . import identify_decide as rule
from . import identify_store as store
from .identify_decide import Decision, IdentityConfidence, IdentityMethod
from .identify_score import Candidate

log = logging.getLogger(__name__)


def entry_for(
    conn: sqlite3.Connection,
    slug: str | None,
    hit: NamedEntry | None,
    cands: list[Candidate],
) -> CatalogEntry | None:
    """The catalog entry the decision picked, taken from what is already in hand."""
    if slug is None:
        return None
    if hit and hit.slug == slug:
        return hit
    candidate = next((c for c in cands if c.slug == slug), None)
    # Neither the name nor a candidate: only a user's declaration picks that, so fetch it.
    return candidate or lookup.by_slug(conn, slug)


def hang(  # noqa: PLR0913
    conn: sqlite3.Connection,
    decision: Decision,
    raw: str | None,
    entry: CatalogEntry | None,
    now: str,
    counts: dict[str, int],
) -> tuple[int, bool]:
    """`(object id, locked)`, where the lock is the user's own word."""
    slug = decision.slug
    if slug:
        existing = store.object_by_slug(conn, slug)
    else:
        existing = store.object_by_name(conn, decision.name)
    locked = decision.method == IdentityMethod.USER or (
        existing is not None and existing["identity_method"] == IdentityMethod.USER
    )

    if existing is None:
        object_id = store.create_object(
            conn,
            slug=slug,
            method=decision.method,
            confidence=decision.confidence,
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
    return object_id, locked


def _name_it(
    conn: sqlite3.Connection,
    object_id: int,
    decision: Decision,
    entry: CatalogEntry | None,
) -> int:
    """Names a newborn object; returns how many of its names another object already owns."""
    if entry is None:
        # A corrected name is the user's word, not a header label: its origin says so.
        source = "user" if decision.method == IdentityMethod.USER else "raw"
        # `decide` and `_towards` give a decision without an entry its free name.
        names = [(cast(str, decision.name), source)]
    else:
        names = [(entry.name, "catalog")]
        if entry.common_name:
            names.append((entry.common_name, "catalog"))

    primary, refused = True, 0
    for name, source in names:
        if store.add_name(conn, object_id, name, origin=source, is_primary=int(primary)):
            primary = False
        else:
            refused += 1
    if primary:
        # Tolerable only because the object has `catalog_slug`: an out-of-catalog
        # object never reaches here without its own name.
        log.warning("identify: oggetto senza nomi propri", extra={"obj": object_id})
    return refused


def _restate(
    conn: sqlite3.Connection, existing: dict[str, Any], decision: Decision, now: str
) -> None:
    """Confidence when another frame links: an existing `user` lock is never touched;
    otherwise a `user` carried by the NEW frame is always written."""
    if existing["identity_method"] == IdentityMethod.USER:
        return
    if decision.method == IdentityMethod.USER:
        store.set_identity(
            conn,
            existing["id"],
            method=IdentityMethod.USER,
            confidence=IdentityConfidence.USER,
            now=now,
        )
        return
    kept = rule.confidence_after(existing["identity_confidence"], decision.confidence)
    if kept == existing["identity_confidence"]:
        return
    store.set_identity(conn, existing["id"], method=decision.method, confidence=kept, now=now)
