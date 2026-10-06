"""Un filtro e un corredo scritti a mano sono quelli che i file porteranno, non un doppione.

Decisione di Marco (21/9/2026, `docs/domini/attrezzatura.md`): un filtro e' il suo nome, un corredo
la sua impronta -- ottica, camera, focale entro il 5 % -- e cio' che crei tu e' esattamente cio'
che la scansione riconoscera'. Qui si crea prima, e si scansiona dopo.
"""

import pytest

from astrolog.spine import gear, gear_create
from astrolog.spine import rigs as corredi
from conftest import frame_by_file, one, run_normalize, scan


def _dopo_la_scansione(conn, tmp_path):
    from synthetic import build_archive

    build_archive(tmp_path / "lib")
    scan(conn, tmp_path / "lib")
    run_normalize(conn)


def _pezzo(conn, kind, name):
    return gear_create.instrument(conn, kind, name, "ora", detected=False)


def test_a_filter_you_wrote_is_the_one_the_files_bring_later(conn, tmp_path):
    """Scritto col nome che leggi nei tuoi file -- `L` -- e non con quello che il vocabolario ne
    farebbe (`Lum`): le pose mono vengono a lui, e un secondo filtro non nasce."""
    scritto = gear_create.filter_declared(conn, "L", [{"band": "L"}], "ora")
    _dopo_la_scansione(conn, tmp_path)

    assert frame_by_file(conn, "L_001.fits")["filter_id"] == scritto
    assert one(conn, "SELECT COUNT(*) FROM filters WHERE name = 'Lum'") == 0


def test_a_name_that_is_already_the_spelling_of_another_filter_is_refused(conn):
    """Se `Halpha` l'hai gia' detto essere il tuo `Ha`, un filtro nuovo chiamato `Halpha` non
    ricevera' mai una posa: si dice, invece di farlo nascere vuoto."""
    from astrolog.spine import declarations

    gear_create.filter_declared(conn, "Ha", [{"band": "HA"}], "ora")
    declarations.learn(conn, "filter", "Halpha", "Ha")
    with pytest.raises(gear_create.SpellingTakenError):
        gear_create.filter_declared(conn, "Halpha", [{"band": "HA"}], "ora")


def test_a_rig_you_wrote_is_the_one_the_files_bring_later(conn, tmp_path):
    """La focale scritta a mano puo' non essere quella esatta dei file: entro il 5 % e' la stessa,
    come fra due scansioni."""
    ottica = _pezzo(conn, "optics", "Askar 103Apo")
    camera = _pezzo(conn, "camera", "ATR2600M(USB2.0)")
    scritto = corredi.create_declared(conn, ottica, camera, 570.0, "ora")
    _dopo_la_scansione(conn, tmp_path)

    assert frame_by_file(conn, "L_001.fits")["rig_id"] == scritto
    assert (
        one(
            conn,
            "SELECT COUNT(*) FROM rigs WHERE optics_id = ? AND camera_id = ?",
            (ottica, camera),
        )
        == 1
    )


def test_a_rig_you_already_have_is_refused(conn):
    ottica = _pezzo(conn, "optics", "TS 130 APO")
    camera = _pezzo(conn, "camera", "ASI2600MM")
    corredi.create_declared(conn, ottica, camera, 910.0, "ora")
    with pytest.raises(corredi.RigExistsError):
        corredi.create_declared(conn, ottica, camera, 920.0, "ora")
    # una focale diversa davvero e' un altro corredo: lo stesso telescopio col riduttore
    corredi.create_declared(conn, ottica, camera, 700.0, "ora")


def test_a_rig_is_made_of_an_optics_and_a_camera_you_own(conn):
    ottica = _pezzo(conn, "optics", "TS 130 APO")
    montatura = _pezzo(conn, "mount", "EQ6-R")
    with pytest.raises(corredi.WrongKindError):
        corredi.create_declared(conn, ottica, montatura, 910.0, "ora")
    with pytest.raises(corredi.WrongKindError):
        corredi.create_declared(conn, 9999, ottica, 910.0, "ora")


