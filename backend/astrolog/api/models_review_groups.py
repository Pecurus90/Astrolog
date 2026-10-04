"""The groups of frames the app asks about. Always per group, never per frame; each carries the
stable key one answers with, and stays on the page once answered (`answer`) to allow a change."""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

# One decimal, as the screen shows it. Rounded here and not in `place.distance_km`, which is
# compared with `spine.group.SAME_PLACE_KM`: rounding there would move the threshold.
DistanceKm = Annotated[float, AfterValidator(lambda km: round(km, 1))]


class Subject(BaseModel):
    """An object the sky found in the frames of a group, and in how many."""

    name: str
    frames: int


class Subjects(BaseModel):
    """What you took in that group, to remember it without going by memory: the objects, the most
    taken on top, and the frames of the two blanks -- which are not the same: `not_yet` is the sky
    that has not looked yet (or did not manage to), `not_found` the sky that looked without finding
    anything. It reads next to the question and does not change it: the group key stays the
    same."""

    found: list[Subject]
    not_found: int
    not_yet: int


class UnnamedAnswer(BaseModel):
    """What the user said about a group of frames with no name and no sky: a catalog object
    (`value` is the slug), a written name, or "it is not an object" (`value` empty). `name` is how
    the object shows: the name of the entry, or the written one."""

    kind: Literal["catalog", "name", "none"]
    value: str | None
    name: str | None


class UnnamedGroup(BaseModel):
    """The frames the header does not name and the sky says nothing about, grouped by **night,
    camera, telescope and pointing**, never by file or folder. The group shows with those values;
    the pointing is that of the frame that opened it. An answered group stays on the page with
    `answer`, because one must be able to change one's mind."""

    key: str = Field(description="The group key: one answers with it, and it does not reopen.")
    night: str | None = Field(
        description="The night, YYYY-MM-DD; empty for those that do not say when."
    )
    camera: str | None = Field(description="`INSTRUME` as written in the file.")
    telescope: str | None = Field(description="`TELESCOP` as written in the file.")
    ra_deg: float | None = Field(description="Where the mount pointed, from the header.")
    dec_deg: float | None
    frames: int
    answer: UnnamedAnswer | None
    first_frame: str | None = Field(
        description="The first and the last frame, ISO in the night's time zone: two objects "
        "without pointing in the same night are a single group, and the hours tell whoever "
        "answers whether they are two. Frames with `DATE-OBS` count: null if none says it."
    )
    last_frame: str | None


class SiteCandidate(BaseModel):
    """A site already declared, with how far it is from those coordinates: it is what one clicks to
    answer. Recomputed on reading, not saved."""

    id: int
    name: str
    distance_km: DistanceKm


class UnclearCoordinates(BaseModel):
    """The frames the app stopped because the header coordinates say another place, grouped by
    **coordinates**: one asks per group, never per frame. The nights are those involved, computed
    in the time zone of those coordinates. `site` is the answer already given, if there is one: an
    answered group stays on the page because a wrong click must be changeable."""

    key: str = Field(description="The rounded coordinates: it is the key one answers with.")
    latitude: float
    longitude: float
    distance_km: DistanceKm | None = Field(
        description="From home; None without a home site (never a fake zero)."
    )
    frames: int
    nights: list[str]
    site: str | None
    candidates: list[SiteCandidate]
    subjects: Subjects


# The words of `spine.unfiltered`, kept glued by a test. The sensor is told by the card
# (`CameraType`).
UnfilteredAnswer = Literal["color", "no_filter", "filter"]


class UnfilteredCamera(BaseModel):
    """The frames that do not tell the filter, grouped by **camera**: without `BAYERPAT` a mono and
    a colour camera cannot be told apart, and one asks only once. A camera the card or the files
    say is colour is not there: its frames are OSC. `answer` is the answer already given: an
    answered group stays on the page because one must be able to change one's mind."""

    key: str = Field(description="The camera name: it is the key one answers with.")
    frames: int
    answer: Literal["no_filter", "filter"] | None = Field(
        description='"Colour" removes it from the page.'
    )
    filter_id: int | None = Field(
        description='With "one of yours", which one; empty if that filter is no longer there.'
    )
    subjects: Subjects


