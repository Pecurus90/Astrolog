"""The answers of "To confirm": what Apply accepts, and what comes back. One answers with the
stable key read from the page, never with the row number."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models_review import Band, ReviewSeen
from .models_review_groups import MosaicAnswer, TypelessAnswer, UnfilteredAnswer


class BandIn(BaseModel):
    band: Band
    width_nm: float | None = None


class FilterCorrection(BaseModel):
    """The card of a filter, or "it is the same filter as" (`merge_into`)."""

    name: str | None = Field(None, min_length=1)
    brand: str | None = None
    model: str | None = None
    catalog_id: str | None = None
    bands: list[BandIn] | None = None
    merge_into: int | None = None


class FilterEdit(FilterCorrection):
    id: int
    is_none: bool | None = None


class LookalikeEdit(BaseModel):
    """The answer to "are they the same piece?": yes merges `id` into `into_id`, no says they are
    two pieces and the proposal does not come back."""

    id: int
    into_id: int
    same: bool


class ObjectEdit(BaseModel):
    """The answer about an object: a catalog slug (usually a clicked candidate) or a hand-written
    name."""

    key: str = Field(
        min_length=1, description="The stable key read from the page, never the row id."
    )
    slug: str | None = None
    name: str | None = Field(None, min_length=1)

    @model_validator(mode="after")
    def one_target_only(self) -> Self:
        """Exactly one of the two: accepting both would mean choosing for the user which one wins.
        Checked here so the OpenAPI declares it and the answer is the usual 422."""
        if bool(self.slug) == bool(self.name):
            raise ValueError("un bersaglio solo: slug oppure name")
        return self


class CoordinatesEdit(BaseModel):
    """The answer about a place: "the frames taken at these coordinates are of this site".

    The site id is sent because it is what the page holds after a click; what gets written is the
    **name**, which is the key that survives."""

    key: str = Field(
        min_length=1, description="The coordinates read from the page, never a row number."
    )
    site_id: int


class UnfilteredEdit(BaseModel):
    """The answer about a camera: its frames that do not tell the filter are of a colour camera
    (`color`), taken with no filter (`no_filter`), or with one of your filters (`filter`, and
    `filter_id` says which)."""

    key: str = Field(min_length=1, description="The camera name read from the page.")
    answer: UnfilteredAnswer
    filter_id: int | None = None

    @model_validator(mode="after")
    def a_filter_says_which(self) -> Self:
        """Without the filter, "one of yours" would not say which; with another answer it would be
        a second target for us to choose between."""
        if (self.filter_id is None) == (self.answer == "filter"):
            raise ValueError("filter_id con la risposta filter, e solo con lei")
        return self


class OpticslessEdit(BaseModel):
    """The answer about a camera at one focal length: with which optics. The **name** is written:
    one the Gear page does not have makes the piece come into being, like a header."""

    key: str = Field(min_length=1, description="The key read from the page.")
    optics: str = Field(
        min_length=1, pattern=r"\S", description="A name of only spaces is not a name."
    )


class RiglessGroupEdit(BaseModel):
    """The answer about a group: with which rig those frames were taken. A rig among those the app
    knows (`rig_id`, what the page holds after a click) **or** the written pieces: the camera and
    the **focal length**, plus the optics if needed. What is written is always the **names**, and
    the pieces come into being from those names as they do from a header."""

    key: str = Field(min_length=1, description="The group key read from the page.")
    rig_id: int | None = None
    optics: str | None = Field(None, min_length=1)
    camera: str | None = Field(None, min_length=1)
    focal_mm: float | None = Field(
        None, gt=0, description="Unknown focal length, never invented: no zeros."
    )

    @model_validator(mode="after")
    def one_way_only(self) -> Self:
        """Accepting both a listed rig and written pieces would mean choosing which one wins.
        Checked here so the OpenAPI declares it and the answer is the usual 422."""
        if bool(self.rig_id) == bool(self.camera):
            raise ValueError("un corredo dall'elenco, oppure la camera scritta")
        if self.rig_id and (self.optics or self.focal_mm):
            raise ValueError("un corredo dall'elenco porta i suoi pezzi")
        if self.camera and self.focal_mm is None:
            # A rig is optics + camera at one focal length: without it, this rig and the one the
            # files name tomorrow would stay twins forever, splitting the hours between them.
            raise ValueError("con la camera si scrive anche la focale")
        return self


class TypelessFolderEdit(BaseModel):
    """The answer about a folder of frames that do not tell what file they are: a sky picture
    (`light`) or a calibration file (`calibration`). The words are two and live in the model, so a
    third one is a 422 declared in the OpenAPI and not an answer to interpret."""

    key: str = Field(min_length=1, description="The folder path read from the page.")
    kind: TypelessAnswer


class UnnamedEdit(BaseModel):
    """The answer about a group of frames with no name and no sky: which object it is -- a catalog
    slug or a written name -- or "it is not an object"."""

    key: str = Field(min_length=1, description="The group key read from the page.")
    slug: str | None = Field(None, min_length=1)
    name: str | None = Field(None, min_length=1)
    not_an_object: bool = False

    @model_validator(mode="after")
    def one_answer_only(self) -> Self:
        """A name of only spaces is no answer: written, the rule would read it as a bad row and
        Apply would say "done" with nothing changed."""
        nome = bool(self.name and self.name.strip())
        if [bool(self.slug), nome, self.not_an_object].count(True) != 1:
            raise ValueError("una risposta sola: slug, name oppure not_an_object")
        return self


class MosaicEdit(BaseModel):
    """The answer about a proposed mosaic: yes, those panels are a mosaic (`yes`), or no.

    The **key** of the mosaic read from the page is sent."""

    key: str = Field(min_length=1)
    answer: MosaicAnswer
    name: str | None = Field(
        default=None,
        description="What the mosaic is of: with yes it is always there, with no never.",
    )

    @model_validator(mode="after")
    def a_yes_says_what(self) -> Self:
        """A single question: the yes says of what, the no says nothing. A name of only spaces
        would name the mosaic with a blank."""
        nome = bool(self.name and self.name.strip())
        if nome != (self.answer == "yes") or (self.name is not None and not nome):
            raise ValueError("il si' con il nome del mosaico, il no senza")
        return self


class ReviewApply(BaseModel):
    """All the decisions together: they are written in a single transaction, and what is listed on
    the page stays confirmed even if it was not touched.

    **A field that does not exist is an error, not a slip to ignore** (`extra="forbid"`): a page
    opened before a server update would send the old name, Pydantic would discard it silently and
    Apply would confirm **everything**, including what that page never showed. On the NAS it is the
    ordinary scenario -- a tab left open on the tablet -- and the damage falls on the side nobody
    looks at again. Better a 422 that shows."""

    model_config = ConfigDict(extra="forbid")

    lookalikes: list[LookalikeEdit] = []
    filters: list[FilterEdit] = []
    objects: list[ObjectEdit] = []
    unclear: list[CoordinatesEdit] = []
    unfiltered: list[UnfilteredEdit] = []
    rigless: list[RiglessGroupEdit] = []
    opticsless: list[OpticslessEdit] = []
    unnamed: list[UnnamedEdit] = []
    typeless: list[TypelessFolderEdit] = []
    mosaics: list[MosaicEdit] = []
    seen: ReviewSeen | None = Field(
        default=None,
        description='How far the page being applied had looked. Absent means "confirm what is '
        "there now\": asked by whoever did not read a page, and it is not the button's way.",
    )


class ReviewApplied(BaseModel):
    changed: int = Field(description="Answers written.")
    confirmed: int = Field(description="Entries that from now on are no longer asked.")
    requeued: int = Field(
        description="Frames put back in the queue because the answer concerns them."
    )
    run_started: bool = Field(
        description="False if the worker was busy: the work stays in the queue."
    )
