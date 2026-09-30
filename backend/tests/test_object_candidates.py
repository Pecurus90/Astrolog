"""I candidati del cielo per gli oggetti in dubbio: li scrive chi identifica, la pagina li legge.

Marco, 22/9/2026: una lettura non calcola mai. Il cono sul catalogo per ogni oggetto in dubbio si
fa a fine giro di `identify` (`spine/object_candidates.py`) e si scrive in `object_candidates`; la
pagina li legge. Quali candidati e in che ordine hanno le loro prove in `test_review_objects.py`.
"""

import pytest

from astrolog.spine import (
    identify,
    object_candidates,
    stages,
    typeless,
    typeless_answer,
    typeless_folders,
)
from astrolog.spine.identify import identify_frames
from conftest import add_folder, apply, db, review
from test_typeless import _frame


def _dubbio(pagina):
    """L'oggetto in dubbio col cielo (M 45, che il cielo dice M 31): l'occupante del banco e' in
    dubbio anche lui, ma la sua posa non ha cielo e non ha niente da cliccare."""
    return next(o for o in pagina["objects"] if o["confidence"] == "low" and o["candidates"])


def test_the_page_reads_the_written_candidates_and_does_not_search_the_sky(
    client_banco, monkeypatch
):
    """Aprire Da confermare non fa il cono sul catalogo: i candidati li ha gia' scritti chi ha
    identificato, e la pagina li legge."""
    monkeypatch.setattr(
        identify, "candidates", lambda *a, **k: pytest.fail("la pagina ha cercato nel cielo")
    )
    assert _dubbio(review(client_banco))["candidates"][0]["slug"]


def test_identify_writes_the_candidates_of_the_doubtful_objects_only(client_banco):
    """Solo gli oggetti in dubbio: uno sicuro non ha niente da cliccare, e cercargli i candidati
    sarebbe pagare un cono per niente."""
    with db(client_banco) as conn:
        righe = conn.execute(
            "SELECT DISTINCT o.identity_confidence FROM object_candidates c"
            " JOIN objects o ON o.id = c.object_id"
        ).fetchall()
    assert [r[0] for r in righe] == ["low"]


def test_an_answered_object_takes_its_candidates_away(client_banco):
    """Risposto, l'oggetto non e' piu' in dubbio: la risposta rifa' identify sulle sue pose, e a
    fine giro i suoi candidati se ne vanno."""
    dubbio = _dubbio(review(client_banco))
    apply(client_banco, objects=[{"key": dubbio["key"], "slug": dubbio["candidates"][0]["slug"]}])
    with db(client_banco) as conn:
        assert conn.execute("SELECT COUNT(*) FROM object_candidates").fetchone()[0] == 0


def test_identify_writes_them_only_when_it_worked_some_pose(client_banco, monkeypatch):
    """Il cono costa: un giro senza pose da lavorare non riscrive."""
    chiamate = []
    monkeypatch.setattr(object_candidates, "write", lambda conn: chiamate.append(1))
    with db(client_banco) as conn:
        list(identify_frames(conn))
        assert chiamate == []
        stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "identify")
        list(identify_frames(conn))
    assert chiamate == [1]


def test_calibration_answered_takes_the_candidates_of_that_sky_away(conn):
    """ "Sono file di calibrazione" stacca il cielo da quei frame senza che identify li lavori: i
    candidati che quel cielo dava se ne vanno nella risposta stessa."""
    radice = add_folder(conn, "D:/Astro")
    oggetto = conn.execute(
        "INSERT INTO objects(identity_confidence, created_at) VALUES('low', 'ora')"
    ).lastrowid
    frame_id = _frame(conn, radice, "dark/a.fits", sky="done")
    conn.execute("UPDATE frames SET object_id = ? WHERE id = ?", (oggetto, frame_id))
    conn.execute(
        "INSERT INTO object_candidates(object_id, rank, slug, name) VALUES(?, 0, 'm-31', 'M 31')",
        (oggetto,),
    )
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    typeless_folders.write(conn)  # come a fine stadio: risolta dal cielo, chiede solo se risposta
    typeless_answer.apply_answer(conn, typeless.row_of(conn, "D:/Astro/dark"))
    assert conn.execute("SELECT COUNT(*) FROM object_candidates").fetchone()[0] == 0


@pytest.mark.parametrize(("voci", "attese"), [(22080, [1]), (0, [])])
def test_a_new_catalog_rewrites_the_candidates(db_path, monkeypatch, voci, attese):
    """I candidati vengono dal catalogo: se all'avvio ne entra uno nuovo si riscrivono."""
    from astrolog.api import app
    from astrolog.catalog import load as catalog_load

    chiamate = []
    monkeypatch.setattr(catalog_load, "load_catalog", lambda conn: voci)
    monkeypatch.setattr(object_candidates, "write", lambda conn: chiamate.append(1))
    app._load_catalog(db_path)
    assert chiamate == attese


def test_a_stopped_identify_writes_the_candidates_of_what_it_did(client_banco, monkeypatch):
    """Una corsa fermata a meta' ha gia' messo oggetti in dubbio: i loro candidati si scrivono."""
    chiamate = []
    monkeypatch.setattr(object_candidates, "write", lambda conn: chiamate.append(1))
    with db(client_banco) as conn:
        stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "identify")
        corsa = identify_frames(conn)
        next(corsa)
        corsa.close()
    assert chiamate == [1]


def test_an_identify_that_breaks_before_its_first_pose_still_rewrites(client_banco, monkeypatch):
    """Prima della prima posa identify ha gia' staccato e spazzato: un oggetto che ha perso la posa
    da cui venivano i suoi candidati non deve tenerli fino alla corsa dopo."""
    chiamate = []
    monkeypatch.setattr(object_candidates, "write", lambda conn: chiamate.append(1))

    def rotto(*args, **kwargs):
        raise RuntimeError("guasto finto")

    monkeypatch.setattr(identify, "frame_safely", rotto)
    with db(client_banco) as conn:
        stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "identify")
        with pytest.raises(RuntimeError):
            list(identify_frames(conn))
    assert chiamate == [1]
