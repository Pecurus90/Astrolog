"""The Gear page. What is not known is `None`, never zero: a number in its place would be a false
datum nobody could disprove (`docs/domini/attrezzatura.md`)."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_review import BandOut, CameraType, CardField, InstrumentKind
from .models_review_apply import BandIn


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
    camera_type: CameraType | None = None
    pixel_size_um: float | None = Field(None, gt=0)
    aperture_mm: float | None = Field(None, gt=0)
    focal_mm: float | None = Field(None, gt=0)
    reducer_factor: float | None = Field(None, gt=0)
    weight_kg: float | None = Field(None, gt=0)
    payload_kg: float | None = Field(None, gt=0)
    slots: int | None = Field(
        None, gt=0, description='A count: zero is not "I don\'t know", it is no wheel.'
    )
    backfocus_mm: float | None = Field(None, gt=0)
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


class FilterNew(BaseModel):
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


class RigMount(BaseModel):
    """The mount you use a rig with, among those you own; `None` goes back to the one the files
    say."""

    mount_id: int | None


class GearObject(BaseModel):
    """An object taken with that piece, and how much it weighed in."""

    key: str
    name: str | None
    frames: int
    integration_s: float


class InstrumentOnPage(BaseModel):
    """A piece of the gear: its card -- the empty fields are those the header cannot tell and the
    user fills in -- plus how much it served and what you took with it."""

    id: int
    kind: InstrumentKind
    name: str
    brand: str | None
    model: str | None
    camera_type: CameraType | None
    pixel_size_um: float | None
    pixel_from_sky_um: float | None = Field(
        description="Derived from the sky when the files do not say it: in a field of its own, so "
        "that whoever shows it says it is derived and does not confuse it with the one from the "
        "files or the user."
    )
    aperture_mm: float | None
    focal_mm: float | None
    reducer_factor: float | None
    weight_kg: float | None
    payload_kg: float | None
    slots: int | None
    backfocus_mm: float | None
    notes: str | None
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
        "or it is a mount no rig carries yet. `None` when the hours are there."
    )


class RigOnPage(BaseModel):
    """A rig: how it is made, how much it served, and **how much sky it really frames**."""

    id: int
    name: str | None = Field(description="The name you gave it, if you gave it one.")
    mount_id: int | None = Field(
        description="The mount you gave it; where you are silent, the frames take the one the "
        "file names."
    )
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
    scale_arcsec_px: float | None = Field(
        description="Measured on the solved frames, median: null until the solver has solved "
        "one. Named as in the schema (`frame_wcs`), which is where they come from. The same "
        "holds for `width_deg` and `height_deg`."
    )
    width_deg: float | None
    height_deg: float | None


class FilterOnPage(BaseModel):
    """An owned filter, with the band it lets through."""

    id: int
    name: str
    brand: str | None
    model: str | None
    bands: list[BandOut]
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
