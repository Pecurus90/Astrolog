"""Each section arrives ready for the screen, because the frontend only formats. The sky candidates
are written by identify, since the catalog cone is costly; the rest is composed here."""

import sqlite3

from ..db.row import Row
from ..place import by_distance, distance_km
from ..spine import coordinates as places
from ..spine import declarations as decl
from ..spine import gear
from ..spine import objects as obj
from ..spine import rigs as corredi
from ..spine.group import SITE_UNCLEAR
from ..spine.identify_decide import DOUBT
from .models_review import FilterCandidate, ObjectCandidate, ObjectOut, RigChoice
from .models_review_groups import SiteCandidate, UnclearCoordinates


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


def object_still_open(conn: sqlite3.Connection, row: Row) -> bool:
    """A doubt AND the candidates the page shows: without a catalog, or before ASTAP, a doubt has
    nothing to click, and the count would never clear."""
    return row["identity_confidence"] == DOUBT and bool(_sky_candidates(conn, row["id"]))


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


def objects(conn: sqlite3.Connection) -> tuple[list[ObjectOut], list[ObjectOut]]:
    """`(open, settled)`: open are the new ones and those with something to click, doubts first, so
    whoever opens the page sees the work. Candidates are read only for those to decide."""
    confermati = decl.confirmed_keys(conn, "object")
    out: list[ObjectOut] = []
    for row in obj.listing(conn):
        nome = obj.display_name(row)
        chiave = obj.stable_key(row)
        dubbio = row["identity_confidence"] == DOUBT
        out.append(
            ObjectOut(
                id=row["id"],
                key=chiave,
                name=nome,
                slug=row["catalog_slug"],
                method=row["identity_method"],
                confidence=row["identity_confidence"],
                frames=row["frames"],
                integration_s=row["integration_s"],
                untimed=row["untimed"],
                confirmed=chiave in confermati,
                candidates=_sky_candidates(conn, row["id"]) if dubbio else [],
            )
        )
    out.sort(key=lambda o: (o.confidence != DOUBT, -o.frames, o.name or ""))
    aperti: list[ObjectOut] = []
    certi: list[ObjectOut] = []
    for o in out:
        (aperti if not o.confirmed or o.candidates else certi).append(o)
    return aperti, certi


def _sky_candidates(conn: sqlite3.Connection, object_id: int) -> list[ObjectCandidate]:
    """What one clicks to answer, and for "the sky says something else" the answer to why."""
    return [
        ObjectCandidate(
            slug=r["slug"],
            name=r["name"],
            common_name=r["common_name"],
            in_frame=None if r["in_frame"] is None else bool(r["in_frame"]),
        )
        for r in conn.execute(
            "SELECT slug, name, common_name, in_frame FROM object_candidates"
            " WHERE object_id = ? ORDER BY rank",
            (object_id,),
        )
    ]
