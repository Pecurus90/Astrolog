"""Il pixel di una camera ricavato dal cielo, quando i file non lo dicono (Marco, 23/9/2026).

Si ricava da cio' che il solver ha misurato: il pixel fisico e' la scala per la focale del corredo,
diviso il binning (`units.pixel_um_from_scale`), e la camera prende la **mediana** delle sue pose
risolte. Lo scrive chi lavora le pose, a fine giro (`camera_sky.write`): la pagina lo legge e
basta. Rischio dichiarato: un riduttore che la focale dell'header non conta sposta il pixel.
"""

from astrolog.spine import camera_sky, stages, typeless, typeless_answer, typeless_folders
from astrolog.spine.declarations import TypeAnswer
from astrolog.spine.solve import solve_frames
from astrolog.units import ARCSEC_PER_RAD_PER_1000
from conftest import add_folder, by_name, correct, db, gear, run_normalize
from test_solve import solver
from test_typeless import _frame

CAMERA = "ATR2600M(USB2.0)"  # nell'archivio sintetico: 7 pose, corredo a 560 mm


def _scala(pixel_um, focal_mm, binning=1):
    return pixel_um * binning / focal_mm * ARCSEC_PER_RAD_PER_1000


def _pose(conn, camera=CAMERA):
    return conn.execute(
        "SELECT f.id, f.binning, g.focal_mm FROM frames f JOIN rigs g ON g.id = f.rig_id"
        " JOIN instruments c ON c.id = g.camera_id WHERE c.name = ? AND f.copy_of IS NULL"
        " ORDER BY f.id",
        (camera,),
    ).fetchall()


def _risolvi(conn, frame_id, scala):
    conn.execute(
        "INSERT OR REPLACE INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, solved_at)"
        " VALUES(?, 10, 41, ?, '2026-09-25T00:00:00Z')",
        (frame_id, scala),
    )


def _ricavato(conn, camera=CAMERA):
    return conn.execute(
        "SELECT pixel_from_sky_um FROM instruments WHERE name = ?", (camera,)
    ).fetchone()[0]


def test_the_pixel_is_the_median_of_what_the_sky_measured(client):
    """Ogni posa risolta dice un pixel; la camera prende quello di mezzo, cosi' una posa risolta
    storta -- succede su un campo povero di stelle -- non lo sposta. A bin 2 la scala raddoppia, e
    il pixel fisico no."""
    with db(client) as conn:
        pose = _pose(conn)
        assert len(pose) >= 3, "il banco deve avere almeno tre pose di quella camera"
        for p in pose:
            _risolvi(conn, p["id"], _scala(3.76, p["focal_mm"]))
        conn.execute("UPDATE frames SET binning = 2 WHERE id = ?", (pose[0]["id"],))
        _risolvi(conn, pose[0]["id"], _scala(3.76, pose[0]["focal_mm"], binning=2))
        _risolvi(conn, pose[1]["id"], _scala(9.0, pose[1]["focal_mm"]))  # la risolta storta
        camera_sky.write(conn)
        assert _ricavato(conn) == 3.76


def test_without_a_solved_pose_there_is_no_pixel_from_the_sky(client):
    """Senza cielo non si ricava niente, e niente non e' zero."""
    with db(client) as conn:
        camera_sky.write(conn)
        assert _ricavato(conn) is None


def test_a_pose_that_does_not_say_its_binning_does_not_vote(client):
    """Un binning che l'header non dice vale "non si sa", non 1: quella posa non vota."""
    with db(client) as conn:
        pose = _pose(conn)
        for p in pose:
            _risolvi(conn, p["id"], _scala(3.76, p["focal_mm"]))
        for p in pose:
            conn.execute("UPDATE frames SET binning = NULL WHERE id = ?", (p["id"],))
        camera_sky.write(conn)
        assert _ricavato(conn) is None


def test_the_gear_page_reads_the_pixel_from_the_sky(client):
    """La pagina lo legge accanto a quello dei file, in un campo suo: chi lo mostra dice che e'
    ricavato, e non lo confonde con quello che i file o l'utente hanno scritto."""
    with db(client) as conn:
        for p in _pose(conn):
            _risolvi(conn, p["id"], _scala(3.76, p["focal_mm"]))
        camera_sky.write(conn)
    camera = by_name(gear(client)["instruments"], CAMERA)
    assert (camera["pixel_size_um"], camera["pixel_from_sky_um"]) == (3.76, 3.76)


