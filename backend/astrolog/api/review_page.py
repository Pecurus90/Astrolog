"""Each section arrives ready for the screen, because the frontend only formats. The sky candidates
are written by identify, since the catalog cone is costly; the rest is composed here."""

import sqlite3
from dataclasses import asdict
from typing import Final

from ..place import by_distance, distance_km
from ..spine import coordinates as places
from ..spine import gear, object_answer, rigs, unnamed
from ..spine import objects as obj
from ..spine.group import GroupReason
from ..spine.identify_decide import DOUBT
from .models_review import (
    FilterCandidate,
    ObjectAnswer,
    ObjectCandidate,
    ObjectCard,
    RigChoice,
)
from .models_review_groups import SiteCandidate, UnclearCoordinates, UnnamedGroup

# The head of a card's key says which kind of group it is: one answer, two writers.
OBJECT_KEY: Final = "object:"
FRAMES_KEY: Final = "frames:"


def filter_choices(conn: sqlite3.Connection) -> list[FilterCandidate]:
    """Filters with a known band, minus the "no filter" row, which is another answer. One home for
    the dropdowns and for the writer: Apply does not accept a filter the dropdown does not offer."""
    rows = conn.execute("SELECT id, name, passband, is_none FROM filters ORDER BY name")
    return [
        FilterCandidate(id=r["id"], name=r["name"], passband=r["passband"])
        for r in rows
        if gear.filter_target(r)
    ]


def optics_choices(conn: sqlite3.Connection) -> list[str]:
    """A name that is not here can be written too, and the piece comes into being."""
    rows = conn.execute(
        "SELECT name FROM instruments WHERE kind = 'optics' ORDER BY name COLLATE NOCASE"
    )
    return [r["name"] for r in rows]


# copies included: the dropdown asks who is used, not the hours
USED_RIGS = "SELECT rig_id, COUNT(*) AS n FROM frames WHERE rig_id IS NOT NULL GROUP BY rig_id"


def rig_choices(conn: sqlite3.Connection) -> list[RigChoice]:
    """A rig without a camera does not answer the question; one with no frame left is the residue
    of an answer that moved them. One home for the dropdown and the writer, like the filters."""
    used = {r["rig_id"]: r["n"] for r in conn.execute(USED_RIGS)}
    names = rigs.rig_names(conn)
    rows = [(key, r) for key, r in rigs.rigs_with_keys(conn) if r["camera"] and r["id"] in used]
    rows.sort(key=lambda kr: (-used[kr[1]["id"]], kr[1]["id"]))
    return [
        RigChoice(
            id=r["id"],
            name=names.get(key),
            optics=r["optics"],
            camera=r["camera"],
            focal_mm=r["focal_mm"],
        )
        for key, r in rows
    ]


def unclear_coordinates(conn: sqlite3.Connection) -> list[UnclearCoordinates]:
    """The nearest declared site first, almost always the right answer. Distances are recomputed on
    read: three multiplications, while a stored state would go stale at the first new site."""
    spots = places.unclear_coordinates(conn, GroupReason.SITE_UNCLEAR)
    if not spots:
        return []
    sites = conn.execute("SELECT id, name, latitude, longitude, is_default FROM sites").fetchall()
    home = next((s for s in sites if s["is_default"]), None)
    out: list[UnclearCoordinates] = []
    for spot in spots:
        # sorted before building the models, which round the distance (`place.by_distance`)
        nearest = [
            SiteCandidate(id=s["id"], name=s["name"], distance_km=km)
            for km, s in by_distance(spot["latitude"], spot["longitude"], sites)
        ]
        out.append(
            UnclearCoordinates(
                **spot,
                # without a home site there is no distance: zero would say "you are home"
                distance_km=distance_km(
                    spot["latitude"], spot["longitude"], home["latitude"], home["longitude"]
                )
                if home
                else None,
                candidates=nearest,
            )
        )
    out.sort(key=lambda n: -n.frames)
    return out


