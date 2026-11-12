from pydantic import BaseModel, Field

from ..spine.year import RowKind


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
    share_pct: int = Field(description="Of the year's `integration_s`, whole: they add up to 100.")
    ring_from: float = Field(
        ge=0,
        le=100,  # [T] percent
        description="Where its piece of the ring starts, in %.",
    )
    ring_to: float = Field(
        ge=0,
        le=100,  # [T] percent
        description="Where it ends: the next one starts here, the last ends at 100.",
    )


class YearFilterRowOut(BaseModel):
    kind: RowKind = Field(
        description="`filter` one filter; `others` the filters past the fourth, when more than "
        "five have a name; `no_filter` the frames naming none."
    )
    name: str = Field(description="As `YearFilterOut.name`; empty for `others`.")
    passbands: list[str] = Field(description="One per filter in the row: the dot's colours.")
    integration_s: int
    share_pct: int = Field(description="Of the year's `integration_s`: the rows add up to 100.")
    count: int = Field(ge=1, description="Filters in the row: N of 'altri N filtri'.")


class YearOut(BaseModel):
    """The year so far: what the Dashboard's year section shows, already counted."""

    year: int
    until: str = Field(description="Today's night date, the last day counted.")
    nights: int
    integration_s: int
    per_night_s: int | None = Field(description="`None` without nights, never 0 in its place.")
    per_month: float = Field(description="Nights per elapsed month, to one decimal.")
    months: list[YearMonthOut] = Field(description="January to December.")
    previous_same_period_s: int = Field(
        description="The year before from January 1 to the same day (February 29 on the 28th)."
    )
    previous_known: bool = Field(
        description="The year before has nights: without, neither dashed bars nor comparison."
    )
    vs_previous_s: int = Field(
        description="`integration_s` less `previous_same_period_s`: negative when behind."
    )
    filters: list[YearFilterOut] = Field(
        description="The year's filters, the most shot first; the frames naming none last, as "
        "`__no_filter__` of band `UNKNOWN`. Empty without hours. The ring draws these."
    )
    rows: list[YearFilterRowOut] = Field(
        description="The list beside the ring, at most six rows (board v81): past five named "
        "filters the first four and one `others`, then `no_filter`. Empty without hours."
    )
