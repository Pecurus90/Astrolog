"""Eliminare un pezzo o un filtro, nella spina (`spine/gear_delete.py`): con lui se ne vanno la sua
scheda, le sue scelte sui setup, i suoi distanziali e le sue righe derivate. Le prove della pagina
stanno in `test_api_gear_delete.py`; qui si guarda ogni riga che deve sparire, e solo quella.
"""

import pytest

from astrolog.spine import gear_create, gear_delete, gear_usage
from astrolog.spine.declarations import EntityType, instrument_key, write_declaration
from astrolog.spine.rigs import SPACER_FIELD
from astrolog.vocab.instruments import InstrumentKind
from conftest import one

ORA = "2026-11-13T12:00:00+00:00"
MOUNT = InstrumentKind.MOUNT
PEZZO = EntityType.INSTRUMENT
SETUP = EntityType.RIG


def _dichiarazioni(conn, entity_type, field):
    return one(
        conn,
        "SELECT COUNT(*) FROM declarations WHERE entity_type = ? AND field = ?",
        (entity_type, field),
    )


def _righe(conn, tabella, subject, subject_id):
    return one(
        conn,
        f"SELECT COUNT(*) FROM {tabella} WHERE subject = ? AND subject_id = ?",  # noqa: S608
        (subject, subject_id),
    )


def test_a_piece_takes_its_card_its_choices_and_its_rows_with_it(conn):
    """La scheda, la scelta come montatura di un setup, il distanziale col suo nome: rinato con lo
    stesso nome, nulla di cio' torna. Le righe dell'altro pezzo restano."""
    montatura = gear_create.instrument(conn, MOUNT, "EQ6-R", ORA, detected=False)
    altra = gear_create.instrument(conn, MOUNT, "AM5", ORA, detected=False)
    write_declaration(conn, PEZZO, instrument_key(MOUNT, "EQ6-R"), "payload_kg", 20, ORA)
    write_declaration(conn, PEZZO, instrument_key(MOUNT, "AM5"), "payload_kg", 13, ORA)
    write_declaration(conn, SETUP, "TS|ASI|910", MOUNT, "EQ6-R", ORA)
    write_declaration(conn, SETUP, "TS|ASI|500", MOUNT, "AM5", ORA)
    write_declaration(conn, SETUP, "TS|ASI|910", SPACER_FIELD + "EQ6-R", 1, ORA)
    write_declaration(conn, SETUP, "TS|ASI|910", SPACER_FIELD + "AM5", 1, ORA)
    gear_usage.write(conn)
    assert _righe(conn, "gear_usage", "instrument", montatura) == 1
    assert _righe(conn, "gear_numbers", "instrument", montatura) == 1

    gear_delete.delete_instrument(conn, montatura)

    assert one(conn, "SELECT COUNT(*) FROM instruments WHERE id = ?", (montatura,)) == 0
    assert _dichiarazioni(conn, "instrument", "payload_kg") == 1
    assert one(conn, "SELECT value FROM declarations WHERE field = 'mount'") == "AM5"
    assert _dichiarazioni(conn, "rig", SPACER_FIELD + "EQ6-R") == 0
    assert _dichiarazioni(conn, "rig", SPACER_FIELD + "AM5") == 1
    assert _righe(conn, "gear_usage", "instrument", montatura) == 0
    assert _righe(conn, "gear_numbers", "instrument", montatura) == 0
    assert _righe(conn, "gear_usage", "instrument", altra) == 1
    assert _righe(conn, "gear_numbers", "instrument", altra) == 1


def test_a_filter_takes_its_rows_with_it(conn):
    filtro = gear_create.create_filter(conn, "Ha", "HA", ORA)
    altro = gear_create.create_filter(conn, "OIII", "OIII", ORA)
    gear_usage.write(conn)
    assert _righe(conn, "gear_usage", "filter", filtro) == 1

    gear_delete.delete_filter(conn, filtro)

    assert one(conn, "SELECT COUNT(*) FROM filters WHERE id = ?", (filtro,)) == 0
    assert _righe(conn, "gear_usage", "filter", filtro) == 0
    assert _righe(conn, "gear_usage", "filter", altro) == 1


def test_what_is_not_there_says_what_was_looked_for(conn):
    with pytest.raises(LookupError, match=r"^pezzo 9999$"):
        gear_delete.delete_instrument(conn, 9999)
    with pytest.raises(LookupError, match=r"^filtro 9999$"):
        gear_delete.delete_filter(conn, 9999)


def test_the_refusals_say_how_many_frames_and_which_rigs():
    assert str(gear_delete.InUseError(2, [10])) == "2 frame"
    assert str(gear_delete.InRigError([10, 11])) == "setup [10, 11]"
