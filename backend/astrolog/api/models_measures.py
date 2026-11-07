"""A frame's measures, ready for the screen: every one with its unit and group, its value or why
it has none (`docs/domini/misure.md`)."""

from typing import Literal

from pydantic import BaseModel, Field

from ..measure_list import Group, Silent, Unit

MeasureOutcome = Literal[
    "measured", "too_few_stars", "unreadable", "not_supported", "fz_unsupported"
]
SqmOutcome = Literal["measured", "calibration_failed", "no_altitude", "unreadable"]
Level = Literal["go", "marginal", "nogo"]
SamplingClassOut = Literal["severe_under", "under", "ideal", "over"]


class MeasureOut(BaseModel):
    key: str = Field(description="The measure's name, the same in the Selection's formula.")
    unit: Unit
    group: Group
    value: float | None
    silent: Silent | None = Field(description="Why `value` is null; null with a value.")


class FrameMeasuresOut(BaseModel):
    """What the three stages wrote for one frame; the words beside the numbers."""

    frame_id: int
    measure_outcome: MeasureOutcome | None = Field(description="Null: not measured yet.")
    solved: bool | None = Field(description="Null: the sky row is not written yet.")
    sqm_outcome: SqmOutcome | None = Field(
        description="Null: no sky brightness row; the measures say why (`sqm_pending`, ...)."
    )
    shape: Literal["fitted", "estimated", "unmeasurable"] | None
    tilt_level: Level | None = Field(
        description="ASTAP's tilt judged: up to 10% go, from 20% nogo (ADR 0044). software-ok"
    )
    sampling_class: SamplingClassOut | None = Field(description="FWHM in px, ADR 0022.")
    angle_axis: Literal["ra", "dec"] | None = Field(description="Stars' long axis on the sky.")
    measures: list[MeasureOut]
