"""L'ultimo tentativo di una fonte meteo per un sito, e com'e' andato (`weather_fetches`).

Vincolo non ovvio: **serve alle fonti che non devono ripetersi troppo spesso** -- Meteoblue per i
crediti, lo storico per non martellare l'archivio dopo un rifiuto -- e sta scritto, non in memoria,
cosi' un riavvio non fa ripartire le chiamate da capo.
"""

from ..clock import iso_z, parse_iso


def last(conn, site_id, source):
    return conn.execute(
        "SELECT attempted_at, status FROM weather_fetches WHERE site_id = ? AND source = ?",
        (site_id, source),
    ).fetchone()


def record(conn, site_id, source, status, adesso):
    conn.execute(
        "INSERT INTO weather_fetches(site_id, source, attempted_at, status) VALUES(?, ?, ?, ?)"
        " ON CONFLICT(site_id, source) DO UPDATE SET attempted_at = excluded.attempted_at,"
        " status = excluded.status",
        (site_id, source, iso_z(adesso), status),
    )


def age(ultimo, adesso):
    """Quanto tempo e' passato dal tentativo: una `timedelta`."""
    return adesso - parse_iso(ultimo["attempted_at"])
