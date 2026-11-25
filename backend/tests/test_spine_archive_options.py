"""Le voci dell'Archivio scritte da chi scrive (ADR 0048, passo 6.19): con nient'altro scelto la
pagina legge `archive_options`, purche' fresca; una scrittura su un suo ingresso la fa contare di
nuovo dalle pose, finche' il giro dopo non la riscrive. Le conte sono le stesse nei due casi."""

from dataclasses import replace

import pytest

from astrolog.catalog import load
from astrolog.spine import archive, archive_criteria
from astrolog.spine.archive_criteria import Key
from astrolog.spine.counts import Scope
from conftest import real_bundle
from perf_archive import build, write_archive
from test_spine_archive import oggetto
from test_spine_archive_mosaic import mosaico
from test_spine_archive_scope import banco, notte, riprese


def fresca(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM derived_fresh WHERE name = 'archive_options'"
    ).fetchone()[0]


def con_mosaico(conn, pezzi):
    ic405 = oggetto(conn, "IC 405", "ic-405")
    pose = riprese(conn, ic405, 2, notte_id=pezzi["agosto"], setup_id=pezzi["a"],
                   filtro=pezzi["ha"], secondi=300.0)  # fmt: skip
    mosaico(conn, pose)


@pytest.mark.parametrize(
    "criteria",
    [
        {},
        {"scope": Scope(years=("2025",))},
        {"filters": ("Ha",)},
        {"filters": ("Ha",), "constellations": ("And", "Cyg")},
        {"forms": ("one",), "types": ("galaxy", "nebula")},
        {"catalogs": ("NGC",)},
    ],
)
def test_the_written_options_are_the_counted_ones(archivio, criteria):
    """Stesse voci, righe e ordine: contate dai frame o lette da cio' che e' scritto."""
    con_mosaico(archivio, banco(archivio))
    base = archive.Criteria(**criteria)
    contate = archive_criteria.offered(archivio, base)

    archive_criteria.write(archivio)

    assert fresca(archivio) == 1
    assert archive_criteria.offered(archivio, base) == contate


def test_a_fresh_read_reads_what_is_written(archivio):
    """Con la tabella fresca, la lettura non conta: un numero scritto a mano si vede."""
    banco(archivio)
    archive_criteria.write(archivio)
    archivio.execute("UPDATE archive_options SET rows = 99 WHERE key = 'year' AND value = '2024'")

    offerti = archive_criteria.offered(archivio, archive.Criteria())
    anni = next(c for c in offerti if c["key"] == Key.YEAR)["options"]

    assert {o["value"]: o["rows"] for o in anni} == {"2025": 1, "2024": 99}


def test_a_criterion_with_another_chosen_is_still_counted(archivio):
    """Col 2025 scelto, le costellazioni si contano col 2025: quelle scritte sono senza."""
    banco(archivio)
    archive_criteria.write(archivio)
    archivio.execute("UPDATE archive_options SET rows = 99 WHERE key = 'constellation'")
    nel_2025 = archive.Criteria(scope=Scope(years=("2025",)))

    offerti = archive_criteria.offered(archivio, nel_2025)
    stelle = next(c for c in offerti if c["key"] == Key.CONSTELLATION)["options"]

    assert {o["value"]: o["rows"] for o in stelle} == {"And": 1, "Cyg": 0}


def _nuova_notte(conn, pezzi):
    riprese(conn, pezzi["ngc"], 1, notte_id=notte(conn, pezzi["casa"], "2023-03-01"),
            setup_id=pezzi["a"], filtro=pezzi["ha"], secondi=60.0)  # fmt: skip


SCRITTURE = {
    "una posa nuova": _nuova_notte,
    "una posa tolta": lambda c, p: c.execute("DELETE FROM frames WHERE object_id = ?", (p["ngc"],)),
    "una posa su un altro oggetto": lambda c, p: c.execute(
        "UPDATE frames SET object_id = ? WHERE object_id = ?", (p["m31"], p["ngc"])
    ),
    "un mosaico": con_mosaico,
    "un oggetto che cambia voce": lambda c, p: c.execute(
        "UPDATE objects SET catalog_slug = 'ic-405' WHERE id = ?", (p["ngc"],)
    ),
    "una notte che cambia data": lambda c, p: c.execute(
        "UPDATE nights SET night_date = '2023-08-02' WHERE id = ?", (p["agosto"],)
    ),
    "un setup che cambia camera": lambda c, p: c.execute(
        "UPDATE rigs SET camera_id = ? WHERE id = ?", (p["asi533"], p["a"])
    ),
    "un filtro rinominato": lambda c, p: c.execute(
        "UPDATE filters SET name = 'H-alpha' WHERE id = ?", (p["ha"],)
    ),
}


def test_a_catalog_loaded_again_makes_the_page_count_again(archivio):
    """Il catalogo si scrive solo intero, e segna `catalog_version` una volta: li' il trigger, non
    sulle 22.080 voci, che costerebbero il caricamento quattro volte (test_perf_catalog)."""
    banco(archivio)
    archivio.execute("UPDATE catalog_version SET version = 'di prima'")
    archive_criteria.write(archivio)

    assert load.load_catalog(archivio, real_bundle()) > 20000

    assert fresca(archivio) == 0


@pytest.mark.parametrize("scrittura", list(SCRITTURE))
def test_a_write_on_an_input_makes_the_page_count_again(archivio, scrittura):
    """Ogni ingresso toglie la freschezza: la pagina dice subito il nuovo, senza il giro."""
    pezzi = banco(archivio)
    archive_criteria.write(archivio)
    scritte = archive_criteria.offered(archivio, archive.Criteria())

    SCRITTURE[scrittura](archivio, pezzi)

    assert fresca(archivio) == 0
    dopo = archive_criteria.offered(archivio, archive.Criteria())
    assert dopo != scritte
    archive_criteria.write(archivio)
    assert archive_criteria.offered(archivio, archive.Criteria()) == dopo


def test_a_site_renamed_reads_at_once_from_the_written_options(archivio):
    """Il sito e' un id: il nome si legge in lettura, e la tabella resta fresca."""
    pezzi = banco(archivio)
    archive_criteria.write(archivio)

    archivio.execute("UPDATE sites SET name = 'Balcone' WHERE id = ?", (pezzi["casa"],))

    assert fresca(archivio) == 1
    offerti = archive_criteria.offered(archivio, replace(archive.Criteria()))
    siti = next(c for c in offerti if c["key"] == Key.SITE)["options"]
    assert [o["label"] for o in siti] == ["Balcone", "Deserto"]


def test_the_rounds_leave_the_options_written(db_path_col_catalogo, tmp_path):
    """Scansione, identificazione e notti vere: alla fine la tabella e' fresca, e dice le conte."""
    write_archive(tmp_path / "lib", 40)
    build(db_path_col_catalogo, tmp_path / "lib")
    from astrolog.db.connect import connect

    conn = connect(db_path_col_catalogo)
    try:
        assert fresca(conn) == 1
        lette = archive_criteria.offered(conn, archive.Criteria())
        conn.execute("DELETE FROM derived_fresh")
        assert archive_criteria.offered(conn, archive.Criteria()) == lette
    finally:
        conn.close()
