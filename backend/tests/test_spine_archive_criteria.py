"""I nove criteri dell'Archivio (tavola v78, `Archivio.dc.html` 139-148): piu' voci di un criterio
fanno passare chi ne ha una, criteri diversi valgono tutti, e ogni voce dice quante righe darebbe
con le altre scelte accese. La regola e' una sola (`archive._where`): le conte la riusano, e una
prova qui le confronta con la pagina che ogni voce darebbe."""

from dataclasses import replace

import pytest

from astrolog.spine import archive, archive_criteria
from astrolog.spine.archive_criteria import Key
from astrolog.spine.counts import Scope
from test_spine_archive import nomi, oggetto, posa
from test_spine_archive_mosaic import mosaico
from test_spine_archive_scope import banco, notte, riprese


def pagina(conn, **criteri):
    righe, quanti = archive.page(conn, limit=50, offset=0, **criteri)
    return set(nomi(righe)), quanti


def voci(conn, chiave, criteria=None):
    """`{voce: righe}` del criterio `chiave`, o `None` se il criterio non si offre."""
    offerti = archive_criteria.offered(conn, criteria or archive.Criteria())
    for c in offerti:
        if c["key"] == chiave:
            return {o["value"]: o["rows"] for o in c["options"]}
    return None


def test_two_choices_of_one_criterion_are_either(archivio):
    """Casa o deserto: passa chi e' stato ripreso in uno dei due."""
    pezzi = banco(archivio)

    assert pagina(archivio, scope=Scope(sites=(pezzi["casa"], pezzi["deserto"]))) == (
        {"M 31", "NGC 7000"},
        2,
    )
    assert pagina(archivio, constellations=("And", "Cyg"))[1] == 2
    assert pagina(archivio, scope=Scope(years=("2024", "2025")))[1] == 2


def test_two_years_are_either(archivio):
    """Due anni insieme: ogni riga dice le ore dei due, e solo quelle."""
    banco(archivio)
    oggetto_vecchio = oggetto(archivio, "M 13", "m-13")
    nel_2023 = notte(archivio, 1, "2023-05-01")
    riprese(archivio, oggetto_vecchio, 1, notte_id=nel_2023, corredo_id=None, filtro=None,
            secondi=60.0)  # fmt: skip

    righe, quanti = archive.page(archivio, limit=50, offset=0, scope=Scope(years=("2023", "2025")))

    assert quanti == 2
    assert {n: r["frames"] for n, r in zip(nomi(righe), righe, strict=True)} == {
        "M 13": 1,
        "M 31": 5,
    }


def test_two_criteria_hold_together(archivio):
    """Cygnus nel 2025: NGC 7000 e' solo del 2024, quindi niente."""
    banco(archivio)

    assert pagina(archivio, constellations=("Cyg",), scope=Scope(years=("2025",))) == (set(), 0)


def test_each_option_counts_the_rows_with_the_other_choices(archivio):
    """Col 2025 acceso Cygnus resta in elenco a zero, e gli anni contano senza se stessi."""
    banco(archivio)
    nel_2025 = archive.Criteria(scope=Scope(years=("2025",)))

    assert voci(archivio, Key.CONSTELLATION) == {"And": 1, "Cyg": 1}
    assert voci(archivio, Key.CONSTELLATION, nel_2025) == {"And": 1, "Cyg": 0}
    assert voci(archivio, Key.YEAR, nel_2025) == {"2025": 1, "2024": 2}
    scelto = next(c for c in archive_criteria.offered(archivio, nel_2025) if c["key"] == Key.YEAR)
    assert [(o["value"], o["chosen"]) for o in scelto["options"]] == [
        ("2025", True),
        ("2024", False),
    ]


def _con(criteria: archive.Criteria, chiave: Key, voce: str) -> archive.Criteria:
    return archive_criteria.choosing(criteria, chiave, (voce,))


@pytest.mark.parametrize(
    "criteria",
    [
        {},
        {"scope": Scope(years=("2025",))},
        {"filters": ("Ha",), "constellations": ("And", "Cyg")},
        {"forms": ("one",), "types": ("galaxy", "nebula")},
        {"filters": ("Ha",), "forms": ("several", "mosaic")},
        {"forms": ("one",), "scope": Scope(years=("2024",))},
        {"filters": ("Lum",), "scope": Scope(years=("2024", "2025"))},
    ],
)
@pytest.mark.parametrize("con_mosaico", [False, True])
def test_an_option_count_is_the_page_it_would_give(archivio, criteria, con_mosaico):
    """La conta di ogni voce e' il totale della pagina con quella voce al posto di quelle del suo
    criterio: due regole che dicono la stessa cosa a modo loro un giorno divergono. Le voci dei
    frame si contano in una passata sola, filtro e forma compresi: anche loro si confrontano."""
    pezzi = banco(archivio)
    if con_mosaico:
        ic405 = oggetto(archivio, "IC 405", "ic-405")
        pose = riprese(archivio, ic405, 2, notte_id=pezzi["agosto"], corredo_id=pezzi["a"],
                       filtro=pezzi["ha"], secondi=300.0)  # fmt: skip
        mosaico(archivio, pose)
    base = archive.Criteria(**criteria)
    controllate = 0

    for criterio in archive_criteria.offered(archivio, base):
        for voce in criterio["options"]:
            scelto = _con(base, criterio["key"], voce["value"])
            _, quanti = archive.page(archivio, limit=1, offset=0, **vars(scelto))
            assert voce["rows"] == quanti, (criterio["key"], voce["value"])
            controllate += 1

    assert controllate > 10, pezzi


