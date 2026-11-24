"""Dew on exposed glass: Beysens 2016 (Atmos. Res. 167:146), Eq. 25, p. 12 of hal-04005956. Its
yield solved for the spread where it turns zero: under it, dew."""

import math

# Eq. 25's elevation polynomial, H in km: NREL pvdeg writes 1.04963*H**2, p. 12 prints H.
RADIATIVE_MM_DAY = 0.37  # [C Beysens 2016, Atmos. Res. 167:146, Eq. 25]
REFERENCE_K = 285.0  # [C Beysens 2016, Eq. 25: ((Td + 273.15) / 285)^4]
ELEVATION_LINEAR = 0.204323  # [C Beysens 2016, Eq. 25]
ELEVATION_SQUARE = 0.0238893  # [C Beysens 2016, Eq. 25]
DEW_POINT_BASE = 18.0132  # [C Beysens 2016, Eq. 25]
DEW_POINT_LINEAR = 1.04963  # [C Beysens 2016, Eq. 25, author copy p. 12: H, not H^2]
DEW_POINT_SQUARE = 0.21891  # [C Beysens 2016, Eq. 25]
CONVECTIVE_MM_DAY_K = 0.06  # [C Beysens 2016, Eq. 25: alpha' on (Td - Ta), mm/d/K]
CUTOFF_MS = 4.4  # [C Beysens 2016, Eq. 23: V0, wind at 10 m]
CUTOFF_POWER = 20  # [C Beysens 2016, Eq. 23]
CUTOFF_GAIN = 100  # [C Beysens 2016, Eq. 23: 101 beyond V0]
KELVIN = 273.15  # [C SI: 0 degC]
OKTAS = 8  # [C WMO: sky in eighths]
KMH_PER_MS = 3.6  # [C SI: 1 m/s = 3.6 km/h]


def _sky_factor(dew_point_c: float, elevation_km: float) -> float:
    """Eq. 25's first bracket: the clear sky's cooling against the site's height and humidity."""
    h = elevation_km
    on_dew = DEW_POINT_BASE - DEW_POINT_LINEAR * h + DEW_POINT_SQUARE * h**2
    return 1 + ELEVATION_LINEAR * h - ELEVATION_SQUARE * h**2 - on_dew * 1e-3 * dew_point_c


def threshold_c(
    dew_point_c: float | None,
    cloud_pct: float | None,
    wind_kmh: float | None,
    elevation_m: float | None,
) -> float | None:
    """The spread under which Eq. 25 gives dew; 0 under full overcast. No elevation: sea level."""
    if dew_point_c is None or cloud_pct is None or wind_kmh is None:
        return None
    oktas = cloud_pct * OKTAS / 100
    wind_ms = wind_kmh / KMH_PER_MS
    radiative = (
        RADIATIVE_MM_DAY
        * _sky_factor(dew_point_c, (elevation_m or 0.0) / 1000)
        * ((dew_point_c + KELVIN) / REFERENCE_K) ** 4
        * (1 - oktas / OKTAS)
    )
    convective = CONVECTIVE_MM_DAY_K * (
        1 + CUTOFF_GAIN * (1 - math.exp(-((wind_ms / CUTOFF_MS) ** CUTOFF_POWER)))
    )
    return max(0.0, radiative / convective)


def shown_threshold(spread_c: float | None, threshold: float | None) -> float | None:
    """To a tenth, on the side the spread sits: a spread under it never reads as over it."""
    if threshold is None:
        return None
    if spread_c is None:
        return round(threshold, 1)
    side = math.ceil if spread_c < threshold else math.floor
    return side(threshold * 10) / 10
