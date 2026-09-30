"""Le scritture della scansione: cartella, ricevuta, frame, posizioni. SQL con segnaposto,
mai composto con stringhe.

Vincolo non ovvio: qui non si decide niente (chi entra, chi si salta): si scrive cio' che
`scan.py` ha deciso. Un frame nuovo nasce con tutti gli stadi `pending`.
"""

import json

from ..db.transaction import transaction
from .stages import mark_pending, refresh_waiting

FRAME_COLUMNS = (
    "image_type",
    "date_obs",
    "exposure_s",
    "gain",
    "offset",
    "ccd_temp_c",
    "naxis1",
    "naxis2",
    "binning",
    "pixel_size_um",
    "bayer_pattern",
    "focal_mm_raw",
    "filter_raw",
    "object_raw",
    "telescope_raw",
    "instrument_raw",
    "filter_wheel_raw",
    "focuser_raw",
    "guide_camera_raw",
    "software_raw",
    "asks_camera",
    "asks_filter",
    "names_optics",
    "ra_hint_deg",
    "dec_hint_deg",
    "site_lat",
    "site_lon",
    "site_elev_m",
)
_FIELD_OF = {"focal_mm_raw": "focal_mm", "ra_hint_deg": "ra_deg", "dec_hint_deg": "dec_deg"}


class FolderNotFoundError(ValueError):
    """La cartella non esiste nel DB: guardia del motore, non un caso dell'utente."""


def folder_root(conn, folder_id):
    row = conn.execute(
        "SELECT root_path, retired_at FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if row is None:
        raise FolderNotFoundError(f"cartella inesistente: id={folder_id}")
    return row["root_path"], row["retired_at"]


def start_run(conn, folder_id, now):
    with transaction(conn):
        return conn.execute(
            "INSERT INTO scan_runs(folder_id, started_at) VALUES(?, ?)", (folder_id, now)
        ).lastrowid


def discard_run(conn, run_id):
    """Toglie una ricevuta aperta la cui corsa non ha mai letto quella cartella: il worker era
    occupato, oppure la corsa si e' fermata prima di arrivarci. Tocca solo le righe **aperte**,
    quindi non puo' portarsi via il racconto di una cartella gia' letta."""
    conn.execute("DELETE FROM scan_runs WHERE id = ? AND ended_at IS NULL", (run_id,))


# Una ricevuta porta con se' il **percorso della sua cartella**, che e' quello che l'utente
# riconosce: col solo id, chi la mostra dovrebbe leggersi le cartelle e appaiarle da se'. La
# giunzione e' **interna** perche' una cartella non si cancella, si **ritira** (`api/folders.py`,
# `retired_at`) -- e cancellarla davvero non si puo': `scan_runs.folder_id` la riferisce, e lo
# schema ferma il colpo. Un percorso che manca sarebbe un archivio incoerente, non un caso da
# mostrare a schermo.
SELECT_RUN = (
    "SELECT r.*, f.root_path AS folder_path FROM scan_runs r JOIN folders f ON f.id = r.folder_id"
)


def run_row(conn, run_id):
    return conn.execute(SELECT_RUN + " WHERE r.id = ?", (run_id,)).fetchone()


def run_outcomes(conn, run_ids):
    """Com'e' finita ognuna di quelle ricevute, e basta: chi lo chiede a ogni interrogazione dello
    stato non deve decodificare l'elenco dei file non letti, che puo' contarne migliaia a ricevuta.
    Quelle che non ci sono piu' non tornano."""
    return [
        r
        for r in (
            conn.execute(
                "SELECT id, status, errors, ended_at FROM scan_runs WHERE id = ?", (run_id,)
            ).fetchone()
            for run_id in run_ids
        )
        if r is not None
    ]


STATUSES = ("ok", "stopped", "aborted", "error")
REASONS = (None, "root_unreachable", "stop_requested", "internal_error", "database_error")
# Perche' un file non e' entrato: il sistema non lo apre, non e' un FITS, il suo nome non si puo'
# scrivere, o un guasto che nessuno aspettava (la traccia sta nel log).
FILE_ERRORS = ("file_unreadable", "header_unreadable", "name_not_utf8", "internal_error")
# Perche' un file si salta: si conta per motivo, calibrazioni comprese (Marco, 2026-09-11).
SKIP_REASONS = ("calibration", "stack", "still_writing")


# Cio' che la scansione lascia fuori e la ricevuta porta per intero: un elenco ciascuno, e in
# `scan_runs` una colonna `<nome>_json`. Chi li passa, li scrive o li mostra parte da questi nomi.
# I file non letti no: possono essere migliaia, e si leggono a pagine (`errors_detail_json`).
RECEIPT_LISTS = ("unreadable_dirs", "hidden_dirs", "linked_dirs", "skipped_by_reason")


def finish_run(conn, run_id, status, reason, counts, left_out, errors, now):  # noqa: PLR0913
    """Chiude la ricevuta; `left_out` e' `{nome: elenco}` coi nomi di `RECEIPT_LISTS`, `errors`
    i file non letti. Stato, motivo e motivi dei file sono codici chiusi: una frase o un nome di
    classe qui e' un errore di programmazione."""
    if status not in STATUSES or reason not in REASONS:
        raise ValueError(f"esito fuori dal vocabolario: {status}/{reason}")
    codes = {e["reason"] for e in errors} - set(FILE_ERRORS)
    codes |= {e["reason"] for e in left_out.get("skipped_by_reason", ())} - set(SKIP_REASONS)
    if codes:
        raise ValueError(f"motivi fuori dal vocabolario: {sorted(codes)}")
    columns = ", ".join(f"{name}_json = ?" for name in RECEIPT_LISTS)
    with transaction(conn):
        conn.execute(
            "UPDATE scan_runs SET ended_at = ?, status = ?, reason = ?, found = ?, new = ?,"  # noqa: S608 - colonne da una costante nostra
            " unchanged = ?, duplicates = ?, missing = ?, skipped = ?, errors = ?, online_only = ?,"
            f" errors_detail_json = ?, {columns} WHERE id = ?",
            (
                now,
                status,
                reason,
                counts["found"],
                counts["new"],
                counts["unchanged"],
                counts["duplicates"],
                counts["missing"],
                counts["skipped"],
                counts["errors"],
                counts["online_only"],
                _as_json(errors),
                *(_as_json(left_out.get(name)) for name in RECEIPT_LISTS),
                run_id,
            ),
        )
        # L'elenco dei file non letti lo tiene l'ultima ricevuta di una cartella, e se quella
        # corsa non e' arrivata in fondo anche l'ultima che ci e' arrivata (Marco, 2026-09-11):
        # quei file si riprovano a ogni scansione arrivata in fondo. Le altre tengono i numeri, e
        # il database non cresce a ogni giro di un NAS, nemmeno se la condivisione cade a ogni giro.
        folder = conn.execute("SELECT folder_id FROM scan_runs WHERE id = ?", (run_id,)).fetchone()
        last_ok = conn.execute(
            "SELECT MAX(id) FROM scan_runs WHERE folder_id = ? AND status = 'ok' AND id < ?",
            (folder[0], run_id),
        ).fetchone()[0]
        conn.execute(
            "UPDATE scan_runs SET errors_detail_json = NULL"
            " WHERE folder_id = ? AND id < ? AND id IS NOT ?",
            (folder[0], run_id, run_id if status == "ok" else last_ok),
        )


def _as_json(items):
    """Un elenco come JSON leggibile, accenti compresi, o NULL se e' vuoto."""
    return json.dumps(items, ensure_ascii=False) if items else None


def position(conn, folder_id, rel_path):
    return conn.execute(
        "SELECT id, frame_id, filesize, mtime, status FROM positions"
        " WHERE folder_id = ? AND rel_path = ?",
        (folder_id, rel_path),
    ).fetchone()


def set_position_present(conn, position_id, now):
    with transaction(conn):
        conn.execute(
            "UPDATE positions SET status = 'present', seen_at = ? WHERE id = ?", (now, position_id)
        )
        refresh_waiting(conn, [_frame_of(conn, position_id)])


def _frame_of(conn, position_id):
    return conn.execute("SELECT frame_id FROM positions WHERE id = ?", (position_id,)).fetchone()[0]


def home_timezone(conn):
    """Il fuso del sito di casa, o `None`: e' quello della notte di una posa che non dice dove."""
    row = conn.execute("SELECT timezone FROM sites WHERE is_default = 1").fetchone()
    return None if row is None else row["timezone"]


def frame_id_by_hash(conn, frame_hash):
    row = conn.execute("SELECT id FROM frames WHERE frame_hash = ?", (frame_hash,)).fetchone()
    return row["id"] if row else None


def insert_frame(conn, fields, frame_hash, header_json, now, night):  # noqa: PLR0913
    """Il frame nuovo, coi grezzi dell'header, la sua notte `(notte, fuso, istante)` e tutti gli
    stadi da fare. Dentro una transazione aperta dal chiamante."""
    values = [fields.get(_FIELD_OF.get(c, c)) for c in FRAME_COLUMNS]
    cols = ", ".join(f'"{c}"' for c in FRAME_COLUMNS)
    marks = ", ".join("?" for _ in FRAME_COLUMNS)  # segnaposto-ok: le colonne, non le righe
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, header_json, created_at, local_night, local_tz,"  # noqa: S608 - colonne fisse
        f" night_instant, {cols}) VALUES(?, ?, ?, ?, ?, ?, {marks})",
        [frame_hash, header_json, now, *night, *values],
    ).lastrowid
    mark_pending(conn, frame_id, now)
    return frame_id


