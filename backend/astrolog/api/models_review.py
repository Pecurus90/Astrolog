"""The "To confirm" page: what the app cannot settle alone."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_page import Page
from .models_review_groups import (
    GearSignature,
    MosaicCandidate,
    TypelessFolder,
    UnclearCoordinates,
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
    camera, because one without does not answer that part."""

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


class ObjectAnswer(BaseModel):
    """What the user said on a card: a catalog object (`value` is the slug), a written name, or "it
    is not an object" (`value` empty). `name` is how the object shows: the entry's, or the written
    one."""

    kind: Literal["catalog", "name", "none"]
    value: str | None
    name: str | None


class ObjectCard(BaseModel):
    """One card per group of frames, asking what object they are (ADR 0014, S3): the frames
    `identify` put on one object, or -- `group` -- frames the header does not name and the sky says
    nothing about. Same answer for both. `name`, `slug`, `method`, `confidence` are what the app
    found: empty on a `group`, and `method`/`confidence` also on frames put out as "not an object",
    which no longer have an object. Asked: a group or a doubt (`low`), until answered (S4)."""

    key: str = Field(
        description="What one answers with: `object:` and the found object's stable key, or "
        "`frames:` and the group's key."
    )
    name: str | None
    slug: str | None
    method: IdentityMethod | None
    confidence: IdentityConfidence | None
    group: UnnamedGroup | None = Field(
        description="Where and when, for frames with no name and no sky; empty otherwise."
    )
    frames: int
    integration_s: float = Field(
        description="The sum of the frames' time; on screen it reads in hours."
    )
    untimed: int = Field(
        description="How many of those frames do not tell their time: they are not worth zero, "
        "they are counted here."
    )
    candidates: list[ObjectCandidate] = Field(
        description="What the sky found, to click: on doubts and on frames put out; zero is a card "
        "too."
    )
    answer: ObjectAnswer | None = Field(
        description="An answered card stays on the page, so one can change one's mind."
    )


class SettledObjects(Page[ObjectCard]):
    """The objects the app knows, with nothing to choose, in pages: they are not questions, and
    they grow with the archive. They open from the Objects section, and are corrected from there."""


class ReviewOut(BaseModel):
    """The whole page in one response: it is not a paged list, it is the open questions."""

    lookalikes: list[LookalikeOut] = Field(
        description="Two spellings that look like the same camera."
    )
    filters: list[FilterOut]
    rig_choices: list[RigChoice] = Field(
        description="The rigs among which one answers a card that asks the camera."
    )
    objects: list[ObjectCard] = Field(
        description="The object cards to decide and the answered ones; open questions on top."
    )
    settled_objects: int = Field(
        description="How many the others are, which the app knows: they are read in pages."
    )
    unclear: list[UnclearCoordinates] = Field(
        description="The places the app asks about: empty when it does not ask."
    )
    gear: list[GearSignature] = Field(
        description="The header signatures whose frames leave out camera, optics or filter."
    )
    filter_choices: list[FilterCandidate] = Field(
        description="The filters with a known band, among which one answers."
    )
    optics_choices: list[str] = Field(
        description="The optics you own, among which one answers a card that asks the optics."
    )
    typeless: list[TypelessFolder] = Field(
        description="The folders whose frames do not tell what file they are."
    )
    mosaics: list[MosaicCandidate] = Field(description="The regions taken in side-by-side panels.")
    to_confirm: int
