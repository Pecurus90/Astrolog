"""A night's measures, ready for the window of the night (`docs/domini/misure.md`): medians and
quartiles written by `night_measures.py`, the frames one by one as the pipeline wrote them."""

from typing import Literal

from pydantic import BaseModel, Field

from ..measure_list import Group, Unit

FrameState = Literal["measured", "estimated", "too_few_stars", "pending"]
TiltLevel = Literal["go", "marginal", "nogo"]
Sampling = Literal["severe_under", "under", "ideal", "over"]
MedianVerdict = Literal[TiltLevel, Sampling]


class MeasureStat(BaseModel):
    """One measure over a set of frames."""

    key: str = Field(description="The measure's name, as in a frame's measures.")
    unit: Unit
    group: Group
    measured: int = Field(description="Frames with a value: the median is over these.")
    median: float | None
    q1: float | None = Field(description="First quartile, type 7 (Hyndman & Fan 1996).")
    q3: float | None
    low: float | None = Field(description="The lowest value: one scale for every row.")
    high: float | None
    trend: list[float] | None = Field(
        description="24 medians along the night in shooting order, each over its stretch of "
        "frames; null under 4 values."
    )
    verdict: MedianVerdict | None = Field(
        description="The median judged by the frame's own rule: `hfd_tilt_pct` the tilt (ADR "
        "0044), `fwhm_px` the sampling (ADR 0022); null for the others."
    )
    silent: Literal["measuring", "no_value"] | None = Field(
        description="Why `median` is null: frames still to be measured, or none of the measured "
        "has it (each frame's reason is in its own measures). Null with a median."
    )
    per_filter: bool = Field(
        description="Background, noise or sky brightness from more than one filter: each filter "
        "has its own scale, so the set's median does not compare; show it per filter."
    )


class MeasureSet(BaseModel):
    """The night, an object, a filter, or an object in a filter: null is all of them."""

    object_key: str | None
    filter: str | None
    frames: int = Field(description="The set's frames, counted as the Nights page counts them.")
    pending: int = Field(description="Of those, still without measures.")
    differs: list[Literal["camera", "gain", "exposure"]] = Field(
        description="What changes among the measured frames: background and noise compare only "
        "when it is empty; the background per second also across exposures."
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
    start: str | None = Field(description="Start of the exposure in the site's zone, with its "
                              "offset; null: not read yet or not written by the file.")  # fmt: skip
    object_key: str | None
    filter: str | None
    state: FrameState = Field(
        description="`measured`, `estimated` (shape from the moments: the fit failed), "
        "`too_few_stars`, or `pending`: not measured yet, or unreadable now and tried again. "
        "A frame never to be measured (a program not read, a rewritten, broken or compressed "
        "file) is not here: it counts only in `frames` (Marco, 8/11)."
    )
    tilt_level: TiltLevel | None = Field(
        description="The tilt's verdict, from `hfd_tilt_pct` (ADR 0044); null without it."
    )
    sampling: Sampling | None = Field(
        description="The sampling from the FWHM in px; null without it."
    )
    angle_axis: Literal["ra", "dec"] | None = Field(
        description="The stars' long axis on the sky; null: round stars or not solved."
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
