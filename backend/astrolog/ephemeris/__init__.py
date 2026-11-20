"""What the sky does from a site at a moment, always offline (contract: docs/domini/effemeridi.md).
Skyfield on JPL DE421 from the skyfield-data wheel, no download ever (ADR 0046)."""

from ..twilight import ASTRO_DEG as ASTRO_DEG  # read here by the ephemeris and its callers
from ..twilight import CIVIL_DEG as CIVIL_DEG
from ..twilight import NAUTICAL_DEG as NAUTICAL_DEG
from ..twilight import RISESET_DEG as RISESET_DEG

# Crossings are interpolated, so the step sets how dense the search is, not the error. [T]
GRID_STEP_MIN = 3

# [T] drawn curve needs far fewer points than the search. Multiple of GRID_STEP_MIN: the stride
# is an integer division, so the points would drift off the step.
TRACK_STEP_MIN = 15

# The Moon calendar counts dark hours on samples: two months of nights in one call per body. [T]
CALENDAR_STEP_MIN = 5

# Mean synodic month: the age's scale. [C Meeus, Astronomical Algorithms, 2nd ed., ch. 49]
SYNODIC_MONTH_DAYS = 29.530588861

# Upper bound, rounded up: a bound too low clips the curve.
# [C lunar standstill: declination up to 28.725 degrees, Wikipedia "Lunar standstill"]
MAX_DECLINATION_DEG = 28.8

# The night chart's ceiling rises in round ticks, so nearby sites share the same scale. [T]
CEILING_STEP_DEG = 15