def test_you_can_narrow_down_to_a_kind_of_object(archivio):
    """La famiglia, non il codice: NGC 7000 e' una nebulosa a emissione, e sta fra le nebulose."""
    banco(archivio)

    assert pagina(archivio, types=("galaxy",)) == ({"M 31"}, 1)
    assert pagina(archivio, types=("nebula",)) == ({"NGC 7000"}, 1)
    assert pagina(archivio, types=("unknown",)) == ({"Il campo dietro casa"}, 1)
    assert voci(archivio, Key.TYPE) == {"galaxy": 1, "nebula": 1, "unknown": 1}


def test_you_can_narrow_down_by_how_many_productions(archivio):
    """M 31 ha due setup, NGC 7000 uno; nel 2024 M 31 ha solo il primo, e le produzioni sono
    quelle dei frame chiesti."""
    banco(archivio)

    assert pagina(archivio, forms=("several",)) == ({"M 31"}, 1)
    assert pagina(archivio, forms=("one",)) == ({"NGC 7000"}, 1)
    assert pagina(archivio, forms=("one",), scope=Scope(years=("2024",))) == (
        {"M 31", "NGC 7000"},
        2,
    )
    # nessun mosaico: la voce non c'e', e il criterio con due voci si'
    assert voci(archivio, Key.FORM) == {"one": 1, "several": 1}


def test_the_choices_offer_the_years_sites_and_pieces_you_shot_with(archivio):
    """Gli anni dal piu' recente, siti e pezzi col nome; un pezzo mai usato non si offre."""
    pezzi = banco(archivio)
    from group_bench import attrezzo

    attrezzo(archivio, "camera", "Nel cassetto")
    offerti = {
        c["key"]: c["options"] for c in archive_criteria.offered(archivio, archive.Criteria())
    }

    assert [o["value"] for o in offerti[Key.YEAR]] == ["2025", "2024"]
    assert [(o["value"], o["label"]) for o in offerti[Key.SITE]] == [
        (str(pezzi["casa"]), "Casa"),
        (str(pezzi["deserto"]), "Deserto"),
    ]
    assert [o["label"] for o in offerti[Key.OPTICS]] == ["Newton", "Rifrattore"]
    assert [o["label"] for o in offerti[Key.CAMERA]] == ["ASI2600", "ASI533"]
    # bande fuori vocabolario: vanno per nome (l'ordine dei filtri: test_filter_order)
    assert [(o["value"], o["passband"]) for o in offerti[Key.FILTER]] == [
        ("Ha", "ha"),
        ("Lum", "l"),
    ]


def test_one_site_or_one_camera_is_not_a_choice(archivio):
    """Con una voce sola, sceglierla non stringe niente: il criterio non c'e'."""
    m31 = oggetto(archivio, "M 31", "m-31")
    posa(archivio, m31)

    offerti = {c["key"] for c in archive_criteria.offered(archivio, archive.Criteria())}

    assert offerti == set()


def test_a_chosen_option_stays_even_alone(archivio):
    """Una voce scelta resta in elenco anche se sola, o non si potrebbe togliere."""
    m31 = oggetto(archivio, "M 31", "m-31")
    posa(archivio, m31)

    scelto = replace(archive.Criteria(), catalogs=("NGC",))

    assert voci(archivio, Key.CATALOG, scelto) == {"M": 1, "NGC": 0}


def test_by_hours_and_by_the_latest_night_are_two_different_orders(archivio):
    """Per integrazione M 31 sta davanti; dai piu' recenti M 13, ripreso a settembre per un
    minuto. Chi non ha notti va in fondo."""
    banco(archivio)
    m13 = oggetto(archivio, "M 13", "m-13")
    settembre = notte(archivio, 1, "2025-09-01")
    riprese(archivio, m13, 1, notte_id=settembre, corredo_id=None, filtro=None, secondi=60.0)

    per_ore, _ = archive.page(archivio, limit=50, offset=0, sort=archive.Order.HOURS)
    recenti, _ = archive.page(archivio, limit=50, offset=0, sort=archive.Order.RECENT)

    assert nomi(per_ore) == ["M 31", "NGC 7000", "M 13", "Il campo dietro casa"]
    assert nomi(recenti) == ["M 13", "M 31", "NGC 7000", "Il campo dietro casa"]


def test_the_totals_are_the_whole_archive_whatever_the_bar_says(archivio):
    """La testa dice tutto l'archivio: tre righe, dieci frame, un'ora e mezza, tre notti."""
    banco(archivio)

    assert archive.totals(archivio) == {
        "rows": 3,
        "mosaics": 0,
        "frames": 10,
        "integration_s": 5400.0,
        "untimed": 0,
        "nights": 3,
    }


def test_the_frames_without_an_object_are_counted_apart(archivio):
    """I frame di luce che nessun oggetto ha preso, copie escluse, con i loro filtri; senza,
    niente carta."""
    banco(archivio)
    assert archive.unresolved(archivio) is None
    soli = [posa(archivio, None, secondi=120.0) for _ in range(2)]
    archivio.execute("UPDATE frames SET exposure_s = NULL WHERE id = ?", (soli[1],))
    archivio.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (soli[0], posa(archivio, None)))
    archivio.execute(
        "UPDATE frames SET filter_id = (SELECT id FROM filters WHERE name = 'Ha') WHERE id = ?",
        (soli[0],),
    )

    fuori = archive.unresolved(archivio)

    assert fuori is not None
    assert (fuori["frames"], fuori["integration_s"], fuori["untimed"]) == (2, 120.0, 1)
    assert [(f["name"], f["frames"]) for f in fuori["filters"]] == [("Ha", 1)]
