"""Mattone 4, scheda Filtro: nome scritto abbinato esatto a lista standard, risposte, filtri
dell'utente (ADR 0031). Risposta vale per nome scritto, per sempre."""

import sqlite3

import pytest

from astrolog.db.connect import connect
from astrolog.pipeline import filters
from astrolog.pipeline.card import read_card
from astrolog.pipeline.changes import add_root
from astrolog.pipeline.filters import (
    FORMS,
    Band,
    StandardFilter,
    answer,
    filter_key,
    resolve,
)
from astrolog.pipeline.scan import scan_root
from astrolog.pipeline.values import Program
from conftest import NOW, nina_light


def _spelling(conn, written: str) -> tuple[str | None, str | None]:
    row = conn.execute(
        "SELECT standard, filter_name FROM pipeline_filter_spellings WHERE written = ?", (written,)
    ).fetchone()
    return (row["standard"], row["filter_name"])


@pytest.mark.parametrize(
    ("written", "standard"),
    [
        ("L", StandardFilter.L), ("R", StandardFilter.R), ("G", StandardFilter.G),
        ("B", StandardFilter.B), ("H", StandardFilter.HA), ("O", StandardFilter.OIII),
        ("S", StandardFilter.SII),  # archive: N.I.N.A. letters; H/O/S map decision 10
        ("Ha", StandardFilter.HA), ("H-alpha", StandardFilter.HA), ("OIII", StandardFilter.OIII),
        ("O III", StandardFilter.OIII), ("SII", StandardFilter.SII), ("S II", StandardFilter.SII),
        ("H-beta", StandardFilter.HB), ("Luminance", StandardFilter.L), ("Red", StandardFilter.R),
        ("UV/IR-Cut", StandardFilter.UVIR), ("UV/IR Cut", StandardFilter.UVIR),
        ("None", StandardFilter.NONE),
        ("No filter", StandardFilter.NONE),
        (" ha ", StandardFilter.HA), ("O  III", StandardFilter.OIII), ("HA", StandardFilter.HA),
    ],
)  # fmt: skip
def test_a_standard_spelling_matches_without_case_or_extra_blanks(conn, written, standard):
    resolve(conn, written)
    assert _spelling(conn, written) == (standard, None)


@pytest.mark.parametrize(
    "written", ["Ha7nm", "Ha 7nm", "H-a", "O3", "S2", "Hb", "Lum", "Rosso", "IR-cut"]
)  # IR-cut: ZWO's label, but a plain IR cut may pass UV
def test_anything_else_is_asked_never_guessed(conn, written):
    resolve(conn, written)
    assert _spelling(conn, written) == (None, None)


def test_forms_are_ascii_normalized_and_unique():
    """FITS header: solo ASCII; Hα e Hβ solo nomi a schermo."""
    for form in FORMS:
        assert form.isascii()
        assert filter_key(form) == form
    assert len(FORMS) == len(set(FORMS))


def test_every_standard_but_none_has_bands():
    for standard in StandardFilter:
        assert bool(standard.bands) is (standard is not StandardFilter.NONE)
    assert StandardFilter.HA_OIII.bands == (Band.HA, Band.OIII)


def test_an_answer_to_a_standard_holds_for_every_spelling_of_its_key(conn):
    resolve(conn, "Ha 7nm")
    resolve(conn, "HA  7NM")
    answer(conn, "Ha 7nm", StandardFilter.HA)
    assert _spelling(conn, "Ha 7nm") == (StandardFilter.HA, None)
    assert _spelling(conn, "HA  7NM") == (StandardFilter.HA, None)


def test_an_answer_holds_for_a_file_scanned_later(conn, tmp_path):
    answer(conn, "Ha 7nm", StandardFilter.HA)
    nina_light(tmp_path / "a.fits", 1, ("FILTER  = 'Ha 7nm'",))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _spelling(conn, "Ha 7nm") == (StandardFilter.HA, None)


def test_a_new_filter_is_born_from_its_answer_with_bands_and_width(conn):
    resolve(conn, "Ha 3nm")
    resolve(conn, "Ha 7nm")
    answer(conn, "Ha 3nm", "Antlia Ha 3nm", {Band.HA: 3.0})
    answer(conn, "Ha 7nm", "Optolong Ha 7nm", {Band.HA: 7.0})
    assert _spelling(conn, "Ha 3nm") == (None, "Antlia Ha 3nm")
    assert _spelling(conn, "Ha 7nm") == (None, "Optolong Ha 7nm")
    widths = conn.execute(
        "SELECT filter_name, band, width_nm FROM pipeline_filter_bands ORDER BY width_nm"
    ).fetchall()
    expected = [("Antlia Ha 3nm", "ha", 3.0), ("Optolong Ha 7nm", "ha", 7.0)]
    assert [tuple(w) for w in widths] == expected


def test_a_written_name_equal_to_a_user_filter_matches_it(conn):
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    resolve(conn, "ANTLIA 3NM")
    assert _spelling(conn, "ANTLIA 3NM") == (None, "Antlia 3nm")


def test_a_spelling_seen_before_its_filter_is_born_matches_it(conn):
    resolve(conn, "Antlia 3nm")
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    assert _spelling(conn, "Antlia 3nm") == (None, "Antlia 3nm")


def test_a_second_answer_can_point_to_an_existing_user_filter(conn):
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    resolve(conn, "Antlia Ha")
    answer(conn, "Antlia Ha", "Antlia 3nm")
    assert _spelling(conn, "Antlia Ha") == (None, "Antlia 3nm")


