"""I conti del setup (ADR 0021): ognuno solo coi suoi dati, e se ne manca uno dice quale.

L'esempio e' quello della tavola di Design, "Notte in quota" (`handoff/design/pagine/componenti/
dati.js`, DECISIONI v16): FRA400 72/400 col solo spianatore, ASI2600MM a 3,76 um e 6248 x 4176,
guida col cercatore 30/120 e la ASI120MM Mini a 3,75 um. La tavola scrive f/5.6, 1.94"/px,
3.36 x 2.25 gradi, 1.61", seeing ottimo 3.9-5.8", guida 6.45"/px con avviso e 3.3x.
"""

import pytest

from astrolog.spine import rig_numbers as rn

OTTICA = {"kind": "optics", "aperture_mm": 72.0, "focal_mm": 400.0, "weight_kg": 2.6}
CAMERA = {
    "kind": "camera", "pixel_size_um": 3.76, "width_px": 6248, "height_px": 4176,
    "thickness_mm": 17.5, "weight_kg": 0.7,
}  # fmt: skip
CERCATORE = {"kind": "guide_scope", "aperture_mm": 30.0, "focal_mm": 120.0, "weight_kg": 0.2}
GUIDA = {"kind": "guide_camera", "pixel_size_um": 3.75, "weight_kg": 0.06}


def setup(**parti):
    base = {"focal_mm": 400.0, "optics": OTTICA, "camera": CAMERA}
    return rn.RigCard(**{**base, **parti})


def test_the_example_of_the_board_comes_back():
    conti = rn.numbers(setup(guide=CERCATORE, guide_camera=GUIDA))
    assert conti["focal_ratio"]["value"] == pytest.approx(5.56, abs=0.01)
    assert conti["sampling"]["value"] == pytest.approx(1.94, abs=0.01)
    assert conti["sampling"]["seeing_from"] == pytest.approx(3.88, abs=0.01)
    assert conti["sampling"]["seeing_to"] == pytest.approx(5.82, abs=0.01)
    assert conti["field"]["width"] == pytest.approx(3.36, abs=0.01)
    assert conti["field"]["height"] == pytest.approx(2.25, abs=0.01)
    assert conti["sensor_size"]["width"] == pytest.approx(23.49, abs=0.01)
    assert conti["guide_scale"]["value"] == pytest.approx(6.45, abs=0.01)
    assert conti["guide_scale"]["in_range"] is False
    assert conti["guide_ratio"]["value"] == pytest.approx(3.32, abs=0.01)


def test_the_resolving_power_of_an_optics_is_dawes():
    assert rn.piece_numbers(OTTICA)["dawes"]["value"] == pytest.approx(1.61, abs=0.01)


def test_a_camera_says_the_size_of_its_sensor():
    assert rn.piece_numbers(CAMERA)["sensor_size"]["height"] == pytest.approx(15.70, abs=0.01)


def test_the_effective_focal_is_the_rigs_and_without_it_the_rig_says_so():
    """Nessun ripiego focale x fattore: l'ADR non lo prevede, e un riduttore senza fattore
    scritto direbbe un numero falso."""
    conti = rn.numbers(setup(focal_mm=None))
    assert conti["sampling"]["missing"] == {"kind": "rig", "field": "focal_mm"}
    assert conti["sampling"]["value"] is None


def test_a_rig_without_optics_says_the_optics_is_missing():
    conti = rn.numbers(setup(optics=None))
    assert conti["focal_ratio"]["missing"] == {"kind": "optics", "field": None}
    assert conti["coverage"]["missing"] == {"kind": "optics", "field": None}


def test_each_number_names_the_first_datum_it_lacks():
    senza_pixel = {**CAMERA, "pixel_size_um": None}
    conti = rn.numbers(setup(camera=senza_pixel))
    assert conti["sampling"]["missing"] == {"kind": "camera", "field": "pixel_size_um"}
    assert conti["field"]["missing"] == {"kind": "camera", "field": "pixel_size_um"}


