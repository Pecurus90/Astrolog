"""Le righe dell'Archivio scritte da chi scrive (ADR 0048, passo 6.19.1): con niente che restringe
le pose la pagina legge `archive_rows` e le tabelle accanto, purche' fresche; la stessa pagina,
contata dalle pose o letta, e' identica, e una scrittura su un ingresso la fa contare di nuovo."""

import pytest

from astrolog.api.archive import archive_page
from astrolog.spine import archive_criteria, search
from test_spine_archive import posa
from test_spine_archive_options import con_mosaico, fresca
from test_spine_archive_scope import banco, notte, riprese


def pagina(conn, **chiesto):
    """La risposta di GET /archive, come la serve la rotta."""
    vuoto = {"limit": 50, "offset": 0, "q": None, "key": None, "year": [], "type_": [],
             "constellation": [], "filter_name": [], "form": [], "site": [], "optics": [],
             "camera": [], "catalog": [], "sort": "name"}  # fmt: skip
    return archive_page(**(vuoto | chiesto), conn=conn).model_dump()


def completo(conn):
    """Il banco dei periodi, un mosaico, due pose senza oggetto (una senza filtro)."""
    pezzi = banco(conn)
    con_mosaico(conn, pezzi)
    posa(conn, None, filtro=pezzi["ha"], secondi=120.0)
    posa(conn, None, secondi=None)
    return pezzi


@pytest.mark.parametrize(
    "chiesto",
    [
        {},
        {"sort": "hours"},
        {"sort": "recent"},
        {"limit": 1, "offset": 1},
        {"q": "M"},
        {"year": ["2024"]},
        {"year": ["2024"], "sort": "hours"},
        {"filter_name": ["Ha"]},
        {"form": ["mosaic"]},
        {"catalog": ["NGC"]},
    ],
)
def test_the_written_page_is_the_counted_one(archivio, chiesto):
    """Righe, ore, produzioni, filtri, totali e pose senza oggetto: gli stessi, nello stesso
    ordine, contati dalle pose o letti da cio' che e' scritto."""
    completo(archivio)
    contata = pagina(archivio, **chiesto)

    archive_criteria.write(archivio)

    assert fresca(archivio) == 1
    assert pagina(archivio, **chiesto) == contata


def test_the_nights_of_a_searched_object_are_the_counted_ones(archivio):
    completo(archivio)
    contate = search.find(archivio, "M", 20)

    archive_criteria.write(archivio)

    assert search.find(archivio, "M", 20) == contate


def test_a_fresh_page_reads_what_is_written(archivio):
    """Con le tabelle fresche la pagina non conta: numeri scritti a mano si vedono."""
    completo(archivio)
    archive_criteria.write(archivio)
    for tabella in ("archive_rows", "archive_productions", "archive_row_filters"):
        archivio.execute(f"UPDATE {tabella} SET frames = 99")  # noqa: S608 - our tables
    archivio.execute("UPDATE archive_whole SET frames = 99, left_frames = 98")

    letta = pagina(archivio)

    assert {r["frames"] for r in letta["items"]} == {99}
    assert {p["frames"] for r in letta["items"] for p in r["productions"]} == {99}
    assert {f["frames"] for r in letta["items"] for f in r["filters"]} == {99}
    assert (letta["whole"]["frames"], letta["unresolved"]["frames"]) == (99, 98)


SCRITTURE = {
    "una posa nuova": lambda c, p: riprese(
        c, p["ngc"], 1, notte_id=notte(c, p["casa"], "2023-03-01"), setup_id=p["a"],
        filtro=p["ha"], secondi=60.0,
    ),
    "una posa che cambia durata": lambda c, p: c.execute(
        "UPDATE frames SET exposure_s = 30.0 WHERE object_id = ?", (p["ngc"],)
    ),
    "una posa che non e' piu' una luce": lambda c, p: c.execute(
        "UPDATE frames SET image_type = 'unknown' WHERE object_id IS NULL"
    ),
    "un nome principale nuovo": lambda c, p: c.execute(
        "UPDATE object_names SET name = 'Andromeda' WHERE object_id = ? AND is_primary = 1",
        (p["m31"],),
    ),
}  # fmt: skip


@pytest.mark.parametrize("scrittura", list(SCRITTURE))
def test_a_write_on_an_input_of_the_rows_makes_the_page_count_again(archivio, scrittura):
    """Gli ingressi che le voci non leggevano e le righe si': durata, tipo, nome dell'oggetto."""
    pezzi = completo(archivio)
    archive_criteria.write(archivio)
    scritta = pagina(archivio)

    SCRITTURE[scrittura](archivio, pezzi)

    assert fresca(archivio) == 0
    dopo = pagina(archivio)
    assert dopo != scritta
    archive_criteria.write(archivio)
    assert pagina(archivio) == dopo


def test_an_instrument_renamed_reads_at_once_from_the_written_rows(archivio):
    """Ottica e camera sono id: il nome si legge in lettura, e le righe restano fresche."""
    pezzi = completo(archivio)
    archive_criteria.write(archivio)

    archivio.execute("UPDATE instruments SET name = 'Il rifrattore' WHERE id = ?",
                     (pezzi["rifrattore"],))  # fmt: skip

    assert fresca(archivio) == 1
    ottiche = {p["optics"] for r in pagina(archivio)["items"] for p in r["productions"]}
    assert "Il rifrattore" in ottiche
