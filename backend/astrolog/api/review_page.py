"""Each section arrives ready for the screen, because the frontend only formats. The sky candidates
are written by identify, since the catalog cone is costly; the rest is composed here."""

import sqlite3
from typing import Final

from ..db.row import Row
from ..place import by_distance, distance_km
from ..spine import coordinates as places
from ..spine import declarations as decl
from ..spine import gear, unnamed
from ..spine import object_answer as risposta
from ..spine import objects as obj
from ..spine import rigs as corredi
from ..spine.group import SITE_UNCLEAR
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
    righe = conn.execute("SELECT id, name, passband, is_none FROM filters ORDER BY name")
    return [
        FilterCandidate(id=r["id"], name=r["name"], passband=r["passband"])
        for r in righe
        if gear.filter_target(r)
    ]


def optics_choices(conn: sqlite3.Connection) -> list[str]:
    """A name that is not here can be written too, and the piece comes into being."""
    righe = conn.execute(
        "SELECT name FROM instruments WHERE kind = 'optics' ORDER BY name COLLATE NOCASE"
    )
    return [r["name"] for r in righe]


# copies included: the dropdown asks who is used, not the hours
USED_RIGS = "SELECT rig_id, COUNT(*) AS n FROM frames WHERE rig_id IS NOT NULL GROUP BY rig_id"


def rig_choices(conn: sqlite3.Connection) -> list[RigChoice]:
    """A rig without a camera does not answer the question; one with no frame left is the residue
    of an answer that moved them. One home for the dropdown and the writer, like the filters."""
    usati = {r["rig_id"]: r["n"] for r in conn.execute(USED_RIGS)}
    nomi = corredi.rig_names(conn)
    righe = [
        (key, r) for key, r in corredi.rigs_with_keys(conn) if r["camera"] and r["id"] in usati
    ]
    righe.sort(key=lambda kr: (-usati[kr[1]["id"]], kr[1]["id"]))
    return [
        RigChoice(
            id=r["id"],
            name=nomi.get(key),
            optics=r["optics"],
            camera=r["camera"],
            focal_mm=r["focal_mm"],
        )
        for key, r in righe
    ]


def keys_with_candidates(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT DISTINCT object_key FROM object_candidates")}


def object_still_open(row: Row, with_candidates: set[str]) -> bool:
    """A doubt AND the candidates the page shows: without a catalog, or before ASTAP, a doubt has
    nothing to click, and the count would never clear."""
    return row["identity_confidence"] == DOUBT and obj.stable_key(row) in with_candidates


def unclear_coordinates(conn: sqlite3.Connection) -> list[UnclearCoordinates]:
    """The nearest declared site first, almost always the right answer. Distances are recomputed on
    read: three multiplications, while a stored state would go stale at the first new site."""
    posti = places.unclear_coordinates(conn, SITE_UNCLEAR)
    if not posti:
        return []
    luoghi = conn.execute("SELECT id, name, latitude, longitude, is_default FROM sites").fetchall()
    casa = next((s for s in luoghi if s["is_default"]), None)
    out: list[UnclearCoordinates] = []
    for posto in posti:
        # sorted on the true distance before building the models: `SiteCandidate` rounds it, and
        # rounded ones would tie two sites under a hundred metres apart
        vicini = [
            SiteCandidate(id=s["id"], name=s["name"], distance_km=quanto)
            for quanto, s in by_distance(posto["latitude"], posto["longitude"], luoghi)
        ]
        out.append(
            UnclearCoordinates(
                **posto,
                # without a home site there is no distance: zero would say "you are home"
                distance_km=distance_km(
                    posto["latitude"], posto["longitude"], casa["latitude"], casa["longitude"]
                )
                if casa
                else None,
                candidates=vicini,
            )
        )
    out.sort(key=lambda n: -n.frames)
    return out


NONE_ANSWER = ObjectAnswer(kind="none", value=None, name=None)


def asks(card: ObjectCard) -> bool:
    """Counts among the things to confirm: no answer yet, and a found object never seen."""
    return card.answer is None and (card.group is not None or not card.confirmed)


def objects(conn: sqlite3.Connection) -> tuple[list[ObjectCard], list[ObjectCard]]:
    """`(open, settled)`: open asks, is new, has something to click or an answer; questions and
    doubts first, so the work shows. Settled: found objects seen, with nothing to click."""
    out = _found_cards(conn) + _group_cards(conn)
    out.sort(key=lambda c: (not asks(c), c.confidence != DOUBT, -c.frames, c.name or c.key))
    aperti: list[ObjectCard] = []
    certi: list[ObjectCard] = []
    for c in out:
        aperto = c.group or c.answer or not c.confirmed or c.candidates
        (aperti if aperto else certi).append(c)
    return aperti, certi


def _found_cards(conn: sqlite3.Connection) -> list[ObjectCard]:
    """The archive's objects, joined by their key with the frames put out under it; then the keys
    whose frames are all out, which have no object row any more."""
    confermati = decl.confirmed_keys(conn, "object")
    fuori = risposta.out_of_archive(conn)
    collegati_fuori = risposta.linked_out(conn)
    candidati = _sky_candidates(conn)
    out: list[ObjectCard] = []
    for row in obj.listing(conn):
        chiave = obj.stable_key(row)
        extra = fuori.pop(chiave, {"frames": 0, "integration_s": 0.0, "untimed": 0})
        # every frame answered "not an object", the ones still waiting for `identify` included
        tutti_fuori = row["frames"] and collegati_fuori.get(row["id"], 0) == row["frames"]
        out.append(
            ObjectCard(
                key=OBJECT_KEY + chiave,
                id=row["id"],
                name=obj.display_name(row),
                slug=row["catalog_slug"],
                method=row["identity_method"],
                confidence=row["identity_confidence"],
                group=None,
                frames=row["frames"] + extra["frames"],
                integration_s=row["integration_s"] + extra["integration_s"],
                untimed=row["untimed"] + extra["untimed"],
                confirmed=chiave in confermati,
                candidates=candidati.get(chiave, []),
                answer=NONE_ANSWER if tutti_fuori else None,
            )
        )
    for chiave, conti in fuori.items():
        out.append(
            ObjectCard(
                key=OBJECT_KEY + chiave,
                id=None,
                name=conti["name"] or chiave,
                slug=chiave if conti["name"] else None,
                method=None,
                confidence=None,
                group=None,
                frames=conti["frames"],
                integration_s=conti["integration_s"],
                untimed=conti["untimed"],
                confirmed=chiave in confermati,
                candidates=candidati.get(chiave, []),
                answer=NONE_ANSWER,
            )
        )
    return out


def _group_cards(conn: sqlite3.Connection) -> list[ObjectCard]:
    """Frames with no name and no sky: the sky has nothing to click there."""
    return [
        ObjectCard(
            key=FRAMES_KEY + g["key"],
            id=None,
            name=None,
            slug=None,
            method=None,
            confidence=None,
            group=UnnamedGroup(**g),
            frames=g["frames"],
            integration_s=g["integration_s"],
            untimed=g["untimed"],
            confirmed=False,
            candidates=[],
            answer=None if g["answer"] is None else ObjectAnswer(**g["answer"]),
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
