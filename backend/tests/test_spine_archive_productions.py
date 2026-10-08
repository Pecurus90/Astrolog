"""Le **produzioni** di una riga dell'Archivio: lo stesso oggetto ripreso con la stessa ottica e
la stessa camera (Marco, 8/10/2026), finche' non esistono i progetti. Ognuna dice il suo corredo,
i suoi frame, le sue ore e i suoi filtri; insieme fanno la riga, senza contare niente due volte.
"""

from astrolog.clock import now_iso
from astrolog.spine import filters_used, productions
from astrolog.spine.counts import Scope, Subject
from group_bench import attrezzo
from group_bench import filtro as nasce_filtro
from test_spine_archive import oggetto, posa
from test_spine_archive_mosaic import CHIAVE, mosaico
from test_spine_archive_scope import banco, corredo, riprese


def corredi(lista):
    return [(p["optics"], p["camera"]) for p in lista]


def test_an_object_shot_with_two_rigs_has_two_productions_most_time_first(archivio):
    """M 31 col rifrattore (sei pose, 3000 s) e col Newton (una, 600 s): due produzioni, e davanti
    quella a cui e' andato piu' tempo."""
    b = banco(archivio)

    sue = productions.of(archivio, Subject.OBJECT, [b["m31"]], alone=True)[b["m31"]]

    assert corredi(sue) == [("Rifrattore", "ASI2600"), ("Newton", "ASI533")]
    assert [(p["frames"], p["integration_s"], p["untimed"]) for p in sue] == [
        (6, 3000.0, 0),
        (1, 600.0, 0),
    ]


def test_each_production_says_its_own_filters_in_the_order_of_the_row(archivio):
    """I filtri sono quelli **di quella produzione**, coi suoi frame e le sue ore, e stanno
    nell'ordine in cui li dice la riga: una carta non li mette in due ordini."""
    b = banco(archivio)

    rifrattore, newton = productions.of(archivio, Subject.OBJECT, [b["m31"]], alone=True)[b["m31"]]
    della_riga = filters_used.of(archivio, Subject.OBJECT, [b["m31"]], alone=True)[b["m31"]]

    assert {(f["name"], f["frames"], f["integration_s"]) for f in rifrattore["filters"]} == {
        ("Lum", 2, 600.0),
        ("Ha", 4, 2400.0),
    }
    assert [f["name"] for f in rifrattore["filters"]] == [f["name"] for f in della_riga]
    assert [(f["name"], f["passband"]) for f in newton["filters"]] == [("Ha", "ha")]


def test_the_productions_of_a_row_add_up_to_the_row(archivio):
    """Niente si conta due volte e niente si perde: la somma delle produzioni e' la riga."""
    b = banco(archivio)

    sue = productions.of(archivio, Subject.OBJECT, [b["m31"]], alone=True)[b["m31"]]

    assert sum(p["frames"] for p in sue) == 7
    assert sum(p["integration_s"] for p in sue) == 3600.0


def test_the_same_optics_and_camera_at_two_focal_lengths_are_one_production(archivio):
    """Un riduttore cambia la focale e il corredo (`rigs` li distingue), non la produzione: la
    definizione guarda l'ottica e la camera."""
    b = banco(archivio)
    ridotto = archivio.execute(
        "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES(?, ?, 320.0, 1, ?)",
        (b["rifrattore"], b["asi2600"], now_iso()),
    ).lastrowid
    riprese(archivio, b["ngc"], 2, notte_id=None, corredo_id=ridotto, filtro=None, secondi=100.0)

    sue = productions.of(archivio, Subject.OBJECT, [b["ngc"]], alone=True)[b["ngc"]]

    assert corredi(sue) == [("Rifrattore", "ASI2600")]
    assert sue[0]["frames"] == 5


def test_frames_that_do_not_say_their_rig_are_a_production_that_says_so(archivio):
    """Un frame senza corredo non sparisce e non si attacca a un altro: e' una produzione col
    corredo che non si sa (`None`), e i frame senza durata si contano a parte."""
    b = banco(archivio)
    riprese(archivio, b["ngc"], 2, notte_id=None, corredo_id=None, filtro=None, secondi=None)

    sue = productions.of(archivio, Subject.OBJECT, [b["ngc"]], alone=True)[b["ngc"]]

    assert corredi(sue) == [("Rifrattore", "ASI2600"), (None, None)]
    ignota = sue[1]
    assert (ignota["frames"], ignota["integration_s"], ignota["untimed"]) == (2, 0, 2)
    assert ignota["filters"] == []


