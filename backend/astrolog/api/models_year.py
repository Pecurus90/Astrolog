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


class YearMonthOut(BaseModel):
    month: int = Field(ge=1, le=12)  # [T] calendar months
    integration_s: int
    previous_s: int = Field(description="The same whole month of the year before.")
    bar: float = Field(
        ge=0, le=1, description="The bar's height: 1 is the fullest month of both years."
    )
    previous_bar: float = Field(ge=0, le=1, description="As `bar`, for the year before.")
    current: bool
    future: bool = Field(description="After the current month: nothing to count yet.")


class YearFilterOut(BaseModel):
    name: str = Field(description="The name you gave it, or the one the files carried.")
    passband: str = Field(description="The canonical passband: it is what gives the colour.")
    integration_s: int
    share_pct: int = Field(description="Of the year's `integration_s`, rounded.")


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
    months: list[YearMonthOut] = Field(description="January to December.")
    previous_same_period_s: int = Field(
        description="The year before from January 1 to the same day (February 29 on the 28th)."
    )
    filters: list[YearFilterOut] = Field(description="The year's filters, the most shot first.")
    no_filter_s: int = Field(description="The frames naming no filter, outside `filters`.")
    no_filter_pct: int