def upsert_position(conn, frame_id, folder_id, rel_path, filesize, mtime, now):  # noqa: PLR0913
    """La posizione di quel file; se allo stesso percorso c'era un altro file, passa a questo, e
    il frame di prima puo' aver perso la cartella che gli dava la risposta sul tipo."""
    prima = position(conn, folder_id, rel_path)
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, status, seen_at)"
        " VALUES(?, ?, ?, ?, ?, 'present', ?)"
        " ON CONFLICT(folder_id, rel_path) DO UPDATE SET frame_id = excluded.frame_id,"
        " filesize = excluded.filesize, mtime = excluded.mtime, status = 'present',"
        " seen_at = excluded.seen_at",
        (frame_id, folder_id, rel_path, filesize, mtime, now),
    )
    refresh_waiting(conn, {frame_id} | ({prima["frame_id"]} if prima else set()))


def mark_missing(conn, folder_id, seen, untouched, now):
    """Le posizioni della cartella non incontrate diventano `missing`, mai cancellate; quelle
    sotto una sottocartella in `untouched` (non apribile) restano com'erano."""
    missing = 0
    with transaction(conn):
        for r in conn.execute(
            "SELECT id, frame_id, rel_path FROM positions"
            " WHERE folder_id = ? AND status = 'present'",
            (folder_id,),
        ).fetchall():
            if any(r["rel_path"].startswith(prefix + "/") for prefix in untouched):
                continue
            if r["rel_path"] not in seen:
                conn.execute(
                    "UPDATE positions SET status = 'missing', seen_at = ? WHERE id = ?",
                    (now, r["id"]),
                )
                refresh_waiting(conn, [r["frame_id"]])
                missing += 1
    return missing
