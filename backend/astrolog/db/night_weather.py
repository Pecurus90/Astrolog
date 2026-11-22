"""Which `weather_nights` row is a night's: the Nights, the history, the calendar and the criteria
join it the same way (Issue #16). Here, below both the spine and the weather, which never meet."""

# `w` is `weather_nights`, `n` is `nights`; the one parameter is the row's `kind`.
OF_THE_NIGHT = "w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?"

# `n` is `nights`: refused alone on enough days, asked no more.
# [T] three different days: not a bad afternoon of the service
GIVEN_UP = (
    "EXISTS (SELECT 1 FROM weather_missing g WHERE g.site_id = n.site_id"
    " AND g.night_date = n.night_date AND g.failed_days >= 3)"
)
