"""The "To confirm" page: what the app cannot settle alone."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_page import Page
from .models_review_groups import (
    MosaicCandidate,
    OpticslessRig,
    RiglessGroup,
    TypelessFolder,
    UnclearCoordinates,
    UnfilteredCamera,
    UnnamedGroup,
)

InstrumentKind = Literal[
    "optics", "camera", "mount", "reducer", "filter_wheel", "guide_scope", "guide_camera",
    "focuser",
]  # fmt: skip
# Only physical bands can be declared, never a derived label: no filter lets "duo" through. A test
# keeps these words equal to `vocab.filters.BANDS`, since a `Literal` wants constants.
Band = Literal["L", "R", "G", "B", "HA", "HB", "OIII", "SII"]
# The words of the schema CHECK and of `spine.declarations`, kept glued by a test.
CameraType = Literal["mono", "color"]
# The fields a card can ask for; which ones per kind is `instrument_answer.CARD`. A test keeps this
# list glued to it and to the fields the answer accepts.
CardField = Literal[
    "brand", "model", "camera_type", "pixel_size_um", "aperture_mm", "focal_mm", "reducer_factor",
    "weight_kg", "payload_kg", "slots", "notes",
]  # fmt: skip
# A test keeps these glued to `spine.identify_decide`, which is in turn guarded against the schema
# CHECK.
IdentityMethod = Literal["coord_confirmed", "coord_review", "exact_name", "historic_name", "user"]
IdentityConfidence = Literal["certain", "high", "low", "user"]


class BandOut(BaseModel):
    band: Band
    width_nm: float | None = Field(
        description="Optional: a light-pollution filter does not declare it."
    )


class FilterModelOut(BaseModel):
    """A filter ON THE MARKET, as it reads in the drop-down when a new filter is declared.

    It is not a filter of the archive: it is an entry of the vocabulary the app carries inside. The
    **aliases** stay out -- they serve to recognise a spelling in the header, and on screen they
    would be noise. When one is picked from here, `catalog_id` remembers which entry it was."""

    id: str
    brand: str
    name: str
    passband: str


class FilterModelList(BaseModel):
    items: list[FilterModelOut]


class FilterCandidate(BaseModel):
    """One of your filters, among which an answer is chosen: one with a known band."""

    id: int
    name: str
    passband: str


class FilterOut(BaseModel):
    id: int
    name: str
    brand: str | None
    model: str | None
    catalog_id: str | None
    passband: str
    is_none: bool
    bands: list[BandOut]
    frames: int


class RigChoice(BaseModel):
    """One of your rigs, among which one chooses which camera took some frames: only those with a
    camera, because one without does not answer that question."""

    id: int
    name: str | None = Field(
        description="The one you gave it; without it, the page shows the two pieces."
    )
    optics: str | None
    camera: str
    focal_mm: float | None


class LookalikeOut(BaseModel):
    """Two spellings that look very much like the same camera: "are they the same piece?". Yes
    merges `id` into `into_id`, no stops proposing it."""

    id: int
    name: str
    frames: int
    into_id: int
    into_name: str
    into_frames: int


class ObjectCandidate(BaseModel):
    """An entry the sky found in the field of this object: it is what one clicks to answer. The
    identification writes it, and the page reads it."""

    slug: str
    name: str
    common_name: str | None
    in_frame: bool | None = Field(
        description="None when the sky carries no sides or rotation: it was called a circle."
    )


class ObjectOut(BaseModel):
    """An object of the archive. `name` is the two steps of the contract already done by the
    backend: the primary name, or the one the catalog gives to the slug."""

    id: int = Field(
        description="The row number: it serves the frontend as a list key, not for answering."
    )
    key: str = Field(description="The stable key one answers with: the catalog slug, or the name.")
    name: str | None
    slug: str | None
    method: IdentityMethod | None
    confidence: IdentityConfidence | None
    frames: int
    integration_s: float = Field(
        description="The sum of the frames' time; on screen it reads in hours."
    )
    untimed: int = Field(
        description="How many of those frames do not tell their time: they are not worth zero, "
        "they are counted here."
    )
    confirmed: bool
    candidates: list[ObjectCandidate] = Field(
        default=[], description="Only on those still to decide."
    )


class SettledObjects(Page[ObjectOut]):
    """The objects already seen, with nothing to choose, in pages: they are not questions, and they
    grow with the archive. They open from the Objects section, and are corrected from there. A doubt
    the sky can say nothing about stays here once seen: there is nothing to click."""


class ReviewSeen(BaseModel):
    """How far the page looked at the objects: the highest row number it really listed. Apply sends
    it back and confirms only up to there.

    Row numbers and not times, because **two rows born in the same instant cannot be ordered**
    (the measurement and the why are in `docs/domini/spina.md`, section Da confermare).

    Zero means "I saw nothing", and it is also the value when the page lists no object: it is not a
    missing limit, it is a limit that lets nothing through. Whoever does not send `seen` at all is
    saying something else -- "confirm what is there now" -- and its home is `ReviewApply`."""

    objects: int = 0


class ReviewOut(BaseModel):
    """The whole page in one response: it is not a paged list, it is the open questions."""

    lookalikes: list[LookalikeOut] = Field(
        description="Two spellings that look like the same camera."
    )
    filters: list[FilterOut]
    rig_choices: list[RigChoice] = Field(
        description="The rigs among which one answers about the frames without a camera."
    )
    objects: list[ObjectOut] = Field(
        description="Those to decide and the new ones; the doubts on top."
    )
    settled_objects: int = Field(
        description="How many the others are, already seen: they are read in pages."
    )
    unnamed: list[UnnamedGroup]
    unclear: list[UnclearCoordinates] = Field(
        description="The places the app asks about: empty when it does not ask."
    )
    unfiltered: list[UnfilteredCamera] = Field(
        description="The cameras whose frames do not tell the filter."
    )
    filter_choices: list[FilterCandidate] = Field(
        description="The filters with a known band, among which one answers."
    )
    rigless: list[RiglessGroup] = Field(
        description="The groups of frames that do not tell the camera."
    )
    opticsless: list[OpticslessRig] = Field(
        description="The cameras at one focal length whose frames do not name the optics."
    )
    optics_choices: list[str] = Field(
        description="The optics you own, among which one answers that question."
    )
    typeless: list[TypelessFolder] = Field(
        description="The folders whose frames do not tell what file they are."
    )
    mosaics: list[MosaicCandidate] = Field(description="The regions taken in side-by-side panels.")
    to_confirm: int
    seen: ReviewSeen = Field(
        description="How far this page looked: Apply sends it back and confirms only what was "
        "listed, never what arrived in the meantime."
    )
