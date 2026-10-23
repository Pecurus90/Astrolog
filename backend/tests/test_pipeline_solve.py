"""Mattone solve: una soluzione di ASTAP per posa, dal file e dalla scheda della posa. ASTAP finto
che risponde coi suoi .ini veri (`tests/astap/`): la suite non lancia mai il solver."""

import math
import os
import shutil
import stat
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astrolog import astap
from astrolog.db.connect import connect
from astrolog.pipeline import scan
from astrolog.pipeline.changes import add_root
from astrolog.pipeline.scan import scan_root
from astrolog.pipeline.scanner import Skip, Skipped
from astrolog.pipeline.solve import solve_root
from conftest import LATER, NOW, nina_light

INI = Path(__file__).with_name("astap")

# Card of a N.I.N.A. light with what the solve uses: focal, pixel, mount pointing.
_SKY = ("FOCALLEN=                560.0", "XPIXSZ  =                 3.76",
        "RA      =     241.254763508206", "DEC     =     17.7165957446809")  # fmt: skip


class FakeAstap:
    """Answers each launch with a real .ini (or .ini text), written where `-o` says; keeps the
    commands. `then`: runs after, as a second worker would. `-h`: help with `version`."""

    def __init__(
        self,
        *answers: str | None,
        then: Callable[[], None] | None = None,
        version: str | None = "CLI-2025.11.19",
    ) -> None:
        self.answers = list(answers)
        self.commands: list[list[str]] = []
        self.then = then
        self.version = version
        self.asked = 0  # -h launches
        self.there: list[bool] = []  # input file present at launch

    def __call__(self, cmd: Sequence[str], timeout_s: float) -> tuple[int, str]:
        if "-h" in cmd:
            self.asked += 1
            return 0, f"ASTAP astrometric solver version {self.version}\n" if self.version else ""
        self.commands.append(list(cmd))
        self.there.append(Path(cmd[cmd.index("-f") + 1]).is_file())
        answer = self.answers[min(len(self.commands), len(self.answers)) - 1]
        if answer == "timeout":
            raise TimeoutError
        if answer is not None:
            ini = Path(f"{cmd[cmd.index('-o') + 1]}.ini")
            if "=" in answer:
                ini.write_text(answer)
            else:
                shutil.copy(INI / answer, ini)
        if self.then is not None:
            self.then()
        return (0 if answer == "solved.ini" else 1), "Using star database D80\r\n"