@pytest.mark.parametrize(
    ("written", "target", "bands"),
    [
        ("Ha 7nm", "My Ha", None),  # new filter without band
        ("Ha 7nm", "My Ha", {}),
        ("H", StandardFilter.OIII, None),  # standard form: never answered
        ("Ha 7nm", "Ha", {Band.HA: 7.0}),  # filter named as standard form
        ("  ", StandardFilter.HA, None),
    ],
)
def test_an_answer_that_would_contradict_the_list_is_refused(conn, written, target, bands):
    with pytest.raises(ValueError):
        answer(conn, written, target, bands)


def test_two_filters_cannot_share_a_key(conn):
    answer(conn, "x", "Antlia 3nm", {Band.HA: 3.0})
    with pytest.raises(ValueError):
        answer(conn, "y", "ANTLIA  3nm", {Band.HA: 3.0})


def test_a_renamed_filter_carries_its_answers_and_spellings(conn):
    resolve(conn, "Ha 3nm")
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    conn.execute("UPDATE pipeline_filters SET name = 'Antlia Ha 3nm' WHERE name = 'Antlia 3nm'")
    assert _spelling(conn, "Ha 3nm") == (None, "Antlia Ha 3nm")


def test_after_a_rename_the_new_name_matches_and_the_old_does_not(conn):
    """Chiave dal nome, una casa: il nome vecchio non indica piu' il filtro."""
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    conn.execute("UPDATE pipeline_filters SET name = 'Antlia Ha 3nm' WHERE name = 'Antlia 3nm'")
    resolve(conn, "ANTLIA HA 3NM")
    resolve(conn, "Antlia 3nm")
    assert _spelling(conn, "ANTLIA HA 3NM") == (None, "Antlia Ha 3nm")
    assert _spelling(conn, "Antlia 3nm") == (None, None)


def test_a_filter_born_with_an_answered_name_takes_that_name(conn):
    """Nome gia' risposto, poi filtro con quel nome: il nome indica il filtro."""
    resolve(conn, "Antlia 3nm")
    answer(conn, "Antlia 3nm", StandardFilter.OIII)
    answer(conn, "Ha 3nm", " Antlia 3nm ", {Band.HA: 3.0})
    assert _spelling(conn, "Antlia 3nm") == (None, "Antlia 3nm")
    answer(conn, "antlia 3NM", " Antlia 3nm ")  # blanks at ends: same filter


def test_the_name_of_a_user_filter_is_never_answered_as_something_else(conn):
    """Il nome di un tuo filtro indica quel filtro: una risposta non lo scavalca."""
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    with pytest.raises(ValueError):
        answer(conn, "antlia  3NM", StandardFilter.OIII)
    resolve(conn, "Antlia 3nm")
    assert _spelling(conn, "Antlia 3nm") == (None, "Antlia 3nm")


def test_a_filter_with_answers_cannot_be_deleted(conn):
    answer(conn, "Ha 3nm", "Antlia 3nm", {Band.HA: 3.0})
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM pipeline_filters WHERE name = 'Antlia 3nm'")


def test_a_failed_answer_leaves_nothing(conn):
    answer(conn, "x", "Antlia 3nm", {Band.HA: 3.0})
    with pytest.raises(ValueError):
        answer(conn, "y", "antlia 3nm", {Band.HA: 3.0})
    assert conn.execute("SELECT COUNT(*) FROM pipeline_filter_answers").fetchone()[0] == 1


def test_an_answer_never_fails_because_a_scan_batch_saved_meanwhile(db_path, monkeypatch):
    """Lotto della scansione salvato fra lettura e scrittura della risposta: la risposta regge,
    il lotto aspetta il suo turno (busy_timeout)."""
    ui, scan = connect(db_path), sqlite3.connect(db_path, timeout=0)
    real = filters._user_filter

    def batch_saved_meanwhile(conn, name, bands):
        conn.execute("SELECT 1 FROM pipeline_filters").fetchall()
        try:
            scan.execute("INSERT INTO pipeline_filter_spellings (written, key) VALUES ('x', 'x')")
            scan.commit()
        except sqlite3.OperationalError:
            scan.rollback()  # answer holds the lock: batch waits, in app by busy_timeout
        return real(conn, name, bands)

    monkeypatch.setattr(filters, "_user_filter", batch_saved_meanwhile)
    try:
        answer(ui, "Ha 7nm", "Antlia Ha", {Band.HA: 7.0})
        assert ui.execute("SELECT name FROM pipeline_filters").fetchall()[0]["name"] == "Antlia Ha"
    finally:
        ui.close()
        scan.close()


def test_the_card_keeps_the_filter_as_written():
    assert read_card(Program.NINA, {"FILTER": " Ha 7nm "}).filter == "Ha 7nm"
    assert read_card(Program.ASIAIR, {}).filter is None
    assert read_card(Program.NINA, {"FILTER": ""}).filter is None


def test_a_scan_resolves_each_written_filter(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1, ("FILTER  = 'H'",))
    nina_light(tmp_path / "b.fits", 2, ("FILTER  = 'Ha 7nm'",))
    nina_light(tmp_path / "c.fits", 3)
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _spelling(conn, "H") == (StandardFilter.HA, None)
    assert _spelling(conn, "Ha 7nm") == (None, None)
    filters = conn.execute("SELECT filter FROM pipeline_cards ORDER BY filter").fetchall()
    assert [f["filter"] for f in filters] == [None, "H", "Ha 7nm"]
