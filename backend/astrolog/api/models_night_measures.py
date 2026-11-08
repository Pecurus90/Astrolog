"""A night's measures, ready for the window of the night (`docs/domini/misure.md`): medians and
quartiles written by `night_measures.py`, the frames one by one as the pipeline wrote them."""

from typing import Literal

from pydantic import BaseModel, Field

from ..measure_list import Group, Unit

FrameState = Literal[
    "measured", "estimated", "too_few_stars", "unreadable", "not_supported", "fz_unsupported",
    "rewritten", "broken", "pending",
]  # fmt: skip


class MeasureStat(BaseModel):
    """One measure over a set of frames."""

    key: str = Field(description="The measure's name, as in a frame's measures.")
    unit: Unit
    group: Group
    measured: int = Field(description="Frames with a value: the median is over these.")
    median: float | None
    q1: float | None = Field(description="First quartile, type 7 (Hyndman & Fan 1996).")
    q3: float | None
    bins: list[int] | None = Field(
        description="24 counts from the least to the most value; null under two different values."
    )
    silent: Literal["measuring", "no_value"] | None = Field(
        description="Why `median` is null: frames still to be measured, or none of the measured "
        "has it (each frame's reason is in its own measures). Null with a median."
    )


class MeasureSet(BaseModel):
    """The night, an object, a filter, or an object in a filter: null is all of them."""

    object_key: str | None
    filter: str | None
    frames: int = Field(description="The set's frames, counted as the Nights page counts them.")
    pending: int = Field(description="Of those, still without measures.")
    comparable: bool = Field(
        description="One camera, gain and exposure among the measured: background and noise "
        "compare. False: they do not."
    )
    measures: list[MeasureStat] = Field(description="Every measure, in the catalogue's order.")


class MeasuredObject(BaseModel):
    key: str = Field(description="The stable key, the same as the Nights'.")
    name: str | None
    frames: int
    pending: int


class MeasuredFilter(BaseModel):
    name: str
    passband: str
    frames: int


class MeasuredFrame(BaseModel):
    """One frame of the night, in shooting order."""

    frame_id: int
    start: str | None = Field(description="Start of the exposure, UTC with its offset; null: "
                              "not read yet or not written by the file.")  # fmt: skip
    object_key: str | None
    filter: str | None
    state: FrameState = Field(
        description="`measured`, `estimated` (shape from the moments: the fit failed), "
        "`too_few_stars`, the file's own failure, `not_supported`/`rewritten`/`broken` (never "
        "measured: a program the new pipeline does not read, a rewritten or broken file), or "
        "`pending`: not measured yet."
    )
    values: dict[str, float] = Field(
        description="Measure -> value, only those it has; why one is missing: the frame's measures."
    )


class NightMeasures(BaseModel):
    night_id: int
    timezone: str | None = Field(description="The site's zone: the times read in it.")
    frames: int
    pending: int
    objects: list[MeasuredObject]
    filters: list[MeasuredFilter] = Field(description="In the app's one filter order.")
    sets: list[MeasureSet] = Field(
        description="Empty until the measures of the nights are written after a scan."
    )
    series: list[MeasuredFrame]
