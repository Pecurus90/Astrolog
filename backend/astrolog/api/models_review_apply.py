"""The answers of "To confirm": what Apply accepts, and what comes back. One answers with the
stable key read from the page, never with the row number."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models_review import Band
from .models_review_groups import GearFilterAnswer, MosaicAnswer, TypelessAnswer


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
    """The answer on an object card: a catalog slug (usually a clicked candidate), a hand-written
    name, or "it is not an object"."""

    key: str = Field(min_length=1, description="The card's key read from the page.")
    slug: str | None = Field(None, min_length=1)
    name: str | None = Field(None, min_length=1)
    not_an_object: bool = False

    @model_validator(mode="after")
    def one_answer_only(self) -> Self:
        """Exactly one: accepting two would mean choosing for the user which one wins. A name of
        only spaces is no answer: Apply would say "done" with nothing changed."""
        named = bool(self.name and self.name.strip())
        if [bool(self.slug), named, self.not_an_object].count(True) != 1:
            raise ValueError("una risposta sola: slug, name oppure not_an_object")
        return self


class CoordinatesEdit(BaseModel):
    """The answer about a place: "the frames taken at these coordinates are of this site".

    The site id is sent because it is what the page holds after a click; what gets written is the
    **name**, which is the key that survives."""

    key: str = Field(
        min_length=1, description="The coordinates read from the page, never a row number."
    )
    site_id: int


class GearEdit(BaseModel):
    """The answer about a signature, the parts it asks: the camera -- a rig among those the app
    knows (`rig_id`, what the page holds after a click) **or** the written camera with its focal
    length, plus the optics if needed --, the optics alone, and what sat in front (`filter`, with
    `filter_id` for "one of yours"). What is written is always **names**: the pieces come into
    being from them as from a header. A part not sent keeps its earlier answer."""

    key: str = Field(min_length=1, description="The signature read from the page.")
    rig_id: int | None = None
    camera: str | None = Field(
        None, min_length=1, pattern=r"\S", description="A name of only spaces is not a name."
    )
    optics: str | None = Field(None, min_length=1, pattern=r"\S")
    focal_mm: float | None = Field(
        None, gt=0, description="Unknown focal length, never invented: no zeros."
    )
    filter: GearFilterAnswer | None = None
    filter_id: int | None = None

    @model_validator(mode="after")
    def one_way_each(self) -> Self:
        """Accepting both a listed rig and written pieces would mean choosing which one wins.
        Checked here so the OpenAPI declares it and the answer is the usual 422."""
        if self.rig_id and (self.camera or self.optics or self.focal_mm):
            raise ValueError("un corredo dall'elenco porta i suoi pezzi")
        if bool(self.camera) != (self.focal_mm is not None):
            # A rig is optics + camera at one focal length: without it, this rig and the one the
            # files name tomorrow would stay twins forever, splitting the hours between them.
            raise ValueError("la camera con la sua focale, e la focale solo con la camera")
        if (self.filter_id is None) == (self.filter == "filter"):
            # without it "one of yours" would not say which; beside another answer, a second target
            raise ValueError("filter_id con la risposta filter, e solo con lei")
        if not (self.rig_id or self.camera or self.optics or self.filter):
            raise ValueError("una risposta dice almeno una parte")
        return self


class TypelessFolderEdit(BaseModel):
    """The answer about a folder of frames that do not tell what file they are: a sky picture
    (`light`) or a calibration file (`calibration`). The words are two and live in the model, so a
    third one is a 422 declared in the OpenAPI and not an answer to interpret."""

    key: str = Field(min_length=1, description="The folder path read from the page.")
    kind: TypelessAnswer


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
        named = bool(self.name and self.name.strip())
        if named != (self.answer == "yes") or (self.name is not None and not named):
            raise ValueError("il si' con il nome del mosaico, il no senza")
        return self


class ReviewApply(BaseModel):
    """All the answers together, written in a single transaction; only what is answered is
    written (ADR 0014, S4).

    **A field that does not exist is an error, not a slip to ignore** (`extra="forbid"`): a page
    opened before a server update would send the old name, and Pydantic would discard it silently.
    On the NAS it is the ordinary scenario -- a tab left open on the tablet. Better a 422 that
    shows."""

    model_config = ConfigDict(extra="forbid")

    lookalikes: list[LookalikeEdit] = []
    filters: list[FilterEdit] = []
    objects: list[ObjectEdit] = []
    unclear: list[CoordinatesEdit] = []
    gear: list[GearEdit] = []
    typeless: list[TypelessFolderEdit] = []
    mosaics: list[MosaicEdit] = []


class ReviewApplied(BaseModel):
    changed: int = Field(description="Answers written.")
    requeued: int = Field(
        description="Frames put back in the queue because the answer concerns them."
    )
    run_started: bool = Field(
        description="False if the worker was busy: the work stays in the queue."
    )