# The words of `spine.typeless.ANSWERS`, kept glued by a test. No "don't know": not knowing is
# already the starting state, and a third answer would move those frames nowhere.
TypelessAnswer = Literal["light", "calibration"]


class TypelessFolder(BaseModel):
    """The frames that do not tell what file they are, grouped by **folder**: whoever shoots keeps
    darks and flats in folders of their own, so one answer closes a whole folder. Only the folders
    where the sky cannot tell are here -- solved is a picture, no stars a calibration --, and until
    answered those frames stay still before the object: they do not become hours, and they do not
    appear among the unnamed frames -- there the question is "what did you take", and answering
    with an object would turn a calibration into hours. An answered group stays on the page because
    one must be able to change one's mind. What the sky found here is absent, and it is not an
    oversight: on those frames the sky could not tell, and showing "no object" would look like an
    answer."""

    key: str = Field(description="The folder path: it is the key one answers with.")
    frames: int
    answer: TypelessAnswer | None


class GroupRig(BaseModel):
    """The rig the user named for a group: the **names** of the pieces, never the row numbers.
    Empty `optics` means they did not say it, not that there was none."""

    optics: str | None
    camera: str
    focal_mm: float | None


class OpticslessRig(BaseModel):
    """The frames whose files do not name the optics (the ASIAIR writes the mount there, others do
    not write it at all), one question per **camera and focal length**: "which optics was it?". The
    answer also holds for the frames still to come; an answered question stays on the page to allow
    a change of mind."""

    key: str = Field(description="The key of the camera at that focal length: one answers with it.")
    camera: str
    focal_mm: float | None
    frames: int
    integration_s: float
    untimed: int
    answer: str | None = Field(description="The name of the optics already given.")
    subjects: Subjects


class RiglessGroup(BaseModel):
    """The frames that do not tell which camera took them, grouped by **night and header values**:
    one asks per group, never per frame, and never per folder. The group shows with the night --
    empty for frames without a date -- and the values that make it. The frames that carry the
    telescope but not the camera fall here too (the ASIAIR writes the mount in `TELESCOP`).
    `optics` and `focal_mm` are what the frames already say, when they say a single thing;
    `focal_suggested` the native focal length of the optics on the card, to propose where the frames
    do not carry it. An answered group stays on the page because one must be able to change one's
    mind."""

    key: str = Field(description="The group key: one answers with it, and it does not reopen.")
    night: str | None = Field(
        description="The night, YYYY-MM-DD; empty for those that do not say when."
    )
    telescope: str | None = Field(
        description="`TELESCOP` as written in the file: it is in the key, and goes on screen."
    )
    width_px: int | None
    height_px: int | None
    pixel_um: float | None
    frames: int
    optics: str | None
    focal_mm: float | None
    focal_suggested: float | None
    answer: GroupRig | None
    subjects: Subjects


# The words of `spine.declarations.MOSAIC_ANSWERS`, kept glued by a test. A no is an answer like a
# yes: without it, the only way to silence a wrong proposal would be to accept it.
MosaicAnswer = Literal["yes", "no"]


class MosaicCandidate(BaseModel):
    """A region taken in **side-by-side panels**, as the page proposes it: how many panels, how many
    frames and which subjects it touches -- often more than one, because each panel frames a
    different part of the complex and the app identifies them as different objects.

    One answers with the **key** of the mosaic, which does not change when the camera changes. An
    answered group stays on the page: one must be able to change one's mind."""

    key: str = Field(description="What one answers with.")
    ra_deg: float = Field(
        description="The centre of the mosaic: on screen it tells which, if two have the same name."
    )
    dec_deg: float
    object: str = Field(
        description="The subjects it touches, with their names, in alphabetical order."
    )
    panels: int
    frames: int
    integration_s: float = Field(
        description="The sum of the panels' time; on screen it reads in hours."
    )
    untimed: int = Field(
        description="How many of those frames do not tell their time: they are not worth zero, "
        "they are counted here."
    )
    answer: MosaicAnswer | None
    answer_name: str | None = Field(
        description="What the mosaic is of, as the user said it; only with yes."
    )
    names: list[str] = Field(
        description="The subjects of `object`, one per entry, and the proposal: the suggestions."
    )
    proposed: str = Field(
        description="The catalog entry at the centre: the field arrives filled in with it."
    )
