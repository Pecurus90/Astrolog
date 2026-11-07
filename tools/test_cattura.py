"""The capture for the collaudatore: a fixed size that the page really sees, steps that click
before each shot, the console with network errors, and every screen of a board of states."""

import json
import os
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cattura


def test_the_phone_is_390_by_844_and_the_desktop_1440_by_900():
    assert cattura.window("telefono") == (390, 844)
    assert cattura.window("desktop") == (1440, 900)
    assert cattura.window("stretto") == (1280, 800), "the narrow desktop Design checks too"


def test_a_taller_capture_keeps_the_width():
    assert cattura.window("telefono", 3000) == (390, 3000)


def test_an_unknown_format_is_refused():
    with pytest.raises(KeyError):
        cattura.window("tablet")


def test_chrome_starts_headless_in_the_given_profile_at_the_given_size():
    command = cattura.chrome_command("chrome", (390, 844), "p")
    assert command[0] == "chrome"
    assert "--headless=new" in command
    assert "--user-data-dir=p" in command
    assert "--window-size=390,844" in command
    assert "--remote-debugging-port=0" in command, "a free port, never one taken by chance"


def test_console_calls_exceptions_and_network_errors_become_lines():
    events = [
        {
            "method": "Runtime.consoleAPICalled",
            "params": {"type": "error", "args": [{"value": "ROTTO"}, {"description": "Error: x"}]},
        },
        {
            "method": "Runtime.exceptionThrown",
            "params": {"exceptionDetails": {"exception": {"description": "TypeError: y"}}},
        },
        {
            "method": "Log.entryAdded",
            "params": {"entry": {"level": "error", "text": "404 (Not Found)", "url": "http://h/a"}},
        },
        {"method": "Page.loadEventFired", "params": {}},
    ]
    lines = [line for e in events if (line := cattura.event_line(e))]
    assert lines == [
        "error: ROTTO Error: x",
        "exception: TypeError: y",
        "error: 404 (Not Found) -- http://h/a",
    ]


def test_a_screen_label_becomes_a_file_name():
    assert cattura.slug("Telefono · Sito: coordinate non valide") == (
        "telefono-sito-coordinate-non-valide"
    )


def test_a_chrome_dead_at_start_is_told_at_once_with_its_code(tmp_path):
    proc = subprocess.Popen([sys.executable, "-c", "raise SystemExit(3)"])
    proc.wait()
    began = time.monotonic()
    with pytest.raises(cattura.ChromeStartError, match="3"):
        cattura._debugger_url(str(tmp_path), proc)
    assert time.monotonic() - began < 2, "no waiting for a port a dead Chrome never opens"


needs_chrome = pytest.mark.skipif(cattura.find_chrome() is None, reason="Chrome is not installed")

PAGE = """<!doctype html><html><body style="margin:0">
<p id="t">prima</p><button id="b" onclick="t.textContent='dopo'">vai</button>
<div data-screen-label="Telefono · Nome: vuoto">
<h2>titolo</h2><div style="height:50px">a</div></div>
<script>console.error('ROTTO'); fetch('manca.json').catch(() => {})</script>
<script>document.title = window.__prima || 'senza'</script></body></html>"""


@needs_chrome
def test_a_real_capture_with_steps_console_and_screens(tmp_path):
    page = tmp_path / "pagina.html"
    page.write_text(PAGE, encoding="utf-8")
    plan = {
        "url": page.as_uri(),
        "formato": "telefono",
        "prima": "window.__prima = 'iniettato'",
        "passi": [
            {"out": str(tmp_path / "a.png")},
            {"js": "b.click(); [t.textContent, document.title]", "out": str(tmp_path / "b.png")},
        ],
        "schermi": str(tmp_path / "schermi"),
    }
    result = cattura.run(plan)
    assert (tmp_path / "a.png").stat().st_size > 0
    assert result["values"] == [None, ["dopo", "iniettato"]], "the step ran, after the init script"
    assert any("ROTTO" in line for line in result["console"])
    assert any("manca.json" in line for line in result["console"]), "network errors too"
    screen = tmp_path / "schermi" / "telefono-nome-vuoto.png"
    assert screen.stat().st_size > 0
    assert json.dumps(result["screens"]) == json.dumps([str(screen)])


# the first start dies at once, the second is the real Chrome
FLAKY_CHROME = """import os, subprocess, sys
mark = sys.argv[1]
if not os.path.exists(mark):
    open(mark, "w").close()
    sys.exit(1)
if os.name == "nt":
    sys.exit(subprocess.call(sys.argv[2:]))
os.execvp(sys.argv[2], sys.argv[2:])"""


@needs_chrome
def test_a_chrome_that_dies_at_start_gets_one_more_try(tmp_path, monkeypatch):
    wrapper = tmp_path / "flaky.py"
    wrapper.write_text(FLAKY_CHROME, encoding="utf-8")
    real = cattura.chrome_command
    mark = str(tmp_path / "started")
    monkeypatch.setattr(
        cattura,
        "chrome_command",
        lambda *a: [sys.executable, str(wrapper), mark, *real(*a)],
    )
    page = tmp_path / "pagina.html"
    page.write_text(PAGE, encoding="utf-8")
    result = cattura.run({"url": page.as_uri(), "carica": 0.5})
    assert os.path.exists(mark), "the first start really died"
    assert result["values"] == []