def test_a_rig_you_wrote_survives_the_merge_of_its_camera(conn):
    """Un'unione cancella i corredi del pezzo che sparisce, e `normalize` li rifa' dalle pose: il
    tuo pose non ne ha, e si rifa' dalla tua parola, col pezzo tenuto."""
    ottica = _pezzo(conn, "optics", "TS 130 APO")
    vecchia = _pezzo(conn, "camera", "ASI2600")
    tenuta = _pezzo(conn, "camera", "ASI2600MM Pro")
    corredi.create_declared(conn, ottica, vecchia, 910.0, "ora")
    gear.merge_instrument(conn, vecchia, tenuta)

    rifatto = conn.execute(
        "SELECT id, focal_mm, detected FROM rigs WHERE optics_id = ? AND camera_id = ?",
        (ottica, tenuta),
    ).fetchone()
    assert rifatto is not None
    assert (rifatto["focal_mm"], rifatto["detected"]) == (910.0, 0)
    # e ha la sua riga d'uso, a zero: non resta "da contare" finche' qualcosa non rigira
    uso = conn.execute(
        "SELECT frames FROM gear_usage WHERE subject = 'rig' AND subject_id = ?", (rifatto["id"],)
    ).fetchone()
    assert uso is not None and uso["frames"] == 0


def test_a_merge_into_a_rig_you_already_have_keeps_one(conn):
    """Se il pezzo tenuto ha gia' lo stesso corredo, dopo l'unione ce n'e' uno solo."""
    ottica = _pezzo(conn, "optics", "TS 130 APO")
    vecchia = _pezzo(conn, "camera", "ASI2600")
    tenuta = _pezzo(conn, "camera", "ASI2600MM Pro")
    corredi.create_declared(conn, ottica, vecchia, 910.0, "ora")
    corredi.create_declared(conn, ottica, tenuta, 910.0, "ora")
    gear.merge_instrument(conn, vecchia, tenuta)

    assert one(conn, "SELECT COUNT(*) FROM rigs WHERE optics_id = ?", (ottica,)) == 1


def test_a_filter_written_with_the_app_name_learns_no_rule(conn):
    """Scritto `B`, che e' gia' il nome del vocabolario, non c'e' niente da imparare: una regola
    `b -> B` sarebbe rumore, e come ogni regola si leggerebbe prima del colore."""
    gear_create.filter_declared(conn, "B", [{"band": "B"}], "ora")
    assert one(conn, "SELECT COUNT(*) FROM header_aliases WHERE kind = 'filter'") == 0


def test_a_rig_you_wrote_is_born_declared_and_when_you_wrote_it(conn):
    ottica = _pezzo(conn, "optics", "TS 130 APO")
    camera = _pezzo(conn, "camera", "ASI2600MM")
    rig = corredi.create_declared(conn, ottica, camera, 910.0, "2026-09-26T12:00:00Z")
    riga = conn.execute("SELECT detected, created_at FROM rigs WHERE id = ?", (rig,)).fetchone()
    assert (riga["detected"], riga["created_at"]) == (0, "2026-09-26T12:00:00Z")


def test_a_declared_rig_whose_piece_is_gone_is_not_born_half(conn):
    """Una dichiarazione che nomina un pezzo che non c'e' piu' non rifa' un corredo con la sola
    ottica: il corredo e' la sua impronta intera."""
    from astrolog.spine.declarations import write_declaration

    _pezzo(conn, "optics", "TS 130 APO")
    write_declaration(conn, "rig", "TS 130 APO|Sparita|500.0", corredi.RigField.DECLARED, 1, "ora")
    corredi.restore_declared(conn, "ora")
    assert one(conn, "SELECT COUNT(*) FROM rigs") == 0
