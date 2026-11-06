"""Where the Sun is at each twilight's end, alone: the ephemeris and the new pipeline both read it,
and the pipeline may not load astropy (ADR 0030)."""

# Rise/set altitude: refraction 34' + apparent radius 16' = 50', for the Moon too.
# [C USNO RST_defs: Sun's centre at zenith distance 90.8333]
RISESET_DEG = -0.833

# Geometric altitude of the Sun's centre at the end of each twilight.
# [C USNO https://aa.usno.navy.mil/faq/RST_defs: 6, 12, 18 degrees below the horizon]
CIVIL_DEG = -6.0
NAUTICAL_DEG = -12.0  # [C USNO]
ASTRO_DEG = -18.0  # [C USNO]