def test_normalize_writes_it_at_the_end_of_its_round(client):
    """Una posa che cambia camera -- un'unione, una risposta -- ripassa da `normalize`: e' li' che
    il pixel ricavato si rifa', senza aspettare un giro del solver."""
    with db(client) as conn:
        for p in _pose(conn):
            _risolvi(conn, p["id"], _scala(3.76, p["focal_mm"]))
        stages.invalidate(conn, [p["id"] for p in _pose(conn)], "normalize")
        run_normalize(conn)
        assert _ricavato(conn) == 3.76


def test_the_solver_writes_it_at_the_end_of_its_round(client, tmp_path):
    """E alla fine del giro del solver, che e' quando la scala arriva."""
    with db(client) as conn:
        pose = [p["id"] for p in _pose(conn)]
        stages.invalidate(conn, pose, "solve")
        list(solve_frames(conn, exe="astap", run=solver({}), cache=tmp_path / "cache"))
        scala = conn.execute(
            "SELECT scale_arcsec_px FROM frame_wcs WHERE frame_id = ?", (pose[0],)
        ).fetchone()[0]
        focale = _pose(conn)[0]["focal_mm"]
        assert _ricavato(conn) == round(scala * focale / ARCSEC_PER_RAD_PER_1000, 2)


def test_a_camera_that_loses_every_solved_pose_forgets_its_pixel(client):
    """Una camera rimasta senza pose risolte -- un'unione che le porta via, un cielo staccato --
    dimentica il pixel che ne aveva ricavato, invece di tenerne uno che niente sostiene piu'."""
    with db(client) as conn:
        pose = _pose(conn)
        for p in pose:
            _risolvi(conn, p["id"], _scala(3.76, p["focal_mm"]))
        camera_sky.write(conn)
        assert _ricavato(conn) == 3.76
        for p in pose:
            conn.execute("DELETE FROM frame_wcs WHERE frame_id = ?", (p["id"],))
        camera_sky.write(conn)
        assert _ricavato(conn) is None


def test_a_rewritten_copy_does_not_vote(client):
    """Una copia riscritta non e' un'altra posa: il suo cielo non entra nella mediana."""
    with db(client) as conn:
        prima, copia = _pose(conn)[:2]
        conn.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (prima["id"], copia["id"]))
        _risolvi(conn, prima["id"], _scala(3.76, prima["focal_mm"]))
        _risolvi(conn, copia["id"], _scala(9.0, copia["focal_mm"]))
        camera_sky.write(conn)
        assert _ricavato(conn) == 3.76


def test_what_the_user_writes_wins_on_the_page(client):
    """Il pixel scritto sulla scheda e' quello che la pagina mostra come pixel della camera; il
    ricavato resta nel suo campo, e chi mostra la riga lo tace (`attrezzatura.test.tsx`)."""
    with db(client) as conn:
        for p in _pose(conn):
            _risolvi(conn, p["id"], _scala(3.8, p["focal_mm"]))
        camera_sky.write(conn)
    camera = by_name(gear(client)["instruments"], CAMERA)
    assert correct(client, camera["id"], pixel_size_um=3.9).status_code == 200
    dopo = by_name(gear(client)["instruments"], CAMERA)
    assert (dopo["pixel_size_um"], dopo["pixel_from_sky_um"]) == (3.9, 3.8)


def test_calibration_answered_takes_back_the_pixel_its_sky_gave(conn):
    """ "Sono file di calibrazione" stacca il cielo da quei frame, e ne' normalize ne' il solver ci
    ripassano: il pixel che quel cielo faceva ricavare va via con lui."""
    radice = add_folder(conn, "D:/Astro")
    camera = conn.execute(
        "INSERT INTO instruments(kind, name, created_at) VALUES('camera', 'Muta', 'ora')"
    ).lastrowid
    corredo = conn.execute(
        "INSERT INTO rigs(camera_id, focal_mm, created_at) VALUES(?, 500.0, 'ora')", (camera,)
    ).lastrowid
    frame_id = _frame(conn, radice, "dark/a.fits", sky="done")
    conn.execute("UPDATE frames SET rig_id = ?, binning = 1 WHERE id = ?", (corredo, frame_id))
    _risolvi(conn, frame_id, _scala(3.76, 500.0))
    camera_sky.write(conn)
    assert _ricavato(conn, "Muta") == 3.76
    typeless.declare(conn, "D:/Astro/dark", TypeAnswer.CALIBRATION)
    typeless_folders.write(conn)  # come a fine stadio: risolta dal cielo, chiede solo se risposta
    typeless_answer.apply_answer(conn, typeless.row_of(conn, "D:/Astro/dark"))
    assert _ricavato(conn, "Muta") is None
