"""La barra dell'Archivio stringe anche per **periodo, ottica, camera e sito**, e allora la riga
dice cio' che hai chiesto: stringendo al 2025, M 31 porta le ore del 2025, non quelle di sempre
(Marco, 7/10/2026). Il periodo si legge sulla **notte**, che va da mezzogiorno a mezzogiorno nel
fuso del sito: una posa delle due di notte del primo gennaio sta nella notte del 31 dicembre.
"""

from astrolog.clock import now_iso
from astrolog.spine import archive, filters_used
from astrolog.spine.counts import Scope, Subject
from group_bench import ARIZONA, attrezzo, luogo
from group_bench import filtro as nasce_filtro
from test_spine_archive import nomi, oggetto, posa
from test_spine_archive_mosaic import CHIAVE, mosaico


def notte(conn, sito, data):
    return conn.execute(
        "INSERT INTO nights(site_id, night_date, created_at) VALUES(?, ?, ?)",
        (sito, data, now_iso()),
    ).lastrowid


def corredo(conn, ottica, camera):
    return conn.execute(
        "INSERT INTO rigs(optics_id, camera_id, detected, created_at) VALUES(?, ?, 1, ?)",
        (ottica, camera, now_iso()),
    ).lastrowid


def riprese(conn, oggetto_id, quante, *, notte_id, corredo_id, filtro, secondi):
    ids = [posa(conn, oggetto_id, filtro=filtro, secondi=secondi) for _ in range(quante)]
    conn.executemany(
        "UPDATE frames SET night_id = ?, rig_id = ? WHERE id = ?",
        [(notte_id, corredo_id, i) for i in ids],
    )
    return ids


def banco(conn):
    """Due oggetti, due siti, due corredi, tre notti. Per ore M 31 sta davanti (3600 s contro
    1800), ma nel 2024 no (600 contro 1800): cosi' l'ordine dice se guarda le ore ristrette."""
    casa, deserto = luogo(conn), luogo(conn, ARIZONA, casa=False)
    rifrattore, newton = attrezzo(conn, "optics", "Rifrattore"), attrezzo(conn, "optics", "Newton")
    asi2600, asi533 = attrezzo(conn, "camera", "ASI2600"), attrezzo(conn, "camera", "ASI533")
    a, b = corredo(conn, rifrattore, asi2600), corredo(conn, newton, asi533)
    novembre, gennaio = notte(conn, casa, "2024-11-10"), notte(conn, casa, "2025-01-15")
    agosto = notte(conn, deserto, "2025-08-02")
    ha, lum = nasce_filtro(conn, "Ha", "ha"), nasce_filtro(conn, "Lum", "l")
    m31, ngc = oggetto(conn, "M 31", "m-31"), oggetto(conn, "NGC 7000", "ngc-7000")
    riprese(conn, m31, 2, notte_id=novembre, corredo_id=a, filtro=lum, secondi=300.0)
    riprese(conn, m31, 1, notte_id=gennaio, corredo_id=b, filtro=ha, secondi=600.0)
    riprese(conn, m31, 4, notte_id=agosto, corredo_id=a, filtro=ha, secondi=600.0)
    riprese(conn, ngc, 3, notte_id=novembre, corredo_id=a, filtro=ha, secondi=600.0)
    # mai ripreso: senza filtri c'e', con un filtro sulle pose non ha niente da far passare
    oggetto(conn, "Il campo dietro casa")
    return {
        "casa": casa, "deserto": deserto, "rifrattore": rifrattore, "newton": newton,
        "asi2600": asi2600, "asi533": asi533, "m31": m31, "ngc": ngc,
    }  # fmt: skip


def ore(righe):
    return {n: (r["frames"], r["integration_s"]) for n, r in zip(nomi(righe), righe, strict=True)}


def stretto(conn, **scope):
    righe, quanti = archive.page(conn, limit=50, offset=0, scope=Scope(**scope))
    return ore(righe), quanti


