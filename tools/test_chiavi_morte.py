"""Le chiavi i18n che nessuno legge: scritte intere, al plurale, o costruite da un modello."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chiavi_morte

CODICE = """
t("nav.gear")
t(n === 1 ? "archive.frames.one" : "archive.frames")
t(`weather.verdict.${v}`)
t(`weather.wind700${forma}`)
const prefisso = "settings.folders"
t(`${prefisso}.label`)
"""


def test_a_key_nobody_asks_for_is_named():
    chiavi = ["nav.gear", "gear.title"]
    assert chiavi_morte.dead(chiavi, CODICE) == ["gear.title"]


def test_the_plural_lives_with_its_base():
    assert chiavi_morte.dead(["archive.frames", "archive.frames.one"], CODICE) == []
    assert chiavi_morte.dead(["nav.gear.one"], CODICE) == []


def test_a_template_keeps_its_family():
    assert chiavi_morte.dead(["weather.verdict.go", "weather.verdict.nogo"], CODICE) == []
    assert chiavi_morte.dead(["weather.wind700", "weather.wind700.ten"], CODICE) == []
    assert chiavi_morte.dead(["weather.window.dark"], CODICE) == ["weather.window.dark"]


def test_a_prefix_written_elsewhere_keeps_the_suffix_the_template_adds():
    assert chiavi_morte.dead(["settings.folders.label"], CODICE) == []
    assert chiavi_morte.dead(["settings.folders.look"], CODICE) == ["settings.folders.look"]


def test_the_main_dictionary_counts_and_the_i18n_code_reads(tmp_path):
    """`it.ts` porta chiavi sue; `i18n/index.ts` e' codice che le legge, non un dizionario."""
    i18n = tmp_path / "i18n"
    i18n.mkdir()
    (i18n / "it.ts").write_text('  "coord.n": "N",\n  "health.tables": "x",\n', encoding="utf-8")
    (i18n / "index.ts").write_text('t("coord.n")\n', encoding="utf-8")
    assert chiavi_morte.dead(chiavi_morte.keys(tmp_path), chiavi_morte.code_of(tmp_path)) == [
        "health.tables"
    ]


def test_the_real_app_has_no_dead_key():
    src = chiavi_morte.SRC
    assert chiavi_morte.dead(chiavi_morte.keys(src), chiavi_morte.code_of(src)) == []
