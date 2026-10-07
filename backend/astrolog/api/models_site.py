"""Site and first-launch shapes. `bortle` goes out but never into the database: it derives from the
brightness, and on creation it is only an input shortcut converted at once into a brightness."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..units import SQM_MAX, SQM_MIN
from .models_page import Page

# Closed sets of codes, not sentences: they reach the screen, and a new word would arrive
# untranslated.
Missing = Literal["no_active_site", "no_solver", "no_star_database"]
SolverSource = Literal["declared", "env", "path", "known_place"]
SkySource = Literal["measured", "service", "scale"]
ElevationSource = Literal["declared", "service"]

# A null alone does not tell "I don't know" from "I didn't ask": each empty field carries its code.
Unknown = Literal["site_no_timezone", "site_no_elevation", "site_no_sky"]


class SiteOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    elevation_m: float | None = Field(
        description="None = not provided: zero is sea level, and it is a true value."
    )
    elevation_source: ElevationSource | None
    timezone: str | None = Field(
        description="None where no time zone is recognised for the coordinates; in open sea it is"
        " the nautical zone (Etc/GMT...)."
    )
    sky_sqm: float | None
    sky_source: SkySource | None
    bortle: int | None = Field(
        description="DERIVED: not a column, and it never appears without the measurement."
    )
    is_default: bool
    nights: int = Field(
        description="How many nights hold it: whoever deletes it knows before trying."
    )
    unknown: list[Unknown] = Field(description="The empty fields, with their reason.")


class SiteList(Page[SiteOut]):
    pass


class SiteCreate(BaseModel):
    name: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = Field(
        default=None,
        description="If you don't give it, the app asks the service; if you do, yours wins.",
    )
    sky_sqm: float | None = Field(None, ge=SQM_MIN, le=SQM_MAX)
    bortle: int | None = Field(None, ge=1, le=9)
    is_default: bool = False


class SiteEdit(BaseModel):
    """What changes in a site. An absent field stays as it is; changed coordinates redo the time
    zone, because an old time zone on new coordinates is a silent error."""

    name: str | None = Field(None, min_length=1)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    elevation_m: float | None = None
    sky_sqm: float | None = Field(None, ge=SQM_MIN, le=SQM_MAX)
    bortle: int | None = Field(None, ge=1, le=9)


class SiteDeleted(BaseModel):
    site_id: int
    deleted: bool


class PlaceOut(BaseModel):
    """A place found by name. It is not a site of the archive: it is a candidate, and becomes a
    site only when the user creates it."""

    name: str
    latitude: float
    longitude: float


class PlaceList(BaseModel):
    """The search is an ACTION, not a list from the archive: no pages, at most a handful of
    candidates the service proposed."""

    items: list[PlaceOut]


class SettingsOut(BaseModel):
    values: dict[str, str | None]
    wizard_done: bool = Field(
        description='The stamp is there: a written fact, not "it looks empty".'
    )
    missing: list[Missing]


class SolverOut(BaseModel):
    """Where the app takes the solver from, and **what** it deduced that from.

    The channel always comes with the path because "found" alone cannot be disproved: automatic
    search goes wrong exactly when it finds something -- an old ASTAP left in the PATH, or another
    user's in a known place -- and whoever looks must be able to say "no, not that one" without
    guessing which of the four channels answered."""

    path: str | None = Field(
        description="None = not found: the channel is None together with it, never alone."
    )
    source: SolverSource | None
    declared: str | None = Field(
        description="What the user wrote, **even when it leads nowhere**: without it, a wrong "
        "path would vanish from the screen and there would be nothing to correct."
    )
    databases: list[str] = Field(
        description="The star databases found next to the program, by name (`d80`, `v50`). "
        "Empty **with** a path means ASTAP starts and recognises nothing; empty **without** a "
        "path only means ASTAP is not there."
    )


class SettingsPatch(BaseModel):
    """A write either passes whole or does not pass: half the preferences written would be worse.

    The values go in as they are: the type of each key is judged where the closed list of keys
    lives, and declaring it here as well would mean writing it twice."""

    values: dict[str, Any]


class BackupCounts(BaseModel):
    """How many of each thing the file carries, as the offer says them."""

    written_at: str | None
    sites: int
    folders: int
    instruments: int
    filters: int
    answers: int


class BackupStatus(BaseModel):
    """The backup next to the database (ADR 0017) and whether to offer it.

    `offer` is `found` only on a database just created with a file beside it, until it is
    restored or declined; `none` otherwise. `last` is the file as it is now, `null` without one;
    `unreadable` is true when a file is there but is not a backup this app reads."""

    offer: Literal["found", "none"]
    last: BackupCounts | None
    unreadable: bool
    path: str