def test_a_period_keeps_the_rows_shot_in_it_with_their_hours_in_it(archivio):
    """La domanda e' "quanto ho fatto nel 2025": M 31 dice le sue cinque pose del 2025, non le
    sette di sempre, e NGC 7000, ripresa solo nel 2024, non c'e'."""
    banco(archivio)

    assert stretto(archivio, since="2025-01-01", until="2025-12-31") == (
        {"M 31": (5, 3000.0)},
        1,
    )
    assert stretto(archivio, since="2024-01-01", until="2024-12-31") == (
        {"M 31": (2, 600.0), "NGC 7000": (3, 1800.0)},
        2,
    )


def test_a_period_can_straddle_the_new_year(archivio):
    """Una stagione invernale va da novembre a febbraio: un anno solo non la dice."""
    banco(archivio)

    assert stretto(archivio, since="2024-11-01", until="2025-02-28") == (
        {"M 31": (3, 1200.0), "NGC 7000": (3, 1800.0)},
        2,
    )


def test_the_period_reads_the_night_not_the_clock(archivio):
    """Le due di notte del primo gennaio sono la notte del 31 dicembre: chi chiede il 2025 non la
    vuole. Si guarda `nights.night_date`, che porta il fuso del sito, non `date_obs`."""
    pezzi = banco(archivio)
    capodanno = notte(archivio, pezzi["casa"], "2024-12-31")
    ngc = pezzi["ngc"]
    ids = riprese(archivio, ngc, 1, notte_id=capodanno, corredo_id=None, filtro=None, secondi=60.0)
    archivio.execute("UPDATE frames SET date_obs = '2025-01-01T01:00:00Z' WHERE id = ?", ids)

    assert "NGC 7000" not in stretto(archivio, since="2025-01-01", until="2025-12-31")[0]


def test_you_can_narrow_down_to_one_optics_or_one_camera(archivio):
    """Ottica e camera, ognuna da sola: "con il Newton" e "con la ASI2600" sono due domande."""
    pezzi = banco(archivio)

    assert stretto(archivio, optics=pezzi["newton"]) == ({"M 31": (1, 600.0)}, 1)
    assert stretto(archivio, camera=pezzi["asi2600"]) == (
        {"M 31": (6, 3000.0), "NGC 7000": (3, 1800.0)},
        2,
    )


def test_you_can_narrow_down_to_one_site(archivio):
    pezzi = banco(archivio)

    assert stretto(archivio, site=pezzi["deserto"]) == ({"M 31": (4, 2400.0)}, 1)


def test_the_narrowings_hold_on_the_same_pose(archivio):
    """Casa **e** ASI533 e' la posa di gennaio, non "M 31 ha pose a casa e pose con la ASI533"."""
    pezzi = banco(archivio)

    assert stretto(archivio, site=pezzi["casa"], camera=pezzi["asi533"]) == (
        {"M 31": (1, 600.0)},
        1,
    )
    assert stretto(archivio, site=pezzi["deserto"], camera=pezzi["asi533"]) == ({}, 0)


def test_the_filter_of_the_bar_asks_the_same_poses(archivio):
    """La Lum di M 31 e' tutta del 2024: "Lum nel 2025" non trova niente."""
    banco(archivio)

    righe, quanti = archive.page(
        archivio,
        limit=50,
        offset=0,
        filter_name="Lum",
        scope=Scope(since="2025-01-01", until="2025-12-31"),
    )

    assert (righe, quanti) == ([], 0)


def test_by_hours_reads_the_narrowed_hours(archivio):
    """Per ore, in tutto M 31 sta davanti; nel 2024 NGC 7000. Un ordine che guardasse le ore di
    sempre metterebbe in cima la riga con meno ore a schermo."""
    banco(archivio)

    tutte, _ = archive.page(archivio, limit=50, offset=0, sort=archive.Order.HOURS)
    anno = Scope(since="2024-01-01", until="2024-12-31")
    nel_2024, _ = archive.page(archivio, limit=50, offset=0, sort=archive.Order.HOURS, scope=anno)

    assert nomi(tutte)[:2] == ["M 31", "NGC 7000"]
    assert nomi(nel_2024) == ["NGC 7000", "M 31"]


