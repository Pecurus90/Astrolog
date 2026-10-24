"""What the sky does from a site at a moment, always offline (contract: docs/domini/effemeridi.md).
Importing the package switches off astropy's network access, deliberately for everything inside."""

from astropy.coordinates import solar_system_ephemeris
from astropy.utils import iers

# Both together: without auto_max_age astropy raises on a future date instead of using its
# bundled tables, and the app runs on a NAS or a laptop with no network.
iers.conf.auto_download = False
iers.conf.auto_max_age = None
solar_system_ephemeris.set("builtin")

# Rise/set altitude: refraction 34' + apparent radius 16' = 50', for the Moon too.
# [C USNO RST_defs: Sun's centre at zenith distance 90.8333]
RISESET_DEG = -0.833

# Geometric altitude of the Sun's centre at the end of each twilight.
# [C USNO https://aa.usno.navy.mil/faq/RST_defs: 6, 12, 18 degrees below the horizon]
CIVIL_DEG = -6.0
NAUTICAL_DEG = -12.0
ASTRO_DEG = -18.0

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