def test_an_oag_guides_with_the_focal_of_the_rig():
    oag = {"kind": "oag", "thickness_mm": 16.5, "prism_mm": 8.0}
    conti = rn.numbers(setup(guide=oag, guide_camera=GUIDA))
    assert conti["guide_scale"]["value"] == pytest.approx(1.93, abs=0.01)
    assert conti["guide_scale"]["in_range"] is True


def test_an_oag_without_a_guide_camera_does_not_borrow_the_main_camera():
    oag = {"kind": "oag", "thickness_mm": 16.5}
    conti = rn.numbers(setup(guide=oag))
    assert conti["guide_scale"]["missing"] == {"kind": "guide_camera", "field": None}


def test_without_a_guide_the_guide_is_missing():
    assert rn.numbers(setup())["guide_scale"]["missing"] == {"kind": "guide", "field": None}


def test_the_ratio_of_guide_and_imaging_has_no_verdict():
    conti = rn.numbers(setup(guide=CERCATORE, guide_camera=GUIDA))
    assert set(conti["guide_ratio"]) == {"value", "missing"}


@pytest.mark.parametrize(("cerchio", "copre"), [(30.0, True), (28.2, False), (20.0, False)])
def test_the_image_circle_covers_the_diagonal_or_not(cerchio, copre):
    """Diagonale dell'ASI2600: 28,26 mm. Un confronto, non una soglia."""
    conti = rn.numbers(setup(optics={**OTTICA, "image_circle_mm": cerchio}))
    assert conti["coverage"]["diagonal_mm"] == pytest.approx(28.26, abs=0.01)
    assert conti["coverage"]["covers"] is copre


def test_the_reducer_decides_the_circle_and_the_backfocus_when_there_is_one():
    riduttore = {"kind": "reducer", "image_circle_mm": 44.0, "required_backfocus_mm": 55.0}
    ottica = {**OTTICA, "image_circle_mm": 20.0, "required_backfocus_mm": 99.0}
    conti = rn.numbers(setup(optics=ottica, reducer=riduttore))
    assert conti["coverage"]["circle_mm"] == 44.0
    assert conti["backfocus"]["difference_mm"] == pytest.approx(17.5 - 55.0)


def test_a_reducer_without_its_circle_does_not_fall_back_on_the_optics():
    riduttore = {"kind": "reducer", "required_backfocus_mm": 55.0}
    conti = rn.numbers(setup(optics={**OTTICA, "image_circle_mm": 44.0}, reducer=riduttore))
    assert conti["coverage"]["missing"] == {"kind": "reducer", "field": "image_circle_mm"}


RUOTA = {"kind": "filter_wheel", "thickness_mm": 20.0, "weight_kg": 0.4}
DIST = {"kind": "spacer", "thickness_mm": 10.0, "weight_kg": 0.05}


@pytest.mark.parametrize(
    ("richiesto", "tolleranza", "verdetto"),
    [
        (55.0, 1.0, "exact"),
        (54.5, 1.0, "in_tolerance"),
        (60.0, 1.0, "short"),
        (50.0, 1.0, "long"),
        (54.5, None, None),
    ],
)
def test_the_backfocus_is_judged_only_with_the_tolerance(richiesto, tolleranza, verdetto):
    """Treno: ruota 20 + due distanziali da 10 + camera 17,5 = 57,5; con l'OAG 16,5 non c'e'.
    Senza tolleranza del produttore solo la differenza (DECISIONI v16.1)."""
    camera = {**CAMERA, "thickness_mm": 15.0}
    riduttore = {
        "kind": "reducer", "required_backfocus_mm": richiesto,
        "backfocus_tolerance_mm": tolleranza,
    }  # fmt: skip
    conti = rn.numbers(setup(camera=camera, reducer=riduttore, wheel=RUOTA, spacers=(DIST, DIST)))
    assert conti["backfocus"]["difference_mm"] == pytest.approx(55.0 - richiesto)
    assert conti["backfocus"]["verdict"] == verdetto


def test_the_oag_and_the_spacers_are_in_the_train():
    oag = {"kind": "oag", "thickness_mm": 16.5}
    ottica = {**OTTICA, "required_backfocus_mm": 55.0}
    conti = rn.numbers(setup(optics=ottica, guide=oag, wheel=RUOTA, spacers=(DIST,)))
    assert conti["backfocus"]["difference_mm"] == pytest.approx(16.5 + 20.0 + 10.0 + 17.5 - 55.0)


