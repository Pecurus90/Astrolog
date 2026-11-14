"""The Gear page. What is not known is `None`, never zero: a number in its place would be a false
datum nobody could disprove (`docs/domini/attrezzatura.md`)."""

from typing import Literal

from pydantic import BaseModel, Field

from ..spine.rig_card import Slot
from .models_gear_numbers import PieceNumbers, RigNumbers, RigPieces
from .models_review import BandOut, CameraType, CardField, FilterSize, InstrumentKind, OpticalDesign
from .models_review_apply import BandIn, FilterSpecs


class InstrumentCardIn(BaseModel):
    """The card of a piece as one writes it: the fields, and nothing else. Both the piece being
    born and the one being corrected use it, so that the day a field changes shape it does not
    change in one action and not in the other. **Not the name**: when correcting it is a field like
    the others and may be left out, when creating it is what makes the piece exist -- so whoever
    asks for it declares it, with its own shape.

    The **measurements** are valid only positive: a zero is not a measurement, it is a blank written
    badly, and once on the card whoever derives from it discards it silently -- a focal length of 0
    makes the scale vanish. It is the same rule `RiglessGroupEdit.focal_mm` imposes on the answer
    about the camera: "unknown, never invented" either holds in every home, or it is not a rule."""

    brand: str | None = None
    model: str | None = None
    optical_design: OpticalDesign | None = None
    camera_type: CameraType | None = None
    sensor: str | None = None
    pixel_size_um: float | None = Field(None, gt=0)
    width_px: int | None = Field(None, gt=0)
    height_px: int | None = Field(None, gt=0)
    adc_bits: int | None = Field(None, gt=0)
    cooled: bool | None = None
    cooling_c: float | None = Field(
        None, gt=0, description="Degrees below the ambient: a cooling of zero is no cooling."
    )
    aperture_mm: float | None = Field(None, gt=0)
    focal_mm: float | None = Field(None, gt=0)
    image_circle_mm: float | None = Field(None, gt=0)
    required_backfocus_mm: float | None = Field(None, gt=0)
    backfocus_tolerance_mm: float | None = Field(None, gt=0)
    reducer_factor: float | None = Field(None, gt=0)
    thickness_mm: float | None = Field(None, gt=0)
    prism_mm: float | None = Field(None, gt=0)
    filter_size: FilterSize | None = None
    step_um: float | None = Field(None, gt=0)
    total_steps: int | None = Field(None, gt=0)
    weight_kg: float | None = Field(None, gt=0)
    payload_kg: float | None = Field(None, gt=0)
    payload_no_cw_kg: float | None = Field(None, gt=0)
    slots: int | None = Field(
        None, gt=0, description='A count: zero is not "I don\'t know", it is no wheel.'
    )
    notes: str | None = None


class InstrumentCorrection(InstrumentCardIn):
    """The card of a piece that already exists, or the merge with another (`merge_into`, "it is the
    same piece as", and then the rest does not count). Sending the name is renaming; not sending it
    leaves the one there is. Which piece it is, the address says."""

    name: str | None = Field(None, min_length=1)
    merge_into: int | None = None


class RigNaming(BaseModel):
    """The name you give a rig: it is how it is declared."""

    name: str = Field(min_length=1)


class FilterNew(FilterSpecs):
    """A filter you write: the name, and the band it lets through -- it is what unblocks the
    frames. Brand and model if you want."""

    name: str = Field(min_length=1)
    bands: list[BandIn] = Field(min_length=1)
    brand: str | None = None
    model: str | None = None


class RigNew(BaseModel):
    """A rig you write: optics and camera among your pieces, and the focal length -- without it, the
    files that tell it would make a second rig come into being."""

    optics_id: int
    camera_id: int
    focal_mm: float = Field(gt=0)


ChosenKind = Literal[
    "filter_wheel", "focuser", "guide_camera", "mount", "reducer", "guide_scope", "oag"
]  # fmt: skip