NONE_ANSWER = ObjectAnswer(kind="none", value=None, name=None)


def asks(card: ObjectCard) -> bool:
    """No answer yet, on a group or a doubt: what the sky or the catalog settled is not asked, a
    catalog name without a sky included (ADR 0014, S4)."""
    return card.answer is None and (card.group is not None or card.confidence == DOUBT)


def objects(conn: sqlite3.Connection) -> tuple[list[ObjectCard], list[ObjectCard]]:
    """`(open, settled)`: open asks, has something to click or an answer; questions first, so the
    work shows. Settled: found objects the app knows, with nothing to click."""
    out = _found_cards(conn) + _group_cards(conn)
    out.sort(key=lambda c: (not asks(c), c.confidence != DOUBT, -c.frames, c.name or c.key))
    open_cards: list[ObjectCard] = []
    settled: list[ObjectCard] = []
    for c in out:
        (open_cards if asks(c) or c.answer or c.candidates else settled).append(c)
    return open_cards, settled


def _found_cards(conn: sqlite3.Connection) -> list[ObjectCard]:
    """The archive's objects, joined by their key with the frames put out under it; then the keys
    whose frames are all out, which have no object row any more."""
    put_out = object_answer.out_of_archive(conn)
    linked_out = object_answer.linked_out(conn)
    candidates = _sky_candidates(conn)
    out: list[ObjectCard] = []
    for row in obj.listing(conn):
        object_key = obj.stable_key(row)
        extra = put_out.pop(object_key, None)
        # every frame answered "not an object", the ones still waiting for `identify` included
        all_out = row["frames"] and linked_out.get(row["id"], 0) == row["frames"]
        out.append(
            ObjectCard(
                key=OBJECT_KEY + object_key,
                name=obj.display_name(row),
                slug=row["catalog_slug"],
                method=row["identity_method"],
                confidence=row["identity_confidence"],
                group=None,
                frames=row["frames"] + (extra.frames if extra else 0),
                integration_s=row["integration_s"] + (extra.integration_s if extra else 0.0),
                untimed=row["untimed"] + (extra.untimed if extra else 0),
                candidates=candidates.get(object_key, []),
                answer=NONE_ANSWER if all_out else None,
            )
        )
    for object_key, totals in put_out.items():
        out.append(
            ObjectCard(
                key=OBJECT_KEY + object_key,
                name=totals.name or object_key,
                slug=object_key if totals.name else None,
                method=None,
                confidence=None,
                group=None,
                frames=totals.frames,
                integration_s=totals.integration_s,
                untimed=totals.untimed,
                candidates=candidates.get(object_key, []),
                answer=NONE_ANSWER,
            )
        )
    return out


def _group_cards(conn: sqlite3.Connection) -> list[ObjectCard]:
    """Frames with no name and no sky: the sky has nothing to click there."""
    return [
        ObjectCard(
            key=FRAMES_KEY + g.key,
            name=None,
            slug=None,
            method=None,
            confidence=None,
            group=UnnamedGroup(**asdict(g)),
            frames=g.frames,
            integration_s=g.integration_s,
            untimed=g.untimed,
            candidates=[],
            answer=None if g.answer is None else ObjectAnswer(**asdict(g.answer)),
        )
        for g in unnamed.by_group(conn)
    ]


def _sky_candidates(conn: sqlite3.Connection) -> dict[str, list[ObjectCandidate]]:
    """What one clicks to answer, and for "the sky says something else" the answer to why."""
    out: dict[str, list[ObjectCandidate]] = {}
    for r in conn.execute(
        "SELECT object_key, slug, name, common_name, in_frame FROM object_candidates"
        " ORDER BY object_key, rank"
    ):
        out.setdefault(r["object_key"], []).append(
            ObjectCandidate(
                slug=r["slug"],
                name=r["name"],
                common_name=r["common_name"],
                in_frame=None if r["in_frame"] is None else bool(r["in_frame"]),
            )
        )
    return out
