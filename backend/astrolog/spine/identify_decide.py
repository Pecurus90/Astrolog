"""Which object a frame is (one of `Branch`), by which method and confidence.
Pure: the caller did the lookups; `user` is never written here."""

from dataclasses import dataclass
from enum import StrEnum

from .. import units
from ..catalog import NamedEntry, NearEntry
from ..vocab.moving import is_moving_designation
from . import identify_score as score
from .identify_score import Candidate


# The two closed vocabularies of `objects`, also in the schema CHECK.
class IdentityMethod(StrEnum):
    COORD_CONFIRMED = "coord_confirmed"
    COORD_REVIEW = "coord_review"
    EXACT_NAME = "exact_name"
    HISTORIC_NAME = "historic_name"
    USER = "user"


class IdentityConfidence(StrEnum):
    CERTAIN = "certain"
    HIGH = "high"
    LOW = "low"
    USER = "user"


class Branch(StrEnum):
    MOVING = "moving"
    NAME_AND_SKY_AGREE = "name_and_sky_agree"
    SKY_DISAGREES = "sky_disagrees"
    SKY_ONLY = "sky_only"
    SKY_AMBIGUOUS = "sky_ambiguous"
    NAME_ONLY = "name_only"
    FREE_NAME_ONLY = "free_name_only"
    NOTHING = "nothing"


class IdentifyReason(StrEnum):
    # No name, and no sky or an empty cone: not a fault, just nothing to deduce from.
    NO_NAME_NO_SKY = "no_name_no_sky"
    # A frame the user has said is "not an object" (a test shot, a focus run).
    NOT_AN_OBJECT = "not_an_object"


@dataclass(frozen=True, slots=True)
class Decision:
    """A catalog `slug` or a free `name`, never both; `nothing` carries neither."""

    branch: Branch
    slug: str | None = None
    name: str | None = None
    method: IdentityMethod | None = None
    confidence: IdentityConfidence | None = None
    review: bool = False


# Confidence ranking, from the best; `user` is absent, it never competes.
_RANK: dict[str | None, int] = {
    IdentityConfidence.CERTAIN: 0,
    IdentityConfidence.HIGH: 1,
    IdentityConfidence.LOW: 2,
}

# The only confidence that is a QUESTION: `high` is a way of knowing, not a doubt.
DOUBT = IdentityConfidence.LOW


def confidence_after(current: str | None, new: str | None) -> str | None:
    """`low` is absorbing (a doubt persists until answered); otherwise the best of the two."""
    if current is None:
        return new
    if DOUBT in (current, new):
        return DOUBT
    return min((current, new), key=lambda c: _RANK.get(c, len(_RANK)))


def decide(
    *,
    raw_name: str | None,
    hit: NamedEntry | None,
    cands: list[Candidate],
    fov_radius_deg: float | None,
) -> Decision:
    """`hit` is the catalog entry matching `raw_name`, if any; `cands` come best first."""
    name = (raw_name or "").strip()

    if is_moving_designation(name):
        # A comet moves: the cone would confidently return the fixed object behind it.
        return Decision(
            Branch.MOVING,
            name=name,
            method=IdentityMethod.EXACT_NAME,
            confidence=IdentityConfidence.HIGH,
        )
    if cands:
        return _from_the_sky(hit, cands, fov_radius_deg)
    if hit:
        method = IdentityMethod.EXACT_NAME if hit.is_primary else IdentityMethod.HISTORIC_NAME
        return Decision(
            Branch.NAME_ONLY, slug=hit.slug, method=method, confidence=IdentityConfidence.HIGH
        )
    if name:
        return Decision(
            Branch.FREE_NAME_ONLY,
            name=name,
            method=IdentityMethod.EXACT_NAME,
            confidence=IdentityConfidence.LOW,
            review=True,
        )
    return Decision(Branch.NOTHING)


def _from_the_sky(
    hit: NamedEntry | None, cands: list[Candidate], fov_radius_deg: float | None
) -> Decision:
    named = next((c for c in cands if c.slug == hit.slug), None) if hit else None
    if named:
        return Decision(
            Branch.NAME_AND_SKY_AGREE,
            slug=named.slug,
            method=IdentityMethod.COORD_CONFIRMED,
            confidence=IdentityConfidence.CERTAIN,
        )
    if hit:
        # Stays linked as a hypothesis until the user answers the question.
        return Decision(
            Branch.SKY_DISAGREES,
            slug=hit.slug,
            method=IdentityMethod.COORD_REVIEW,
            confidence=IdentityConfidence.LOW,
            review=True,
        )

    best = cands[0]
    second = cands[1] if len(cands) > 1 else None
    if second and score.is_ambiguous(
        best, second, separation_deg=_between(best, second), fov_radius_deg=fov_radius_deg
    ):
        return Decision(
            Branch.SKY_AMBIGUOUS,
            slug=best.slug,
            method=IdentityMethod.COORD_REVIEW,
            confidence=IdentityConfidence.LOW,
            review=True,
        )
    return Decision(
        Branch.SKY_ONLY,
        slug=best.slug,
        method=IdentityMethod.COORD_CONFIRMED,
        confidence=IdentityConfidence.CERTAIN,
    )


def _between(first: NearEntry, second: NearEntry) -> float:
    """True angular distance, not the difference of offsets from the center, which can cancel."""
    return units.angular_separation_deg(first.ra_deg, first.dec_deg, second.ra_deg, second.dec_deg)