class RigPartChoice(BaseModel):
    """The piece you use a rig with, among those you own of that kind; `None` goes back to what
    the files say."""

    piece_id: int | None


class RigSpacers(BaseModel):
    """The spacers of a rig, all of them: the list replaces the one there is, empty takes them
    off. No file names a spacer, so there is nothing to go back to."""

    piece_ids: list[int]


class GearObject(BaseModel):
    """An object taken with that piece, and how much it weighed in."""

    key: str
    name: str | None
    frames: int
    integration_s: float


BAR = Field(
    description="Its hours on the most used of its group, 3-100: rigs among rigs, filters among "
    "filters, a piece among its kind. Never under 3, so a short bar still shows; null without "
    "known hours."
)


class PieceInRig(BaseModel):
    """A rig holding a piece or a filter: what the page says before deleting it."""

    rig_id: int
    frames: int = Field(description="The rig's frames that used it; a chosen part may have none.")
    chosen: bool = Field(description="You gave it to the rig, instead of the files naming it.")


class DeleteRefused(BaseModel):
    """Why Delete is off before the gesture: the same refusal the DELETE gives."""

    code: Literal["in_use", "in_rig"] = Field(
        description="`in_use`: frames use it. `in_rig`: the optics or camera of a rig without "
        "frames, which is made of it."
    )
    frames: int
    rigs: list[int] = Field(description="`in_use`: the rigs of those frames; `in_rig`: the rigs.")


class OffsetBias(BaseModel):
    """A camera's bias at one offset its files write (ADR 0022): it gives the sky brightness."""

    offset: int | None = Field(description="Null: the files do not write the offset.")
    bias_adu: float | None = Field(description="Null: not declared yet.")
    frames: int = Field(description="Its light frames with that offset.")


class OffsetBiasIn(BaseModel):
    offset: int | None = Field(ge=0)
    bias_adu: float = Field(gt=0, description="A bias of zero is no bias: it is not declared.")


class InstrumentOnPage(BaseModel):
    """A piece of the gear: its card -- the empty fields are those the header cannot tell and the
    user fills in -- plus how much it served and what you took with it."""

    id: int
    kind: InstrumentKind
    name: str
    brand: str | None
    model: str | None
    optical_design: OpticalDesign | None
    camera_type: CameraType | None
    sensor: str | None
    pixel_size_um: float | None
    pixel_from_sky_um: float | None = Field(
        description="Derived from the sky when the files do not say it: in a field of its own, so "
        "that whoever shows it says it is derived and does not confuse it with the one from the "
        "files or the user."
    )
    width_px: int | None = Field(
        description="The whole sensor: on a camera the most frequent among its files, the one "
        "you write wins. The same holds for `height_px`."
    )
    height_px: int | None
    adc_bits: int | None
    cooled: bool | None
    cooling_c: float | None
    aperture_mm: float | None
    focal_mm: float | None
    image_circle_mm: float | None
    required_backfocus_mm: float | None
    backfocus_tolerance_mm: float | None
    reducer_factor: float | None
    thickness_mm: float | None
    prism_mm: float | None
    filter_size: FilterSize | None
    step_um: float | None
    total_steps: int | None
    weight_kg: float | None
    payload_kg: float | None
    payload_no_cw_kg: float | None
    slots: int | None
    notes: str | None
    numbers: PieceNumbers
    detected: bool = Field(description="Detected from the files, or declared by you.")
    mergeable_into: list[int] = Field(
        description="The pieces it can be merged into: only those the spine accepts."
    )
    frames: int | None = Field(
        description="Null where the link with the frames does not exist: a kind that no frame in "
        "**this archive** names does not have zero hours, it has hours the app does not know -- "
        "and whoever shows the row says so. The spine decides it, not this shape. The same holds "
        "for `integration_s`, `untimed` and `nights`."
    )
    integration_s: float | None
    untimed: int | None
    nights: int | None
    objects: list[GearObject]
    counted: bool = Field(
        description='False for a piece born mid-run, which the counter has not counted yet: "not '
        'counted yet" is not "cannot be known", and the page tells them apart.'
    )
    no_hours: Literal["files_silent", "no_rig"] | None = Field(
        description="Why a counted piece has no hours to show: the files do not name that kind, "
        "or it is a mount, reducer or guide scope no rig carries yet. `None` when the hours "
        "are there."
    )
    bar_pct: float | None = BAR
    in_rigs: list[PieceInRig] = Field(
        description="The rigs holding it, by rig id: as a part, or as their optics or camera "
        "(`chosen` false). Deleting is refused while any frame uses it."
    )
    from_files: list[str] = Field(
        description='The card fields read from the files ("dai file"); any other filled field '
        'is yours ("inserito"). Only a camera\'s sensor specs come from the files.'
    )
    delete_refused: DeleteRefused | None = Field(
        description="Null: it can be deleted. Counted frames only: one not yet counted is "
        "refused by the DELETE itself."
    )
    rig_for_mount: int | None = Field(
        description="A mount no rig carries: the first rig still without a mount, where "
        '"Seleziona montatura" opens the choice. Null on any other piece.'
    )
    biases: list[OffsetBias] = Field(
        description="A camera's offsets as its files write them, each with its bias; empty on "
        "the other pieces."
    )