def test_a_rig_that_knows_only_its_camera_is_its_own_production(archivio):
    """Meta' corredo e' un dato: la camera si dice, l'ottica non si sa. Non si fonde con chi non
    dice niente."""
    b = banco(archivio)
    solo_camera = corredo(archivio, None, b["asi533"])
    riprese(archivio, b["ngc"], 1, notte_id=None, corredo_id=solo_camera, filtro=None, secondi=50.0)
    riprese(archivio, b["ngc"], 1, notte_id=None, corredo_id=None, filtro=None, secondi=40.0)

    sue = productions.of(archivio, Subject.OBJECT, [b["ngc"]], alone=True)[b["ngc"]]

    assert corredi(sue) == [("Rifrattore", "ASI2600"), (None, "ASI533"), (None, None)]


def test_a_rewritten_copy_is_not_a_frame_of_a_production(archivio):
    b = banco(archivio)
    originale = archivio.execute(
        "SELECT id FROM frames WHERE object_id = ? LIMIT 1", (b["ngc"],)
    ).fetchone()["id"]
    copia = posa(archivio, b["ngc"], secondi=600.0)
    archivio.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (originale, copia))

    sue = productions.of(archivio, Subject.OBJECT, [b["ngc"]], alone=True)[b["ngc"]]

    assert sum(p["frames"] for p in sue) == 3


def test_a_narrowed_row_tells_the_productions_of_what_was_asked(archivio):
    """Stringendo al 2025 le produzioni sono quelle del 2025: il rifrattore porta le sole quattro
    pose di agosto, non le sei di sempre."""
    b = banco(archivio)

    sue = productions.of(
        archivio, Subject.OBJECT, [b["m31"]], alone=True, scope=Scope(since="2025-01-01")
    )[b["m31"]]

    assert [(p["optics"], p["frames"]) for p in sue] == [("Rifrattore", 4), ("Newton", 1)]
    assert [f["name"] for f in sue[0]["filters"]] == ["Ha"]


def test_a_mosaic_has_its_productions_too_and_the_object_alone_keeps_its_own(archivio):
    """Un mosaico e' una riga come le altre: le sue produzioni sono i corredi delle sue pose.
    L'oggetto ripreso anche da solo porta le sole pose fuori dal mosaico."""
    ottica, camera = attrezzo(archivio, "optics", "Newton"), attrezzo(archivio, "camera", "ASI2600")
    a = corredo(archivio, ottica, camera)
    ha = nasce_filtro(archivio, "Ha", "ha")
    ic = oggetto(archivio, "IC 405", "ic-405")
    nel_mosaico = riprese(archivio, ic, 3, notte_id=None, corredo_id=a, filtro=ha, secondi=300.0)
    riprese(archivio, ic, 1, notte_id=None, corredo_id=a, filtro=ha, secondi=100.0)
    mosaico(archivio, nel_mosaico)

    del_mosaico = productions.of(archivio, Subject.MOSAIC, [CHIAVE])[CHIAVE]
    da_solo = productions.of(archivio, Subject.OBJECT, [ic], alone=True)[ic]

    assert [(p["optics"], p["frames"]) for p in del_mosaico] == [("Newton", 3)]
    assert [(p["optics"], p["frames"]) for p in da_solo] == [("Newton", 1)]


def test_all_the_productions_of_a_page_come_in_two_questions(archivio):
    """Una per le produzioni e una per i loro filtri, per tutta la pagina: non una per riga."""
    b = banco(archivio)
    domande = []
    archivio.set_trace_callback(lambda sql: domande.append(sql) if "SELECT" in sql else None)

    assert productions.of(archivio, Subject.OBJECT, [], alone=True) == {}
    assert domande == []
    productions.of(archivio, Subject.OBJECT, [b["m31"], b["ngc"]], alone=True)
    archivio.set_trace_callback(None)

    assert len([d for d in domande if d.lstrip().startswith("SELECT")]) == 2