def _option(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def _solve(conn, root: int, run: astap.Run, tmp_path: Path, exe: str | None = "astap_cli"):
    solver = astap.Solver(exe, run, databases=tmp_path / "db")
    return solve_root(conn, root, LATER, solver, tmp_path / "work")


def _scanned(conn, nas: Path) -> int:
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    return root


def _solutions(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM pipeline_solutions ORDER BY frame_id")]


def _outcomes(conn) -> list[str]:
    return [row["outcome"] for row in _solutions(conn)]


def _nina_pixels(seed: int) -> tuple[np.ndarray, fits.Header]:
    data = ((np.arange(48 * 64) + seed) % 4093).astype(np.uint16).reshape(48, 64)
    header = fits.Header()
    for key, value in {"SWCREATE": "N.I.N.A. 3.2.0.9001 (x64)", "IMAGETYP": "LIGHT",
                       "INSTRUME": "ATR2600M", "DATE-OBS": f"2025-06-29T21:{seed:02d}:33.412",
                       "EXPTIME": 300.0, "FOCALLEN": 560.0, "XPIXSZ": 3.76}.items():  # fmt: skip
        header[key] = value
    return data, header


def _nina_fz(path: Path, seed: int) -> None:
    """N.I.N.A. light compressed by fpack (Rice)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data, header = _nina_pixels(seed)
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(data, header)]).writeto(path)


def test_a_light_gets_the_sky_astap_found(conn, tmp_path):
    """Il .ini vero di un light: centro, scala e rotazione salvati per la posa."""
    nas = tmp_path / "nas"
    nina_light(nas / "m13.fits", 1, _SKY)
    root = _scanned(conn, nas)
    result = _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    [row] = _solutions(conn)
    assert row["outcome"] == "solved" and result.solved == 1
    assert row["ra_deg"] == pytest.approx(241.25198643662179)
    assert row["dec_deg"] == pytest.approx(17.726894038989336)
    cd11, cd21 = -2.6277393210341225e-004, -2.7944266362463124e-004
    assert row["scale_arcsec_px"] == pytest.approx(math.hypot(cd11, cd21) * 3600)
    assert row["rotation_deg"] is not None


def test_the_command_carries_the_card_hint_and_the_catalogue_folder(conn, tmp_path):
    """Indizio dalla scheda (ore e distanza dal polo sud), campo sempre detto, cartella del
    catalogo detta, niente -wcs ne' -D: ASTAP sceglie il catalogo per campo."""
    nas = tmp_path / "nas"
    nina_light(nas / "m13.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    [cmd] = run.commands
    assert float(_option(cmd, "-ra")) == pytest.approx(241.254763508206 / 15, abs=1e-5)
    assert float(_option(cmd, "-spd")) == pytest.approx(17.7165957446809 + 90, abs=1e-4)
    assert _option(cmd, "-r") == "30"
    field = 16 * 3.76 / 560.0 * 206.264806 / 3600
    assert float(_option(cmd, "-fov")) == pytest.approx(field, abs=1e-3)
    assert Path(_option(cmd, "-d")) == tmp_path / "db"
    assert "-wcs" not in cmd and "-D" not in cmd


def test_the_result_lands_in_a_fresh_folder_never_beside_the_frame(conn, tmp_path):
    """Base nuova per ogni lancio, fuori dalla cartella dell'utente e senza punto nel nome (ASTAP
    tronca al punto); la cartella di lavoro si svuota dopo."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    nina_light(nas / "b.fits", 2, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    bases = [Path(_option(cmd, "-o")) for cmd in run.commands]
    assert len(set(bases)) == 2
    assert all(work_dir in base.parents for base in bases for work_dir in [tmp_path / "work"])
    assert all("." not in base.name for base in bases)
    assert sorted(p.name for p in nas.iterdir()) == ["a.fits", "b.fits"]
    assert not any((tmp_path / "work").iterdir())


def test_a_crash_never_reads_an_earlier_result_as_its_own(conn, tmp_path):
    """Misurato: ASTAP che cade esce 0 e non scrive il .ini; quello vecchio restava e diceva
    PLTSOLVD=T. Il secondo frame non e' risolto."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    nina_light(nas / "b.fits", 2, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini", None), tmp_path)
    assert _outcomes(conn) == ["solved", "crashed"]


@pytest.mark.parametrize(
    ("answer", "outcome"), [("no_stars.ini", "no_stars"), ("no_solution.ini", "no_solution")]
)
def test_a_failure_is_saved_with_its_reason(conn, tmp_path, answer, outcome):
    """Poche stelle e nessuna soluzione: il frame e' stato provato, si dice perche'."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap(answer), tmp_path)
    [row] = _solutions(conn)
    assert row["outcome"] == outcome and row["ra_deg"] is None


def test_a_solved_shot_is_not_launched_again(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert run.commands == []


def test_calibrations_are_never_launched_typeless_get_their_try(conn, tmp_path):
    """Dark, flat, bias: niente stelle, mai ad ASTAP. Senza tipo: un tentativo."""
    nas = tmp_path / "nas"
    for i, kind in enumerate(("DARK", "FLAT", "BIAS")):
        nina_light(nas / f"{kind}.fits", i, _SKY, imagetyp=kind)
    nina_light(nas / "typeless.fits", 9, _SKY, imagetyp="WHATEVER")
    root = _scanned(conn, nas)
    run = FakeAstap("no_stars.ini")
    _solve(conn, root, run, tmp_path)
    assert [Path(_option(cmd, "-f")).name for cmd in run.commands] == ["typeless.fits"]


def test_one_launch_per_shot_and_the_plain_copy_is_the_one(conn, tmp_path):
    """Un .fits e la sua copia fpack sono la stessa posa: un lancio, sul non compresso (ASTAP
    2025 non legge i .fz)."""
    nas = tmp_path / "nas"
    _nina_fz(nas / "a.fits.fz", 0)
    data, header = _nina_pixels(0)
    fits.PrimaryHDU(data=data, header=header).writeto(nas / "b.fits")
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert [Path(_option(cmd, "-f")).name for cmd in run.commands] == ["b.fits"]
    assert len(_solutions(conn)) == 1


def test_without_a_pointing_the_search_is_blind(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY[:2])
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    [cmd] = run.commands
    assert "-ra" not in cmd and _option(cmd, "-r") == "180"


def test_without_focal_the_field_is_left_to_astap_but_still_said(conn, tmp_path):
    """Senza -fov ASTAP usa il campo dell'ultimo solve: stato fuori da noi. Senza scala, 0."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY[2:])
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert _option(run.commands[0], "-fov") == "0"


def test_no_catalogue_stops_the_pass_and_writes_nothing(conn, tmp_path):
    """Senza catalogo ogni frame fallirebbe uguale: ci si ferma al primo, nessuna riga."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    nina_light(nas / "b.fits", 2, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("no_database.ini")
    result = _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and _solutions(conn) == []
    assert result.stopped is astap.Reason.NO_STAR_DATABASE


def test_without_astap_nothing_is_launched_and_nothing_written(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    result = _solve(conn, root, run, tmp_path, exe=None)
    assert run.commands == [] and _solutions(conn) == []
    assert result.stopped is astap.Reason.ASTAP_MISSING


@pytest.mark.parametrize(
    ("answer", "outcome"),
    [("timeout", "timeout"), (None, "crashed"), ("PLTSOLVD=T\n", "crashed"),
     ("unreadable.ini", "unreadable")],
)  # fmt: skip
def test_a_shot_that_did_not_end_is_tried_once_more_then_waits(conn, tmp_path, answer, outcome):
    """Decisione D5: una volta alla scansione dopo, poi ferma. Detto il perche', con i tentativi."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    launched = []
    for _ in range(3):
        run = FakeAstap(answer)
        _solve(conn, root, run, tmp_path)
        launched.append(len(run.commands))
    [row] = _solutions(conn)
    assert launched == [1, 1, 0]
    assert (row["outcome"], row["attempts"], row["step"]) == (outcome, 2, "first")


def test_a_new_astap_tries_a_waiting_shot_again(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    for _ in range(2):
        _solve(conn, root, FakeAstap("timeout"), tmp_path)
    run = FakeAstap("solved.ini", version="CLI-2026.07.16")
    _solve(conn, root, run, tmp_path)
    [row] = _solutions(conn)
    assert len(run.commands) == 1 and row["outcome"] == "solved"
    assert row["astap_version"] == "2026.07.16" and row["attempts"] == 3


def test_a_new_catalogue_tries_a_waiting_shot_again(conn, tmp_path, monkeypatch):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    monkeypatch.setattr(astap, "catalogues_in", lambda folder: ("d80",))
    for _ in range(2):
        _solve(conn, root, FakeAstap("timeout"), tmp_path)
    monkeypatch.setattr(astap, "catalogues_in", lambda folder: ("d50", "d80"))
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and _outcomes(conn) == ["solved"]
    assert _solutions(conn)[0]["installed"] == "d50,d80"


def test_the_row_says_which_astap_and_catalogue_and_how_long(conn, tmp_path):
    """Versione da -h, catalogo che ASTAP dice di aver usato, durata di tutta la scala."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    [row] = _solutions(conn)
    assert (row["astap_version"], row["catalogue"]) == ("2025.11.19", "d80")
    assert row["duration_s"] >= 0 and row["attempts"] == 1


@pytest.mark.parametrize("plain_root", ["same", "other"])
def test_a_compressed_file_waiting_never_holds_back_its_plain_copy(conn, tmp_path, plain_root):
    """.fz illeggibile da questo ASTAP: fatto del file, non della posa. Il .fits della stessa
    posa, arrivato dopo o in un'altra radice, si lancia."""
    _nina_fz(tmp_path / "nas" / "a.fits.fz", 0)
    root = _scanned(conn, tmp_path / "nas")
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    data, header = _nina_pixels(0)
    plain = tmp_path / ("nas" if plain_root == "same" else "usb")
    plain.mkdir(exist_ok=True)
    fits.PrimaryHDU(data=data, header=header).writeto(plain / "b.fits")
    other = root if plain_root == "same" else _scanned(conn, plain)
    scan_root(conn, other, LATER)
    run = FakeAstap("solved.ini")
    _solve(conn, other, run, tmp_path)
    assert [Path(_option(c, "-f")).name for c in run.commands] == ["b.fits"]
    assert _outcomes(conn) == ["solved"]


def test_a_file_waiting_never_holds_back_a_good_copy_elsewhere(conn, tmp_path):
    nina_light(tmp_path / "nas" / "a.fits", 1, _SKY)
    nas = _scanned(conn, tmp_path / "nas")
    for _ in range(2):
        _solve(conn, nas, FakeAstap("unreadable.ini"), tmp_path)
    nina_light(tmp_path / "usb" / "a.fits", 1, _SKY)
    usb = _scanned(conn, tmp_path / "usb")
    run = FakeAstap("solved.ini")
    _solve(conn, usb, run, tmp_path)
    assert len(run.commands) == 1 and _outcomes(conn) == ["solved"]


def test_an_unread_version_counts_as_unchanged(conn, tmp_path):
    """-h che fallisce non e' un ASTAP nuovo: la posa in attesa resta ferma."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    _nina_fz(nas / "b.fits.fz", 2)
    root = _scanned(conn, nas)
    for _ in range(2):
        _solve(conn, root, FakeAstap("timeout"), tmp_path)
    run = FakeAstap("solved.ini", version=None)
    _solve(conn, root, run, tmp_path)
    assert run.commands == []


def test_the_installed_catalogues_are_read_where_astap_reads_them(conn, tmp_path):
    """Cartella -d detta: i cataloghi si guardano li', non accanto al programma."""
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "d50_0101.1476").write_bytes(b"")
    nina_light(tmp_path / "nas" / "a.fits", 1, _SKY)
    root = _scanned(conn, tmp_path / "nas")
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    assert _solutions(conn)[0]["installed"] == "d50"


def test_a_new_astap_reading_fpack_still_launches_once_per_shot(conn, tmp_path):
    nas = tmp_path / "nas"
    _nina_fz(nas / "a.fits.fz", 0)
    data, header = _nina_pixels(0)
    fits.PrimaryHDU(data=data, header=header).writeto(nas / "b.fits")
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini", version="CLI-2026.07.16")
    _solve(conn, root, run, tmp_path)
    assert {Path(_option(c, "-f")).name for c in run.commands} == {"b.fits"}


def test_the_duration_is_the_time_the_ladder_took(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini", then=lambda: time.sleep(0.05)), tmp_path)
    assert _solutions(conn)[0]["duration_s"] >= 0.03  # Windows clock: 15 ms steps


def test_settled_failures_are_never_launched_again(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    nina_light(nas / "b.fits", 2, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("no_stars.ini", "no_solution.ini"), tmp_path)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert run.commands == [] and sorted(_outcomes(conn)) == ["no_solution", "no_stars"]


def test_the_wait_follows_the_file_last_tried(conn, tmp_path):
    """.fz in attesa, poi la copia .fits va in timeout due volte: aspetta lei, non si rilancia."""
    _nina_fz(tmp_path / "nas" / "a.fits.fz", 0)
    nas = _scanned(conn, tmp_path / "nas")
    _solve(conn, nas, FakeAstap("solved.ini"), tmp_path)
    data, header = _nina_pixels(0)
    (tmp_path / "usb").mkdir()
    fits.PrimaryHDU(data=data, header=header).writeto(tmp_path / "usb" / "b.fits")
    usb = _scanned(conn, tmp_path / "usb")
    for _ in range(2):
        _solve(conn, usb, FakeAstap("timeout"), tmp_path)
    run = FakeAstap("solved.ini")
    _solve(conn, usb, run, tmp_path)
    assert run.commands == [] and _outcomes(conn) == ["timeout"]


def test_a_settled_outcome_is_never_overwritten(conn, tmp_path, db_path):
    """Un'altra passata ha gia' scritto un esito definitivo: il nostro timeout non lo cambia."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    other = connect(db_path)

    def other_pass() -> None:
        with other:
            other.execute(
                "INSERT INTO pipeline_solutions (frame_id, outcome, step, attempts, tried_at)"
                " SELECT id, 'no_stars', 'first', 1, ? FROM pipeline_frames",
                (LATER,),
            )

    result = _solve(conn, root, FakeAstap(None, then=other_pass), tmp_path)
    other.close()
    assert _outcomes(conn) == ["no_stars"]
    assert result.untried == {} and result.failed == {}  # counts only what it wrote


def test_a_gone_file_is_not_launched(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    (nas / "a.fits").unlink()
    (nas / "keep.txt").write_text("x")  # root not silent: the file is gone, not unreachable
    scan_root(conn, root, LATER)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert run.commands == []


def test_the_solution_goes_with_the_shot(conn, tmp_path):
    """Legata alla posa: il file spostato la tiene, nessun nuovo lancio."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    (nas / "moved").mkdir()
    (nas / "a.fits").rename(nas / "moved" / "a.fits")
    scan_root(conn, root, LATER)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert run.commands == [] and len(_solutions(conn)) == 1


def test_a_shot_solved_from_another_root_is_not_launched_again(conn, tmp_path):
    nina_light(tmp_path / "nas" / "a.fits", 1, _SKY)
    nina_light(tmp_path / "usb" / "a.fits", 1, _SKY)
    first, second = _scanned(conn, tmp_path / "nas"), _scanned(conn, tmp_path / "usb")
    _solve(conn, first, FakeAstap("solved.ini"), tmp_path)
    run = FakeAstap("solved.ini")
    _solve(conn, second, run, tmp_path)
    assert run.commands == []


def test_a_file_held_while_locked_is_not_launched(conn, tmp_path, monkeypatch):
    """Bloccato da un altro programma: tiene posa e scheda, ma ad ASTAP non va (puo' essere a meta'
    scrittura)."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    os.utime(nas / "a.fits", (2_000_000_000, 2_000_000_000))
    monkeypatch.setattr(scan, "scan_file", lambda p, size: Skipped(p, Skip.UNREADABLE))
    scan_root(conn, root, LATER)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert run.commands == []


def test_a_shot_that_leaves_takes_its_solution_with_it(conn, tmp_path):
    """Posa senza piu' file (riscritto): via il frame, via la soluzione (chiavi esterne accese)."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    nina_light(nas / "a.fits", 2, _SKY)
    os.utime(nas / "a.fits", (2_000_000_000, 2_000_000_000))
    scan_root(conn, root, LATER)
    assert _solutions(conn) == []


def test_without_a_catalogue_folder_astap_looks_in_its_own(conn, tmp_path):
    """Mac e Linux: ASTAP cerca il catalogo in una sua cartella, non accanto al programma. Non
    detta, non si passa."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    solve_root(conn, root, LATER, astap.Solver("/usr/bin/astap_cli", run), tmp_path / "work")
    assert "-d" not in run.commands[0]


@pytest.mark.parametrize(
    "crval", [("360.0", "17.7"), ("-0.001", "17.7"), ("400", "17.7"), ("241.2", "90.5")]
)
def test_a_sky_out_of_range_never_stops_the_pass(conn, tmp_path, crval):
    """Un .ini che dice risolto con un cielo impossibile: il passo va avanti sulla posa dopo."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    nina_light(nas / "b.fits", 2, _SKY)
    root = _scanned(conn, nas)
    solved = (INI / "solved.ini").read_text()
    odd = solved.replace("CRVAL1= 2.4125198643662179E+002", f"CRVAL1={crval[0]}").replace(
        "CRVAL2= 1.7726894038989336E+001", f"CRVAL2={crval[1]}"
    )
    _solve(conn, root, FakeAstap(odd, "solved.ini"), tmp_path)
    rows = _solutions(conn)
    assert len(rows) == 2 and rows[1]["outcome"] == "solved"
    assert rows[0]["ra_deg"] is None or 0 <= rows[0]["ra_deg"] < 360


def test_a_result_with_decimal_commas_is_read(conn, tmp_path):
    """La virgola decimale della macchina vale come punto, anche nel centro."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    comma = "PLTSOLVD=T\nCRVAL1=100,5\nCRVAL2=20,25\nCD1_1=-2,6E-004\nCD2_1=-2,7E-004\n"
    _solve(conn, root, FakeAstap(comma), tmp_path)
    [row] = _solutions(conn)
    assert row["outcome"] == "solved" and row["ra_deg"] == pytest.approx(100.5)


def test_a_half_written_result_is_tried_again(conn, tmp_path):
    """PLTSOLVD=T senza numeri: un .ini a meta', non un cielo che non si risolve."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("PLTSOLVD=T\n"), tmp_path)
    assert _outcomes(conn) == ["crashed"]


def test_a_shot_solved_meanwhile_by_another_pass_is_no_crash(conn, tmp_path, db_path):
    """Due passate insieme sulla stessa radice: chi arriva secondo non esplode."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    other = connect(db_path)

    def other_pass() -> None:
        with other:
            other.execute(
                "INSERT INTO pipeline_solutions (frame_id, outcome, step, tried_at)"
                " SELECT id, 'no_solution', 'first', ? FROM pipeline_frames",
                (LATER,),
            )

    _solve(conn, root, FakeAstap("solved.ini", then=other_pass), tmp_path)
    other.close()
    assert len(_solutions(conn)) == 1


def test_a_file_astap_cannot_read_is_tried_again(conn, tmp_path):
    """ASTAP dice "Error reading image file" (file sparito, compresso, nome che non legge): non e'
    un cielo che non si risolve. Detto, e si riprova alla passata dopo."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    result = _solve(conn, root, FakeAstap("unreadable.ini"), tmp_path)
    assert _outcomes(conn) == ["unreadable"] and result.untried == {"unreadable": 1}


def test_a_compressed_only_shot_waits_for_an_astap_that_reads_it(conn, tmp_path):
    """ASTAP legge i .fz dalla 2026.07.16 (hnsky.org): prima non si lancia, si dice perche'.
    Versione chiesta una volta per passata."""
    nas = tmp_path / "nas"
    _nina_fz(nas / "a.fits.fz", 1)
    _nina_fz(nas / "b.fits.fz", 2)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini", version="CLI-2025.11.19")
    result = _solve(conn, root, run, tmp_path)
    assert run.commands == [] and run.asked == 1
    assert result.untried == {"fz_unsupported": 2}
    rows = _solutions(conn)
    assert [(r["outcome"], r["step"], r["astap_version"]) for r in rows] == [
        ("fz_unsupported", None, "2025.11.19")
    ] * 2
    run = FakeAstap("solved.ini", version="CLI-2025.11.19")
    _solve(conn, root, run, tmp_path)  # same ASTAP: waits, however many passes
    assert [r["attempts"] for r in _solutions(conn)] == [1, 1]
    run = FakeAstap("solved.ini", version="CLI-2026.07.16")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 2 and _outcomes(conn) == ["solved", "solved"]


@pytest.mark.parametrize("version", ["CLI-2026.07.16", "CLI-2027.1.2"])
def test_an_astap_that_reads_fpack_gets_the_compressed_file(conn, tmp_path, version):
    nas = tmp_path / "nas"
    _nina_fz(nas / "a.fits.fz", 1)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini", version=version)
    _solve(conn, root, run, tmp_path)
    assert [Path(_option(cmd, "-f")).name for cmd in run.commands] == ["a.fits.fz"]


def test_an_astap_that_does_not_say_its_version_gets_the_try(conn, tmp_path):
    """Versione non letta: si prova, e se non legge il file si riprova dopo."""
    nas = tmp_path / "nas"
    _nina_fz(nas / "a.fits.fz", 1)
    root = _scanned(conn, nas)
    run = FakeAstap("unreadable.ini", version=None)
    result = _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and result.untried == {"unreadable": 1}
    assert _solutions(conn)[0]["astap_version"] is None


_CJK = "星雲"  # 2 CJK letters: outside every Western ANSI code page
windows = pytest.mark.skipif(os.name != "nt", reason="ANSI code page: Windows only")


def _in_code_page(text: str) -> bool:
    try:
        text.encode("mbcs")
    except UnicodeEncodeError:
        return False
    return True


def _short_or_skip(path: Path) -> str:
    short = astap._short_name(str(path))
    if not short or not _in_code_page(short):
        pytest.skip("volume without 8.3 names")
    return short


def _no_short_names(monkeypatch) -> None:
    """Such a volume: GetShortPathNameW succeeds, gives the long name back (Microsoft Learn)."""
    monkeypatch.setattr(astap, "_short_name", lambda path: path)


@windows
def test_a_name_outside_the_code_page_goes_by_its_short_name(conn, tmp_path):
    """Misurato: ASTAP riceve la riga di comando nella code page ANSI, i CJK diventano "?". Col
    nome 8.3 lo legge: il file dell'utente, nessuna copia."""
    nas = tmp_path / "nas" / _CJK
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, tmp_path / "nas")
    short = _short_or_skip(nas / "a.fits")
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert _option(run.commands[0], "-f") == short and run.there == [True]
    assert [row["outcome"] for row in _solutions(conn)] == ["solved"]


@windows
@pytest.mark.parametrize("name", ["a.fits", "a.fits.fz"])
def test_without_short_names_astap_gets_a_copy_and_the_original_stays_read_only(
    conn, tmp_path, monkeypatch, name
):
    """Volume senza 8.3: copia nella cartella del lancio (come N.I.N.A.), estensione che ASTAP
    riconosce. Mai link: condivide la sola lettura, la pulizia la toglieva all'originale."""
    _no_short_names(monkeypatch)
    nas = tmp_path / "nas" / _CJK
    if name.endswith(".fz"):
        _nina_fz(nas / name, 1)
    else:
        nina_light(nas / name, 1, _SKY)
    root = _scanned(conn, tmp_path / "nas")
    (nas / name).chmod(stat.S_IREAD)
    run = FakeAstap("solved.ini", version="CLI-2026.07.16")
    _solve(conn, root, run, tmp_path)
    given = Path(_option(run.commands[0], "-f"))
    assert (tmp_path / "work") in given.parents and run.there == [True]
    assert given.name == ("frame.fits.fz" if name.endswith(".fz") else "frame.fits")
    assert not os.access(nas / name, os.W_OK)
    assert [p.name for p in nas.iterdir()] == [name]
    assert not any((tmp_path / "work").iterdir())
    (nas / name).chmod(stat.S_IREAD | stat.S_IWRITE)


@windows
def test_a_compressed_file_never_goes_by_its_short_name(conn, tmp_path, monkeypatch):
    """L'8.3 di un .fz finisce in .FZ, ASTAP vuole .fits.fz (hnsky.org): copia."""
    monkeypatch.setattr(astap, "_short_name", lambda path: "C:\\NAS\\AFITS~1.FZ")
    _nina_fz(tmp_path / "nas" / _CJK / "a.fits.fz", 1)
    root = _scanned(conn, tmp_path / "nas")
    run = FakeAstap("solved.ini", version="CLI-2026.07.16")
    _solve(conn, root, run, tmp_path)
    assert Path(_option(run.commands[0], "-f")).name == "frame.fits.fz"


@windows
def test_a_copy_that_fails_is_tried_again(conn, tmp_path, monkeypatch):
    """Disco pieno: niente lancio, detto (nessun gradino), si riprova."""
    _no_short_names(monkeypatch)

    def full(*args: object, **kwargs: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(shutil, "copyfile", full)
    nina_light(tmp_path / "nas" / _CJK / "a.fits", 1, _SKY)
    root = _scanned(conn, tmp_path / "nas")
    run = FakeAstap("solved.ini")
    result = _solve(conn, root, run, tmp_path)
    assert run.commands == [] and result.untried == {"unreadable": 1}
    assert [(r["outcome"], r["step"]) for r in _solutions(conn)] == [("unreadable", None)]


@windows
def test_a_work_folder_outside_the_code_page_goes_by_its_short_name(conn, tmp_path):
    """Misurato: -o in una cartella CJK, nessun .ini. Anche il risultato passa dall'8.3."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    work = tmp_path / _CJK / "work"
    work.mkdir(parents=True)
    _short_or_skip(work)
    run = FakeAstap("solved.ini")
    solve_root(conn, root, LATER, astap.Solver("astap_cli", run), work)
    assert _in_code_page(_option(run.commands[0], "-o"))
    assert [row["outcome"] for row in _solutions(conn)] == ["solved"]


@windows
def test_a_work_folder_astap_cannot_name_stops_the_pass(conn, tmp_path, monkeypatch):
    """Cartella di lavoro senza nome ANSI ne' 8.3: ogni lancio fallirebbe, ci si ferma."""
    _no_short_names(monkeypatch)
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    solver = astap.Solver("astap_cli", run)
    result = solve_root(conn, root, LATER, solver, tmp_path / _CJK / "work")
    assert run.commands == [] and result.stopped is astap.Reason.PATH_UNSUPPORTED


def _steps(run: FakeAstap) -> list[tuple[str, bool, bool, str]]:
    """(-z, field said, pointing said, -r) of each launch."""
    return [
        (_option(c, "-z"), _option(c, "-fov") != "0", "-ra" in c, _option(c, "-r"))
        for c in run.commands
    ]


def _step(conn) -> list[tuple[str, str]]:
    return [(row["outcome"], row["step"]) for row in _solutions(conn)]


# Hinted ladder: N.I.N.A. failover drops only the pointing (ImageSolver.cs); z1, fov0 measured.
_HINTED = [
    ("0", True, True, "30"),
    ("1", True, True, "30"),
    ("0", False, True, "30"),
    ("0", True, False, "180"),
]


def test_no_solution_climbs_the_ladder_until_one_step_solves(conn, tmp_path):
    """Nessuna soluzione: -z 1, poi campo libero. Si salva il gradino che ha risolto."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini", "no_solution.ini", "solved.ini")
    _solve(conn, root, run, tmp_path)
    assert _steps(run) == _HINTED[:3]
    assert _step(conn) == [("solved", "any_field")]


def test_a_shot_never_solved_tries_every_step_then_says_so(conn, tmp_path):
    """Con indizio: in coda la cieca col campo (failover di N.I.N.A.). Mai cieca a campo libero:
    su un frame che non si risolve corre 285 s (misura)."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini")
    _solve(conn, root, run, tmp_path)
    assert _steps(run) == _HINTED
    assert _step(conn) == [("no_solution", "blind")]


def test_a_shot_solved_at_once_says_first(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("solved.ini")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and _step(conn) == [("solved", "first")]


def test_without_a_pointing_the_ladder_is_blind_from_the_start(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY[:2])
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini")
    _solve(conn, root, run, tmp_path)
    assert _steps(run) == [("0", True, False, "180"), ("1", True, False, "180"),
                           ("0", False, False, "180")]  # fmt: skip
    assert _step(conn) == [("no_solution", "any_field")]


def test_without_a_field_the_same_launch_is_never_repeated(conn, tmp_path):
    """Campo ignoto: "campo libero" e' gia' il primo gradino, non si rilancia uguale."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY[2:])
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini")
    _solve(conn, root, run, tmp_path)
    assert _steps(run) == [("0", False, True, "30"), ("1", False, True, "30"),
                           ("0", False, False, "180")]  # fmt: skip
    assert len({tuple(c) for c in run.commands}) == len(run.commands)


def test_not_enough_stars_never_climbs(conn, tmp_path):
    """Nuvole o dark senza tipo: 0,2 s invece di 8 (misura), nessun gradino in piu'."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("no_stars.ini", "solved.ini")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and _step(conn) == [("no_stars", "first")]


def test_a_typeless_shot_gets_one_try(conn, tmp_path):
    """Senza tipo: un tentativo (D6 del piano), poi si dice com'e' andata."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY, imagetyp="WHATEVER")
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini", "solved.ini")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and _step(conn) == [("no_solution", "first")]


def test_a_timeout_after_no_solution_ends_as_no_solution(conn, tmp_path):
    """ASTAP ha gia' detto che non trova: il gradino oltre 60 s chiude la scala, scritto. Senza,
    un frame irrisolvibile costava 70-86 s a ogni passata, per sempre (misura)."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini", "timeout", "solved.ini")
    result = _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 2 and _step(conn) == [("no_solution", "full_res")]
    assert result.failed == {"no_solution": 1}


def test_a_timeout_at_the_first_launch_waits_for_the_next_pass(conn, tmp_path):
    """Nessuna risposta di ASTAP ancora: scritto timeout, si riprova alla passata dopo."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("timeout", "solved.ini")
    result = _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 1 and _outcomes(conn) == ["timeout"]
    assert result.untried == {"timeout": 1}


def test_a_crash_mid_ladder_is_said_at_its_step(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    root = _scanned(conn, nas)
    run = FakeAstap("no_solution.ini", None, "solved.ini")
    _solve(conn, root, run, tmp_path)
    assert len(run.commands) == 2 and _step(conn) == [("crashed", "full_res")]