class RigPart(BaseModel):
    """One thing a rig's frames used besides optics and camera."""

    kind: Literal[
        "mount",
        "filter_wheel",
        "focuser",
        "guide_camera",
        "reducer",
        "guide_scope",
        "oag",
        "spacer",
        "software",
        "filter",
    ]
    id: int | None = Field(
        description="The instrument, or the filter for `filter`; null for `software`, which is "
        "not a piece."
    )
    name: str
    frames: int = Field(description="How many of the rig's frames used it, rewritten copies out.")
    chosen: bool = Field(
        description="You gave it to the rig, instead of the files naming it. A mount you choose "
        "goes on every frame; any other kind only where the file names none."
    )
    passband: str | None = Field(
        description="Only a filter: its canonical passband, which gives the colour."
    )
    ring_from: float | None = Field(
        description="Only a filter: where its slice of the rig's ring starts, in percent of the "
        "rig's filtered frames; `ring_to` where it ends, the next one's start."
    )
    ring_to: float | None


class RigSlot(BaseModel):
    """One of the ten parts of a rig's card."""

    kind: Slot
    filled: bool


class RigOnPage(BaseModel):
    """A rig: how it is made, how much it served, and **how much sky it really frames**."""

    id: int
    name: str | None = Field(description="The name you gave it, if you gave it one.")
    optics_id: int | None = Field(description="Its optics among `instruments`; `camera_id` too.")
    camera_id: int | None
    optics: str | None
    camera: str | None
    focal_mm: float | None
    frames: int | None = Field(
        description="Null until it is counted (`counted`): a rig born mid-run. The same holds for "
        "`integration_s`, `untimed` and `nights`."
    )
    integration_s: float | None
    untimed: int | None
    nights: int | None
    objects: list[GearObject]
    counted: bool
    bar_pct: float | None = BAR
    scale_arcsec_px: float | None = Field(
        description="Measured on the solved frames, median: null until the solver has solved "
        "one. Named as in the schema (`frame_wcs`), which is where they come from. The same "
        "holds for `width_deg` and `height_deg`."
    )
    width_deg: float | None
    height_deg: float | None
    parts: list[RigPart] = Field(
        description="What its frames used and what you chose for it, kind by kind in the card's "
        "order (mount, wheel, focuser, guide camera, reducer, guide scope, OAG, spacers, capture "
        "software, filters), each from the most used. A kind no frame names and you did not "
        "choose is not listed."
    )
    numbers: RigNumbers | None = Field(
        description="From the cards of its pieces: the chosen part, else the most used. Null "
        "only for a rig born after the last write of the numbers."
    )
    pieces: RigPieces | None = Field(
        description="The pieces the numbers read, which the optical train draws; null with them."
    )
    title: str | None = Field(
        description="The index card's title: your name for it, else optics and camera short "
        "(model, else the name without its brand). Null only without either piece."
    )
    slots: list[RigSlot] = Field(
        description="The ten parts of the card in its order, each held or still to say; the "
        "guide slot holds a guide scope or an OAG. Filters are not a slot."
    )
    slots_missing: int = Field(description="How many of `slots` are still to say.")


