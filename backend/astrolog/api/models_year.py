from typing import Literal

from pydantic import BaseModel, Field

# Repeated rather than imported from `spine.year`, as the other route contracts do.
HeatLevel = Literal["future", "none", "under2", "2to4", "4to6", "over6"]


class YearDayOut(BaseModel):
    date: str = Field(description="`YYYY-MM-DD`, a night date.")
    level: HeatLevel = Field(
        description="`future` after today; `none` without hours; then the board's legend: under "
        "2 h, 2-4, 4-6, over 6."
    )
    integration_s: int


class YearOut(BaseModel):
    """The year so far: what the Dashboard's year section shows, already counted."""

    year: int
    until: str = Field(description="Today's night date, the last day counted.")
    nights: int
    integration_s: int
    per_night_s: int | None = Field(description="`None` without nights, never 0 in its place.")
    per_month: float = Field(description="Nights per elapsed month, to one decimal.")
    lead_blank: int = Field(
        description="Empty squares before January 1 in a Monday-first week grid (0-6)."
    )
    days: list[YearDayOut] = Field(description="Every day of the year, January 1 first.")
