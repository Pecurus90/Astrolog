"""Impostazioni › Scansioni (tavola v82, `SezioneServizi`): una scansione e' un gesto, con le sue
cartelle, cosa e' entrato, cosa e' rimasto fuori e perche'. Le ricevute si scrivono a mano: la
regola e' sul raggruppamento, non sulla lettura dei file."""

import json

from astrolog.db.connect import connect
from conftest import add_folder

T0 = "2026-11-15T21:05:00+00:00"


def _folder(conn, path):
    return add_folder(conn, path)


def _run(conn, folder_id, *, batch=None, ended=True, status="ok", reason=None, **counts):
    errors_detail = counts.pop("errors_detail", None)
    lists = {k: counts.pop(k, None) for k in ("unreadable_dirs", "hidden_dirs", "linked_dirs")}
    skipped = counts.pop("skipped_by_reason", [])
    cols = {
        "folder_id": folder_id,
        "batch": batch,
        "started_at": T0,
        "ended_at": "2026-11-15T21:08:40+00:00" if ended else None,
        "status": status if ended else None,
        "reason": reason,
        "skipped_by_reason_json": json.dumps(skipped),
        "errors_detail_json": None if errors_detail is None else json.dumps(errors_detail),
        **{f"{k}_json": json.dumps(v or []) for k, v in lists.items()},
        **counts,
    }
    names = ", ".join(cols)
    marks = ", ".join("?" for _ in cols)
    cur = conn.execute(f"INSERT INTO scan_runs({names}) VALUES({marks})", tuple(cols.values()))
    conn.commit()
    return cur.lastrowid


def _scans(client):
    r = client.get("/api/v1/scans")
    assert r.status_code == 200, r.text
    return r.json()


def test_scansiona_on_two_folders_is_one_scan(client_vuoto, db_path):
    """Il gesto e' uno: le due cartelle in una carta, i conti sommati."""
    conn = connect(db_path)
    a, b = _folder(conn, "D:/Astro/2026"), _folder(conn, "E:/Sole")
    first = _run(conn, a, new=120, unchanged=3, duplicates=2)
    _run(conn, b, batch=first, new=66, duplicates=2,
         skipped_by_reason=[{"reason": "calibration", "count": 4}])  # fmt: skip
    conn.close()
    body = _scans(client_vuoto)
    assert body["total"] == 1
    scan = body["items"][0]
    assert scan["id"] == first and scan["folders"] == ["D:/Astro/2026", "E:/Sole"]
    assert scan["outcome"] == "completed" and scan["new"] == 186
    assert scan["duration_s"] == 220
    assert scan["left_out"] == [
        {"reason": "unchanged", "count": 3},
        {"reason": "duplicates", "count": 4},
        {"reason": "calibration", "count": 4},
    ]


def test_the_newest_scan_comes_first(client_vuoto, db_path):
    conn = connect(db_path)
    a = _folder(conn, "D:/Astro")
    old = _run(conn, a)
    new = _run(conn, a)
    conn.close()
    assert [s["id"] for s in _scans(client_vuoto)["items"]] == [new, old]


def test_a_stop_is_said_and_a_fault_is_worse(client_vuoto, db_path):
    """Interrotta a mano su una cartella, bloccata sull'altra: la carta dice bloccata, col perche'
    e la cartella; Riprova solo sulla piu' recente."""
    conn = connect(db_path)
    a, b = _folder(conn, "D:/Astro"), _folder(conn, "E:/Esterno")
    stopped = _run(conn, a, status="stopped", reason="stop_requested")
    first = _run(conn, a, status="stopped", reason="stop_requested")
    _run(conn, b, batch=first, status="aborted", reason="root_unreachable")
    conn.close()
    newest, older = _scans(client_vuoto)["items"]
    assert newest["outcome"] == "blocked" and newest["reason"] == "root_unreachable"
    assert newest["reason_folder"] == "E:/Esterno" and newest["can_retry"] is True
    assert older["id"] == stopped and older["outcome"] == "stopped" and older["reason"] is None
    assert older["can_retry"] is False


def test_a_receipt_left_open_without_the_worker_is_blocked(client_vuoto, db_path):
    """Un processo morto lascia la ricevuta aperta: non e' «in corso» per sempre."""
    conn = connect(db_path)
    _run(conn, _folder(conn, "D:/Astro"), ended=False)
    conn.close()
    scan = _scans(client_vuoto)["items"][0]
    assert (scan["outcome"], scan["reason"], scan["duration_s"]) == ("blocked", "left_open", None)


def test_unread_files_the_first_five_then_all(client_vuoto, db_path):
    conn = connect(db_path)
    detail = [{"file": f"M31/L_{i:04}.fits", "reason": "header_unreadable"} for i in range(7)]
    sid = _run(conn, _folder(conn, "D:/Astro"), errors=7, errors_detail=detail,
               unreadable_dirs=["D:/Astro/privata"])  # fmt: skip
    conn.close()
    scan = _scans(client_vuoto)["items"][0]
    assert scan["unread"] == 7 and scan["unread_kept"] is True
    assert scan["unread_files"] == detail[:5]
    assert scan["dirs_left_out"] == [{"path": "D:/Astro/privata", "why": "unreadable"}]
    tutti = client_vuoto.get(f"/api/v1/scans/{sid}/unread").json()
    assert (tutti["total"], tutti["items"]) == (7, detail)


def test_an_unread_list_no_longer_kept_says_so(client_vuoto, db_path):
    conn = connect(db_path)
    sid = _run(conn, _folder(conn, "D:/Astro"), errors=3)  # list dropped by a newer scan
    conn.close()
    scan = _scans(client_vuoto)["items"][0]
    assert scan["unread"] == 3 and scan["unread_kept"] is False and scan["unread_files"] == []
    r = client_vuoto.get(f"/api/v1/scans/{sid}/unread")
    assert r.status_code == 410 and r.json()["detail"]["code"] == "errors_not_kept"
    r = client_vuoto.get("/api/v1/scans/9999/unread")
    assert r.status_code == 404 and r.json()["detail"]["code"] == "scan_not_found"


def test_no_scan_yet(client_vuoto):
    assert _scans(client_vuoto) == {"items": [], "total": 0, "limit": 20, "offset": 0}
