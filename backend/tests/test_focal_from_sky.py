"""La focale di un frame si misura dal cielo, e l'header e' il ripiego (ADR 0016).

Dopo una soluzione la focale e' `206,265 x pixel / scala`: e' quella vera del treno ottico, col
riduttore dentro, che `FOCALLEN` spesso non dice. Il corredo nasce dall'header prima del cielo;
il cielo lo corregge quando la misura non e' quella del corredo.
"""

from astrolog.db.connect import connect
from astrolog.spine import run as run_mod
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from astrolog.spine.solve import solve_frames
from astrolog.spine.stages import StageName
from astrolog.units import focal_from_scale
from conftest import add_folder, write_light
from test_solve import solver

PIXEL = 3.76


def _ini(focal_mm, pixel_um=PIXEL):
    """La soluzione di ASTAP per un treno ottico a quella focale: scala in gradi per pixel."""
    deg = 206.265 * pixel_um / focal_mm / 3600
    return f"PLTSOLVD=T\nCRVAL1=10.5\nCRVAL2=41.2\nCD1_1={deg}\nCD1_2=0\nCD2_1=0\nCD2_2={deg}\n"


def _archivio(tmp_path, n=3, **header):
    root = tmp_path / "lib"
    for i in range(n):
        write_light(
            root / f"{i}.fits", date=f"2024-05-17T2{i}:00:00", INSTRUME="ZWO ASI2600MM", **header
        )
    return root


def _gira(conn, root, misurata, cache):
    list(scan_folder(conn, add_folder(conn, root)))
    list(normalize_frames(conn))
    list(
        solve_frames(
            conn, exe="astap", run=solver({i: _ini(misurata) for i in range(9)}), cache=cache
        )
    )
    list(normalize_frames(conn))


def _focali(conn):
    sql = "SELECT r.focal_mm FROM frames f JOIN rigs r ON r.id = f.rig_id ORDER BY f.id"
    return [r[0] for r in conn.execute(sql)]


def test_the_focal_is_the_pixel_over_the_scale():
    """206,265 x 3,76 / 1,3849 = 560 mm, arrotondata al millimetro; senza pixel o scala, niente."""
    assert focal_from_scale(PIXEL, 206.265 * PIXEL / 560.4) == 560
    assert focal_from_scale(None, 1.38) is None
    assert focal_from_scale(PIXEL, None) is None


def test_the_sky_writes_the_measured_focal_next_to_the_solution(db_path, tmp_path):
    conn = connect(db_path)
    _gira(conn, _archivio(tmp_path, FOCALLEN=560.0, XPIXSZ=PIXEL), 562.3, tmp_path / "c")
    assert [r[0] for r in conn.execute("SELECT focal_mm FROM frame_wcs")] == [562] * 3


def test_a_reducer_the_header_does_not_say_moves_the_frames_to_the_true_focal(db_path, tmp_path):
    """L'header dice la focale nativa, 700; col riduttore 0,8x il cielo misura 560: i frame
    vanno al corredo della focale vera, e quello dell'header non ha piu' frame."""
    conn = connect(db_path)
    _gira(conn, _archivio(tmp_path, FOCALLEN=700.0, XPIXSZ=PIXEL), 560.0, tmp_path / "c")
    assert _focali(conn) == [560] * 3
    vuoti = conn.execute(
        "SELECT COUNT(*) FROM rigs r"
        " WHERE NOT EXISTS (SELECT 1 FROM frames f WHERE f.rig_id = r.id)"
    ).fetchone()[0]
    assert vuoti == 0


def test_the_frames_the_sky_sends_back_are_redone_in_the_same_run(db_path, tmp_path, monkeypatch):
    """Nella coda vera `normalize` gira prima di `solve`: il frame rimandato si rifa' nello stesso
    giro, non al prossimo avvio, e `identify` lo trova pronto."""
    conn = connect(db_path)
    list(scan_folder(conn, add_folder(conn, _archivio(tmp_path, FOCALLEN=700.0, XPIXSZ=PIXEL))))
    fake = solver({i: _ini(560.0) for i in range(9)})
    monkeypatch.setattr(
        run_mod,
        "solve_frames",
        lambda c: solve_frames(c, exe="astap", run=fake, cache=tmp_path / "c"),
    )
    for _, factory in run_mod.queue(db_path, [StageName.NORMALIZE, StageName.SOLVE]):
        list(factory())
    rifare = conn.execute(
        "SELECT COUNT(*) FROM frame_stages WHERE stage = 'normalize' AND status != 'done'"
    ).fetchone()[0]
    assert (rifare, _focali(conn)) == (0, [560] * 3)


def test_a_measure_within_the_tolerance_keeps_the_rig_and_redoes_nothing(db_path, tmp_path):
    """Header 560, cielo 562: e' lo stesso corredo, e il cielo non rimanda niente indietro."""
    conn = connect(db_path)
    root = _archivio(tmp_path, FOCALLEN=560.0, XPIXSZ=PIXEL)
    list(scan_folder(conn, add_folder(conn, root)))
    list(normalize_frames(conn))
    prima = _focali(conn)
    list(
        solve_frames(
            conn, exe="astap", run=solver({i: _ini(562.0) for i in range(9)}), cache=tmp_path / "c"
        )
    )
    rifare = conn.execute(
        "SELECT COUNT(*) FROM frame_stages WHERE stage = 'normalize' AND status = 'pending'"
    ).fetchone()[0]
    assert (rifare, _focali(conn)) == (0, prima)


def test_without_a_pixel_the_header_focal_stays(db_path, tmp_path):
    """Senza `XPIXSZ` ne' pixel della camera la focale non si misura: resta quella dell'header."""
    conn = connect(db_path)
    _gira(conn, _archivio(tmp_path, FOCALLEN=700.0), 560.0, tmp_path / "c")
    assert (
        conn.execute("SELECT COUNT(*) FROM frame_wcs WHERE focal_mm IS NOT NULL").fetchone()[0] == 0
    )
    assert _focali(conn) == [700] * 3


def test_a_frame_without_a_header_focal_takes_the_measured_one(db_path, tmp_path):
    """L'header non dice la focale: il corredo nasce senza, e il cielo gliela da'."""
    conn = connect(db_path)
    _gira(conn, _archivio(tmp_path, XPIXSZ=PIXEL), 560.0, tmp_path / "c")
    assert _focali(conn) == [560] * 3


def test_without_xpixsz_the_camera_card_pixel_times_the_binning_measures(db_path, tmp_path):
    """L'header non dice il pixel ma la scheda della camera si': il pixel fisico per il binning
    (2 x 3,76) da' la focale vera; senza il binning la misura uscirebbe la meta'."""
    conn = connect(db_path)
    root = _archivio(tmp_path, FOCALLEN=700.0, XBINNING=2)
    list(scan_folder(conn, add_folder(conn, root)))
    list(normalize_frames(conn))
    conn.execute("UPDATE instruments SET pixel_size_um = ? WHERE kind = 'camera'", (PIXEL,))
    esiti = {i: _ini(560.0, pixel_um=2 * PIXEL) for i in range(9)}
    list(solve_frames(conn, exe="astap", run=solver(esiti), cache=tmp_path / "c"))
    list(normalize_frames(conn))
    assert [r[0] for r in conn.execute("SELECT focal_mm FROM frame_wcs")] == [560] * 3
    assert _focali(conn) == [560] * 3