def test_the_found_count_follows_the_narrowing(archivio):
    pezzi = banco(archivio)

    assert archive.found(archivio) == {"objects": 3, "mosaics": 0}
    assert archive.found(archivio, scope=Scope(site=pezzi["deserto"])) == {
        "objects": 1,
        "mosaics": 0,
    }


def test_the_pills_of_a_row_say_the_narrowed_hours(archivio):
    """Le pastiglie dei filtri sono la stessa riga divisa per filtro: nel 2024 M 31 e' tutta
    Lum, e una pastiglia Ha con le ore del 2025 smentirebbe la riga accanto."""
    pezzi = banco(archivio)

    pastiglie = filters_used.of(
        archivio,
        Subject.OBJECT,
        [pezzi["m31"]],
        alone=True,
        scope=Scope(since="2024-01-01", until="2024-12-31"),
    )

    assert [(p["name"], p["integration_s"]) for p in pastiglie[pezzi["m31"]]] == [("Lum", 600.0)]


def test_a_mosaic_says_only_the_panels_and_hours_shot_in_the_period(archivio):
    """Un mosaico ripreso in due anni: stringendo al 2025 la riga porta le ore del 2025, e la carta
    apre i soli pannelli ripresi allora."""
    pezzi = banco(archivio)
    ha = nasce_filtro(archivio, "Ha 7nm", "ha")
    pannelli = [oggetto(archivio, n, s) for n, s in (("IC 405", "ic-405"), ("Sh2 230", "sh2-230"))]
    dentro = [posa(archivio, p, filtro=ha) for p in pannelli]
    mosaico(archivio, dentro)
    notti = [notte(archivio, pezzi["casa"], d) for d in ("2023-03-01", "2025-03-01")]
    archivio.executemany(
        "UPDATE frames SET night_id = ? WHERE id = ?", list(zip(notti, dentro, strict=True))
    )
    nel_2025 = Scope(since="2025-01-01", until="2025-12-31")

    righe, _ = archive.page(archivio, limit=50, offset=0, mosaic=True, scope=nel_2025)

    assert [(r["frames"], r["integration_s"]) for r in righe] == [(1, 300.0)]
    assert len(archive.panels(archivio, [CHIAVE], nel_2025)[CHIAVE]) == 1
    assert len(archive.panels(archivio, [CHIAVE])[CHIAVE]) == 2


def test_the_choices_offer_the_years_sites_and_pieces_you_shot_with(archivio):
    """Gli anni sono quelli delle tue notti, dal piu' recente. Siti, ottiche e camere compaiono
    solo se sono almeno due: con uno solo, sceglierlo non stringe niente."""
    pezzi = banco(archivio)
    # posseduta e mai usata: non stringe niente, non si offre
    attrezzo(archivio, "camera", "Nel cassetto")

    scelte = archive.choices(archivio)

    assert scelte["years"] == ["2025", "2024"]
    assert scelte["sites"] == [
        {"id": pezzi["casa"], "name": "Casa"},
        {"id": pezzi["deserto"], "name": "Deserto"},
    ]
    assert scelte["optics"] == [
        {"id": pezzi["newton"], "name": "Newton"},
        {"id": pezzi["rifrattore"], "name": "Rifrattore"},
    ]
    assert scelte["cameras"] == [
        {"id": pezzi["asi2600"], "name": "ASI2600"},
        {"id": pezzi["asi533"], "name": "ASI533"},
    ]


def test_one_site_or_one_camera_is_not_a_choice(archivio):
    casa = luogo(archivio)
    ottica, camera = attrezzo(archivio, "optics", "Rifrattore"), attrezzo(archivio, "camera", "ASI")
    m31, gennaio = oggetto(archivio, "M 31", "m-31"), notte(archivio, casa, "2025-01-15")
    a = corredo(archivio, ottica, camera)
    riprese(archivio, m31, 1, notte_id=gennaio, corredo_id=a, filtro=None, secondi=60.0)

    scelte = archive.choices(archivio)

    assert (scelte["years"], scelte["sites"], scelte["optics"], scelte["cameras"]) == (
        ["2025"],
        [],
        [],
        [],
    )
