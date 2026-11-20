"""Which `weather_nights` row is a night's: the Nights, the history, the calendar and the criteria
join it the same way (Issue #16). Here, below both the spine and the weather, which never meet."""

# `w` is `weather_nights`, `n` is `nights`; the one parameter is the row's `kind`.
OF_THE_NIGHT = "w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?"
