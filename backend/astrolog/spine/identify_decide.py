"""Which object a frame is (one of `BRANCHES`), by which method and confidence.
Pure: the caller did the lookups; `user` is never written here."""

from typing import Any

from .. import units
from ..vocab.moving import is_moving_designation
from . import identify_score as score

# The two closed vocabularies of `objects`, also in the schema CHECK.
IDENTITY_METHODS = ("coord_confirmed", "coord_review", "exact_name", "historic_name", "user")
IDENTITY_CONFIDENCES = ("certain", "high", "low", "user")

BRANCHES = (
    "moving",
    "name_and_sky_agree",
    "sky_disagrees",
    "sky_only",
    "sky_ambiguous",
    "name_only",
    "free_name_only",
    "nothing",
)

# No name, and no sky or an empty cone: not a fault, just nothing to deduce from.
NO_NAME_NO_SKY = "no_name_no_sky"
# A frame the user has said is "not an object" (a test shot, a focus run).
NOT_AN_OBJECT = "not_an_object"


# Confidence ranking, from the best; `user` is absent, it never competes.
_RANK = {"certain": 0, "high": 1, "low": 2}

# The only confidence that is a QUESTION: `high` is a way of knowing, not a doubt.
DOUBT = "low"


def confidence_after(current: str | None, new: str) -> str:
    """`low` is absorbing (a doubt persists until answered); otherwise the best of the two."""
    if current is None:
        return new
    if DOUBT in (current, new):
        return DOUBT
    return min((current, new), key=lambda c: _RANK.get(c, len(_RANK)))


def _decision(  # noqa: PLR0913
    branch: str,
    *,
    slug: str | None = None,
    name: str | None = None,
    method: str | None = None,
    confidence: str | None = None,
    review: bool = False,
) -> dict[str, Any]:
    return {
        "branch": branch,
        "slug": slug,
        "name": name,
        "method": method,
        "confidence": confidence,
        "review": review,
    }


def decide(
    *,
    raw_name: str | None,
    hit: dict[str, Any] | None,
    cands: list[dict[str, Any]],
    fov_radius_deg: float | None,
) -> dict[str, Any]:
    """`hit` is the catalog entry matching `raw_name`, if any; `cands` come best first."""
    name = (raw_name or "").strip()

    if is_moving_designation(name):
        # A comet moves: the cone would confidently return the fixed object behind it.
        return _decision("moving", name=name, method="exact_name", confidence="high")
    if cands:
        return _from_the_sky(hit, cands, fov_radius_deg)
    if hit:
        method = "exact_name" if hit["is_primary"] else "historic_name"
        return _decision("name_only", slug=hit["slug"], method=method, confidence="high")
    if name:
        return _decision(
            "free_name_only", name=name, method="exact_name", confidence="low", review=True
        )
    return _decision("nothing")


def _from_the_sky(
    hit: dict[str, Any] | None, cands: list[dict[str, Any]], fov_radius_deg: float | None
) -> dict[str, Any]:
    named = next((c for c in cands if c["slug"] == hit["slug"]), None) if hit else None
    if named:
        return _decision(
            "name_and_sky_agree",
            slug=named["slug"],
            method="coord_confirmed",
            confidence="certain",
        )
    if hit:
        # Stays linked as a hypothesis until the user answers the question.
        return _decision(
            "sky_disagrees", slug=hit["slug"], method="coord_review", confidence="low", review=True
        )

    best = cands[0]
    second = cands[1] if len(cands) > 1 else None
    if second and score.is_ambiguous(
        best, second, separation_deg=_between(best, second), fov_radius_deg=fov_radius_deg
    ):
        return _decision(
            "sky_ambiguous",
            slug=best["slug"],
            method="coord_review",
            confidence="low",
            review=True,
        )
    return _decision("sky_only", slug=best["slug"], method="coord_confirmed", confidence="certain")


def _between(first: dict[str, Any], second: dict[str, Any]) -> float:
    """True angular distance, not the difference of offsets from the center, which can cancel."""
    return units.angular_separation_deg(
        first["ra_deg"], first["dec_deg"], second["ra_deg"], second["dec_deg"]
    )
