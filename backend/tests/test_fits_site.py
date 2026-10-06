"""Il sito scritto nell'header: in ogni forma in cui un programma lo scrive, e con la longitudine
fra -180 e 180. La regola e la sua fonte stanno in `fits/header_coords.site`.
"""

import pytest

from astrolog.fits.header_fields import extract_fields

# (nome, header, (latitudine, longitudine) attese). Coordinate tonde e inventate: non sono i
# posti di nessuno.
SITI = [
    ("in gradi decimali", {"SITELAT": 45.5, "SITELONG": 9.5}, (45.5, 9.5)),
    # la stessa forma di OBJCTDEC: gradi, minuti e secondi separati da spazi
    ("gradi-minuti-secondi, sud e ovest", {"SITELAT": "-30 15 00", "SITELONG": "-70 45 00"},
     (-30.25, -70.75)),
    ("gradi-minuti-secondi, est", {"SITELAT": "-37 30 00", "SITELONG": "145 30 00"},
     (-37.5, 145.5)),
    # la longitudine contata da 0 a 360 verso est e' la stessa, riportata fra -180 e 180
    ("longitudine da 0 a 360", {"SITELAT": 45.5, "SITELONG": 350.0}, (45.5, -10.0)),
    ("360 e' Greenwich", {"SITELAT": 51.5, "SITELONG": 360.0}, (51.5, 0.0)),
    ("180 resta 180", {"SITELAT": -17.5, "SITELONG": 180.0}, (-17.5, 180.0)),
    ("oltre 360 non e' una longitudine", {"SITELAT": 45.5, "SITELONG": 400.0}, (45.5, None)),
]  # fmt: skip


@pytest.mark.parametrize("header, atteso", [c[1:] for c in SITI], ids=[c[0] for c in SITI])
def test_the_site_is_read_in_every_written_form(header, atteso):
    """Il sito si scrive in gradi decimali o in gradi-minuti-secondi, e si leggono tutte e due:
    senza, si perde la domanda su dove sono state riprese quelle pose."""
    m = extract_fields(header, "x")
    lat, lon = atteso
    assert m.site_lat == pytest.approx(lat)
    assert m.site_lon == (None if lon is None else pytest.approx(lon))