def test_a_piece_of_the_train_without_thickness_is_named():
    ottica = {**OTTICA, "required_backfocus_mm": 55.0}
    conti = rn.numbers(setup(optics=ottica, wheel={**RUOTA, "thickness_mm": None}))
    assert conti["backfocus"]["missing"] == {"kind": "filter_wheel", "field": "thickness_mm"}


MONTATURA = {"kind": "mount", "payload_kg": 13.0, "payload_no_cw_kg": 8.0}


def test_the_load_is_only_a_percentage_of_the_highest_payload():
    conti = rn.numbers(setup(mount=MONTATURA, guide=CERCATORE, guide_camera=GUIDA))
    pesi = 2.6 + 0.7 + 0.2 + 0.06
    assert conti["load"]["percent"] == pytest.approx(pesi / 13.0 * 100)
    assert conti["load"]["within"] is True


def test_over_the_payload_is_said():
    leggera = {"kind": "mount", "payload_kg": 3.0}
    assert rn.numbers(setup(mount=leggera))["load"]["within"] is False


def test_the_load_names_the_mount_then_the_piece_without_weight():
    assert rn.numbers(setup())["load"]["missing"] == {"kind": "mount", "field": None}
    senza_carico = {"kind": "mount"}
    assert rn.numbers(setup(mount=senza_carico))["load"]["missing"] == {
        "kind": "mount", "field": "payload_kg",
    }  # fmt: skip
    conti = rn.numbers(setup(mount=MONTATURA, wheel={**RUOTA, "weight_kg": None}))
    assert conti["load"]["missing"] == {"kind": "filter_wheel", "field": "weight_kg"}


def test_the_load_says_the_weight_and_the_payload_it_divides():
    """La tavola scrive «3,6 kg su 13» sotto la percentuale (`conti`, 361)."""
    conti = rn.numbers(setup(mount=MONTATURA, guide=CERCATORE, guide_camera=GUIDA))
    assert conti["load"]["weight_kg"] == pytest.approx(2.6 + 0.7 + 0.2 + 0.06)
    assert conti["load"]["payload_kg"] == 13.0


def test_the_backfocus_says_the_train_and_who_requires_it():
    """La tavola scrive il treno intero e «richiesto 55 mm dal riduttore» (`conti`, 356)."""
    riduttore = {"kind": "reducer", "required_backfocus_mm": 55.0}
    conti = rn.numbers(setup(reducer=riduttore, wheel=RUOTA, spacers=(DIST,)))
    assert conti["backfocus"]["train_mm"] == pytest.approx(20.0 + 10.0 + 17.5)
    assert conti["backfocus"]["required_mm"] == 55.0
    assert conti["backfocus"]["required_by"] == "reducer"
    ottica = {**OTTICA, "required_backfocus_mm": 55.0}
    assert rn.numbers(setup(optics=ottica))["backfocus"]["required_by"] == "optics"


def test_the_guide_scale_says_which_guide_it_used():
    """«con ZWO 30 mm f/4» o «fuori asse, con la focale del setup» (`conti`, 352)."""
    cercatore = {**CERCATORE, "name": "ZWO 30 mm f/4"}
    conti = rn.numbers(setup(guide=cercatore, guide_camera=GUIDA))
    assert conti["guide_scale"]["guide"] == "guide_scope"
    assert (conti["guide_scale"]["range_from"], conti["guide_scale"]["range_to"]) == (0.5, 4.0)
    assert conti["guide_scale"]["guide_name"] == "ZWO 30 mm f/4"
    oag = {"kind": "oag", "name": "OAG-L"}
    assert rn.numbers(setup(guide=oag, guide_camera=GUIDA))["guide_scale"]["guide"] == "oag"


def test_the_guide_ratio_names_the_sampling_first():
    """Come la tavola (353): senza il pixel della camera manca il campionamento, non la guida."""
    camera = {**CAMERA, "pixel_size_um": None}
    conti = rn.numbers(setup(camera=camera))
    assert conti["guide_ratio"]["missing"] == {"kind": "camera", "field": "pixel_size_um"}
