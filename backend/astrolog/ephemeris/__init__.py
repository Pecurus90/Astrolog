"""What the sky does from a site at a moment, always offline (contract: docs/domini/effemeridi.md).
Importing the package switches off astropy's network access, deliberately for everything inside."""

from astropy.coordinates import solar_system_ephemeris
from astropy.utils import iers

# Both together: without auto_max_age astropy raises on a future date instead of using its
# bundled tables, and the app runs on a NAS or a laptop with no network.
iers.conf.auto_download = False
iers.conf.auto_max_age = None
solar_system_ephemeris.set("builtin")

# Rise/set altitude: refraction 34' + apparent radius 16' = 50', the Nautical Almanac convention,
# for the Moon too.
RISESET_DEG = -0.833

# Geometric altitude of the Sun's centre at the end of each twilight, as defined by the USNO
# (https://aa.usno.navy.mil/faq/RST_defs).
CIVIL_DEG = -6.0
NAUTICAL_DEG = -12.0
ASTRO_DEG = -18.0

# Crossings are interpolated, so the step sets how dense the search is, not the error.
GRID_STEP_MIN = 3

# The drawn curve needs far fewer points than the search. Must stay a multiple of GRID_STEP_MIN:
# the stride is an integer division, so the points would drift off the step.
TRACK_STEP_MIN = 15

# An upper bound, rounded up: at the major lunistice the Moon's declination exceeds the 28.58 sum
# of the mean inclinations, and a bound too low clips the curve.
MAX_DECLINATION_DEG = 28.8

# The night chart's ceiling rises in round ticks, so nearby sites share the same scale.
CEILING_STEP_DEG = 15