class FilterOnPage(BaseModel):
    """An owned filter, with the band it lets through."""

    id: int
    name: str
    brand: str | None
    model: str | None
    passband: str | None = Field(description="Its canonical passband: it gives the colour.")
    bands: list[BandOut]
    filter_size: FilterSize | None
    thickness_mm: float | None
    mounted: bool | None
    fast_optics: bool | None
    frames: int | None = Field(
        description="Null until it is counted (`counted`). The same holds for `integration_s`, "
        "`untimed` and `nights`."
    )
    integration_s: float | None
    untimed: int | None
    nights: int | None
    objects: list[GearObject]
    counted: bool
    mergeable_into: list[int] = Field(
        description="The filters it can be merged into: only those the spine accepts."
    )
    bar_pct: float | None = BAR
    in_rigs: list[PieceInRig] = Field(description="The rigs whose frames used it, by rig id.")
    delete_refused: DeleteRefused | None = Field(description="Null: it can be deleted.")


class FieldBox(BaseModel):
    """A rig's measured field on the comparison frame: the widest plus 15%, never under 0.9
    degrees, two thirds as tall (board v82 `confronto`)."""

    rig_id: int
    width_pct: float
    height_pct: float = Field(description="Never over 100: a tall field stops at the frame.")


class GearList(BaseModel):
    instruments: list[InstrumentOnPage]
    rigs: list[RigOnPage]
    filters: list[FilterOnPage]
    cards: dict[InstrumentKind, list[CardField]] = Field(
        description="Which fields the card of each kind asks for, in reading order. It comes **per "
        "kind and not per piece** because it also serves to write one of a kind you do not own "
        "yet: there, there is no piece to copy them from. The backend decides them, and the page "
        "keeps no second list."
    )
    moon_deg: float = Field(
        description="The full Moon's apparent diameter, drawn beside the rigs' fields for scale."
    )
    fields: list[FieldBox] = Field(
        description="The measured rigs' fields on one comparison frame, widest first: the board "
        "draws them one over the other. Empty until a rig has a solved frame."
    )
    moon_pct: float | None = Field(
        description="The full Moon's width on that frame, in percent; null without fields."
    )
    brands: list[str] = Field(
        description='The makers already written on pieces and filters: "altra" adds a new one.'
    )


class InstrumentNew(InstrumentCardIn):
    """A piece you write. Kind and name are what make it exist -- a piece is its name within its
    kind -- and the card comes with it: creating and then correcting would be two actions for a
    single thing, and between the two the piece would half exist."""

    kind: InstrumentKind
    name: str = Field(
        min_length=1, description="Required here: without a name the piece is nobody."
    )


class GearWritten(BaseModel):
    """What happened while writing. `requeued` is not zero when the answer changes the meaning of
    some frame -- the colour of a camera does -- and then the work restarts by itself."""

    id: int
    requeued: int
    run_started: bool


class CameraBiasIn(BaseModel):
    """A camera's bias at one offset, as the files write both (ADR 0021, ADR 0022)."""

    camera: str = Field(min_length=1, description="The camera as the files write it.")
    offset: int | None = Field(ge=0, description="Null: the files do not write the offset.")
    bias_adu: float = Field(gt=0, description="A bias of zero is no bias: it is not declared.")


class CameraBiasOut(BaseModel):
    """One camera and offset of the files, or of a declared bias; `frames`: its light frames."""

    camera: str
    offset: int | None
    bias_adu: float | None = Field(description="Null: not declared yet.")
    frames: int
