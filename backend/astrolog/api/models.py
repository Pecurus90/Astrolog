"""Spine shapes. "Don't know" is a coded field, never a silent null; archive row lists are paged
(`Page`), an action's answer is not. Each domain keeps its models in its own `models_*` file."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .models_page import Page


class Health(BaseModel):
    status: Literal["ok"]
    api_version: str
    schema_tables: int
    data_root: str | None
    catalog_entries: int
    catalog_version: str | None


class PathInfo(BaseModel):
    family: Literal["windows", "posix"]
    data_root: str | None


class FolderCreate(BaseModel):
    root_path: str = Field(min_length=1)
    name: str | None = None


class PathProbe(BaseModel):
    root_path: str = Field(min_length=1)


class ProbeOut(BaseModel):
    root_path: str
    reachable: bool
    fits_count: int | None = Field(
        description="None = not looked at (the folder is unreachable); never reported as 0."
    )
    complete: bool | None = Field(
        description='False = the count stopped at the time limit: there are "more than" fits_count.'
    )


class FolderEntry(BaseModel):
    name: str
    path: str = Field(description="The path to register, as it is.")


class BrowseOut(BaseModel):
    path: str
    parent: str | None = Field(description="None at the data root: there is no going higher.")
    folders: list[FolderEntry] = Field(description="The visible subfolders, sorted.")


class FolderOut(BaseModel):
    id: int
    name: str | None
    root_path: str
    created_at: str
    reachable: bool
    frames: int = Field(
        description="Positions present: comes from the database, so it holds with the disk "
        "detached too."
    )
    reactivated: bool = False


class FolderList(Page[FolderOut]):
    pass


class RetireOut(BaseModel):
    folder_id: int
    retired: bool
    kept_frames: int


class ScanStarted(BaseModel):
    run_id: int
    folder_id: int


class FolderSkipped(BaseModel):
    """A folder the toolbar action did not read, with its reason: `root_unreachable` (the
    detached disk, the NAS switched off) or `scan_running` (another run is already reading it).

    It carries the **path** and not just the row id: that is what the user recognises, and the
    scan route already holds it for its pre-check. Without it the page would have to fetch the
    folder list and stitch two answers together right at the moment of the failure -- and for a
    user with more than a hundred folders they would not even match up."""

    folder_id: int
    root_path: str
    reason: Literal["root_unreachable", "scan_running"]


class ScanAllStarted(BaseModel):
    """What the "read them all" action did: the folders started, each with its receipt, and the
    ones skipped with their reason. Skipped folders are reported instead of vanishing: a
    detached disk is exactly what the user must know, and hiding it would make an incomplete
    scan look complete."""

    started: list[ScanStarted]
    skipped: list[FolderSkipped]


# The words of `spine/scan_store` for why a file did not get in and why it was skipped.
FileError = Literal["file_unreadable", "header_unreadable", "name_not_utf8", "internal_error"]
SkipReason = Literal["calibration", "stack", "still_writing"]


class FileNotRead(BaseModel):
    file: str = Field(
        description="Relative to the root; a name that is not UTF-8 carries `?` in place of the "
        "bad bytes."
    )
    reason: FileError


class SkippedCount(BaseModel):
    reason: SkipReason
    count: int


class ScanRunOut(BaseModel):
    id: int
    folder_id: int
    folder_path: str = Field(
        description="The folder's path, which is what the user recognises: with `folder_id` "
        "alone the page would have to read the folders and pair them up itself. Never empty: "
        "removing a folder **retires** it, and the foreign key of `scan_runs` keeps its row."
    )
    folder_retired: bool = Field(
        description="The folder was removed (retired) since: its path no longer updates."
    )
    started_at: str
    ended_at: str | None
    duration_s: float | None = Field(
        description="None = unknown: the run is open, or the two instants do not add up."
    )
    status: Literal["ok", "stopped", "aborted", "error"] | None = Field(
        description="None = the run is open."
    )
    reason: Literal["root_unreachable", "stop_requested", "internal_error", "database_error"] | None
    found: int
    new: int
    unchanged: int
    duplicates: int
    missing: int
    skipped: int
    errors: int
    online_only: int = Field(
        description="Online-only FITS: not opened, so as not to download them; they are "
        "revisited later."
    )
    unreadable_dirs: list[str]
    hidden_dirs: list[str] = Field(
        description="Hidden subfolders left out (the recycle bin, for instance)."
    )
    linked_dirs: list[str] = Field(
        description="Reached through a link or a junction: not followed."
    )
    skipped_by_reason: list[SkippedCount] = Field(
        description="How many were skipped per reason, calibration frames included."
    )


class ScanRunList(Page[ScanRunOut]):
    pass


class ScanErrorList(Page[FileNotRead]):
    """The files a scan did not read, paginated: they can be thousands."""


StageState = Literal["not_run", "running", "stopped", "completed", "completed_with_errors", "error"]


class StageRecord(BaseModel):
    name: str
    state: StageState
    current: int | None
    total: int | None
    tally: dict[str, Any]
    reason: str | None = Field(
        default=None,
        description="Why the stage stopped, when it stopped on its own: a code, never a sentence.",
    )


class WorkerSnapshot(BaseModel):
    state: Literal["idle", "running", "stopped", "completed", "completed_with_errors", "error"]
    stage: str | None
    started_at: str | None = Field(
        description="None until it has ever started: never an invented instant."
    )
    ended_at: str | None
    stages: list[StageRecord]
    error: str | None = None


class ScanEvent(BaseModel):
    """A scan progress event: the file being read and the counts so far."""

    current: int
    total: int
    file: str
    run_id: int
    folder_id: int
    found: int
    new: int
    unchanged: int
    duplicates: int
    missing: int
    skipped: int
    errors: int
    online_only: int


class ScanProgress(BaseModel):
    """The scan of the current run: what the page shows while it runs and when it ends."""

    state: StageState
    folder_id: int
    run_id: int
    last_event: ScanEvent | None
    receipt: ScanRunOut | None


PipelineAction = Literal["start", "stop", "resume"]


class PipelineStatus(BaseModel):
    worker: WorkerSnapshot
    scan: ScanProgress | None
    pending: dict[str, int] = Field(description="Per stage: how many frames are still missing.")
    action: PipelineAction = Field(
        description="The button's verb, decided here and not in the page: start / stop / resume."
    )


class WorkerOut(BaseModel):
    worker: WorkerSnapshot
