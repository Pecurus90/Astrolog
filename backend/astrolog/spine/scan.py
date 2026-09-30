"""Lo stadio di scansione: dalle cartelle ai frame, leggendo l'header e 64 KB di pixel dal
centro (l'impronta), mai il resto.

Vincolo non ovvio: un generatore che committa per frame ed emette un evento per file; chi lo
chiude (Stop) lo trova a transazione chiusa e la ricevuta dice `stopped` con i numeri veri.
Radice irraggiungibile, prima o a meta' corsa, = `aborted` senza toccare una posizione. Un file
che non si legge, per qualunque motivo, si salta e la ricevuta lo nomina: non ferma la corsa.
Calibrazione e stack si saltano e si contano per motivo -- e con loro i file che non dicono che
file sono, nelle cartelle che l'utente ha chiamato di calibrazione, se non sono gia' in archivio.
Un file solo online non si apre, perche' aprirlo lo scaricherebbe: si conta nella ricevuta e si
rivede la volta dopo.
"""

import logging
import os
import sqlite3
import time
from functools import partial

from ..clock import night_date, night_instant, now_iso
from ..db.transaction import transaction
from ..fits.frame_type import CALIBRATION_TYPES, UNKNOWN
from ..fits.header_fields import extract_fields
from ..fits.header_read import HeaderReadError, frame_fingerprint, header_to_json, read_frame
from ..fits.walk import long_path, walk_dir
from ..place import timezone_of_frame
from . import header_asks, typeless
from . import scan_store as store
from .stage_run import receipt

log = logging.getLogger(__name__)

COUNTS = ("found", "new", "unchanged", "duplicates", "missing", "skipped", "errors", "online_only")
DEFAULT_MIN_AGE_S = 30  # un file scritto da meno di tanto e' ancora in scrittura: si rivede dopo


class _RootLostError(Exception):
    """Interno: la radice e' sparita, fra il pre-controllo e il walk o a meta' corsa."""


def root_readable(root):
    """La radice si apre davvero? `isdir` non basta: una condivisione caduta puo' esistere
    come cartella e non rispondere. E' l'unico controllo di raggiungibilita' della spina."""
    try:
        os.scandir(long_path(root)).close()
    except OSError:
        return False
    return True


def rel_path(abs_path, root):
    """Il percorso relativo alla radice, con `/` su ogni sistema: e' la chiave di `positions`."""
    return os.path.relpath(abs_path, root).replace(os.sep, "/")


# un NAS rimontato con un'altra precisione tronca l'mtime al millisecondo: non e' una modifica
MTIME_TOLERANCE_S = 0.001


def is_unchanged(known, size, mtime):
    """Il pre-controllo incrementale: stessa dimensione e stesso mtime al millisecondo."""
    return (
        known is not None
        and known["filesize"] == size
        and abs(known["mtime"] - mtime) < MTIME_TOLERANCE_S
    )


def _receipt(status, reason, run_id, folder_id, counts, left_out=None, errors=()):  # noqa: PLR0913
    lists = {name: list((left_out or {}).get(name, ())) for name in store.RECEIPT_LISTS}
    return receipt(status, reason, counts, errors, run_id=run_id, folder_id=folder_id, **lists)


def scan_folder(conn, folder_id, *, run_id=None, min_age_s=DEFAULT_MIN_AGE_S, now_fn=time.time):  # noqa: C901
    """Scansiona la cartella `folder_id`; yield di un evento per file e, in coda, la
    ricevuta. `run_id` e' la riga di `scan_runs` gia' aperta da chi ha avviato (per
    rispondere subito con l'id), o None per aprirla qui."""
    root, _retired = store.folder_root(conn, folder_id)
    counts = dict.fromkeys(COUNTS, 0)
    online, seen, errors, traced = [], set(), [], set()
    left_out = {name: [] for name in store.RECEIPT_LISTS}
    skipped, unreadable = left_out["skipped_by_reason"], left_out["unreadable_dirs"]
    if run_id is None:
        run_id = store.start_run(conn, folder_id, now_iso())
    log.info("scan: inizio", extra={"scan_run_id": run_id, "folder_id": folder_id, "root": root})
    if not root_readable(root):
        log.warning("scan: radice irraggiungibile", extra={"scan_run_id": run_id, "root": root})
        store.finish_run(
            conn, run_id, "aborted", "root_unreachable", counts, left_out, errors, now_iso()
        )
        yield _receipt("aborted", "root_unreachable", run_id, folder_id, counts)
        return

    status, reason = "ok", None
    try:
        files = walk_dir(
            root,
            unreadable=unreadable,
            hidden=left_out["hidden_dirs"],
            online_only=online,
            linked=left_out["linked_dirs"],
        )
        if any(os.path.normpath(d) == os.path.normpath(root) for d in unreadable):
            raise _RootLostError  # caduta fra il controllo e il walk
        for dirs in (unreadable, left_out["hidden_dirs"], left_out["linked_dirs"]):
            # dalla radice in giu', come i file non letti: il percorso intero e' quello della
            # cartella, che la ricevuta dice gia'. Un nome che non e' UTF-8 non si scrive.
            dirs[:] = [_shown(rel_path(d, root)) for d in dirs]
        total = len(files)
        counts["found"] = total + len(online)
        net = (conn, folder_id, root, counts, errors, seen, run_id, traced)
        for abs_path in online:
            rel = rel_path(abs_path, root)
            _safely(*net, rel, partial(_not_on_disk, conn, folder_id, rel, counts, seen))
        for i, abs_path in enumerate(files, start=1):
            rel = rel_path(abs_path, root)
            one = (conn, folder_id, root, abs_path, rel, counts, skipped, seen, min_age_s, now_fn)
            _safely(*net, rel, partial(_one_file, *one))
            yield {
                "current": i,
                "total": total,
                "file": _shown(os.path.basename(abs_path)),
                "run_id": run_id,
                "folder_id": folder_id,
                **counts,
            }
        # Sotto una cartella che non si e' potuta aprire i file non sono spariti: non si sa. Le
        # loro posizioni restano com'erano -- e la ricevuta le nomina gia' dalla radice in giu',
        # che e' la stessa forma delle posizioni.
        counts["missing"] = store.mark_missing(conn, folder_id, seen, unreadable, now_iso())
    except GeneratorExit:
        status, reason = "stopped", "stop_requested"
        raise
    except _RootLostError:
        # la radice e' caduta: si smette senza segnare "non trovato" file che ci sono
        status, reason = "aborted", "root_unreachable"
        log.warning("scan: radice caduta", extra={"scan_run_id": run_id})
    except Exception as err:
        # il database che non risponde (disco pieno, occupato) non e' un file che non si legge
        status = "error"
        reason = "database_error" if isinstance(err, sqlite3.Error) else "internal_error"
        log.exception("scan: errore di sistema", extra={"scan_run_id": run_id})
        raise
    finally:
        # un guasto a meta' scrittura: se il database risponde, la ricevuta si chiude lo stesso
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        store.finish_run(conn, run_id, status, reason, counts, left_out, errors, now_iso())
        log.info("scan: fine", extra={"scan_run_id": run_id, "status": status, **counts})

    yield _receipt(status, reason, run_id, folder_id, counts, left_out, errors)


def _shown(name):
    """Il nome come l'archivio lo puo' scrivere e la pagina mostrare. Python porta i byte di un
    nome che non e' UTF-8 come surrogati, che sqlite3 e il JSON rifiutano: diventano `?`."""
    return name.encode("utf-8", "replace").decode("utf-8")


def _safely(conn, folder_id, root, counts, errors, seen, run_id, traced, rel, work):  # noqa: PLR0913
    """Un file dentro la sua rete: `work()` lo legge o lo conta, e se il file non si legge -- per
    qualunque motivo -- la ricevuta lo nomina col suo codice e la corsa va avanti (Marco,
    2026-09-11)."""
    code = "name_not_utf8" if _shown(rel) != rel else _failure(work, root, run_id, traced)
    if code is not None:
        _count_error(conn, folder_id, rel, code, counts, errors, seen, run_id)


def _failure(work, root, run_id, traced):
    """Perche' `work()` non ha letto il file, in codice, o None se l'ha letto. Il sistema che non
    apre un file lo dice con un numero d'errore (permessi, file sparito o bloccato); astropy dice
    "non e' un FITS" con un `OSError` senza numero. La radice caduta e il database che non
    risponde non sono un file: fermano la corsa."""
    try:
        work()
    except (HeaderReadError, OSError) as err:
        cause = err.cause if isinstance(err, HeaderReadError) else err
        if isinstance(cause, OSError) and not root_readable(root):
            raise _RootLostError from err  # nello stat o dentro la lettura dell'header
        if isinstance(cause, OSError) and cause.errno is not None:
            return "file_unreadable"
        return "header_unreadable"
    except Exception as err:
        if isinstance(err, sqlite3.Error):
            raise
        # Un guasto che nessuno aspettava si nomina come gli altri. La traccia va nel log una volta
        # per tipo: uguale su mille file, mille tracce riempirebbero i 20 MB del log.
        if type(err) not in traced:
            traced.add(type(err))
            log.exception("scan: errore imprevisto", extra={"scan_run_id": run_id})
        return "internal_error"
    return None


def _not_on_disk(conn, folder_id, rel, counts, seen):
    """Un FITS solo online: non si apre -- aprirlo lo scaricherebbe -- e si rivede alla prossima
    scansione. Se era gia' in archivio non e' sparito: e' li', solo non sul disco."""
    counts["online_only"] += 1
    pos = store.position(conn, folder_id, rel)
    if pos is not None:
        seen.add(rel)
        if pos["status"] != "present":  # era "non trovata", ed e' ricomparsa: solo non sul disco
            store.set_position_present(conn, pos["id"], now_iso())


def _count_error(conn, folder_id, rel, code, counts, errors, seen, run_id):  # noqa: PLR0913
    counts["errors"] += 1
    errors.append({"file": _shown(rel), "reason": code})
    # un nome che non si scrive non ha una posizione, e chiederla al DB con quel nome fallirebbe
    if code != "name_not_utf8" and store.position(conn, folder_id, rel) is not None:
        seen.add(rel)  # il file c'e', anche se non si legge: non e' "non trovato"
    log.warning(
        "scan: file non letto", extra={"scan_run_id": run_id, "file": _shown(rel), "error": code}
    )


def _one_file(conn, folder_id, root, abs_path, rel, counts, skipped, seen, min_age_s, now_fn):  # noqa: PLR0913
    """Un file: pre-controllo incrementale, eta', header, tipo, impronta, scrittura."""
    st = os.stat(long_path(abs_path))
    size, mtime = st.st_size, st.st_mtime
    pos = store.position(conn, folder_id, rel)
    now = now_iso()
    if is_unchanged(pos, size, mtime):
        seen.add(rel)
        counts["unchanged"] += 1
        if pos["status"] != "present":
            store.set_position_present(conn, pos["id"], now)
        return
    if now_fn() - mtime < min_age_s:
        _skip(rel, "still_writing", counts, skipped, seen, pos)
        return
    header, block = read_frame(long_path(abs_path))
    if os.stat(long_path(abs_path)).st_size != size:
        _skip(rel, "still_writing", counts, skipped, seen, pos)  # cresciuto mentre si leggeva
        return
    fields = extract_fields(header, abs_path)
    kind = fields["image_type"]
    if kind in CALIBRATION_TYPES or kind == "stack":
        _skip(rel, "stack" if kind == "stack" else "calibration", counts, skipped, seen, pos)
        return
    # Un file che non dice che file e' non e' un light: se l'utente ha gia' detto che in quella
    # cartella ci sono file di calibrazione, si salta alla porta come quelli che lo dicono da
    # soli. Altrimenti entra e aspetta: il cielo non lo prende finche' non si sa che file e'
    # (`spine/stages.py`, chi e' pronto), e non conta nemmeno nel residuo della spina. Un file
    # che e' gia' un frame invece entra anche li': se ci e' stato spostato, saltato sembrerebbe
    # sparito, che tiene le ore; con la posizione nuova lo stacco lo trova
    # (`typeless_answer.detach_waiting`).
    detto = typeless.answer_at(conn, root, rel) if kind == UNKNOWN else None
    fingerprint = frame_fingerprint(long_path(abs_path), header, block)
    if detto == typeless.CALIBRATION and store.frame_id_by_hash(conn, fingerprint) is None:
        _skip(rel, "calibration", counts, skipped, seen, pos)
        return
    with transaction(conn):
        frame_id = store.frame_id_by_hash(conn, fingerprint)
        if frame_id is None:
            notte = night_of(conn, fields, mtime)
            giudicati = {**fields, **header_asks.of(fields)}
            frame_id = store.insert_frame(
                conn, giudicati, fingerprint, header_to_json(header), now, notte
            )
            counts["new"] += 1
        elif pos is not None and pos["frame_id"] == frame_id:
            counts["unchanged"] += 1  # toccato sul disco (magari l'header), stessi pixel
        else:
            counts["duplicates"] += 1
        store.upsert_position(conn, frame_id, folder_id, rel, size, mtime, now)
    seen.add(rel)


def night_of(conn, fields, mtime):
    """(notte, fuso, istante) della posa, scritti quando entra: da mezzogiorno a mezzogiorno nel
    fuso delle coordinate dell'header, o del sito di casa, o in UTC (fuso `None`), a partire
    dall'istante di `clock.night_instant`."""
    fuso = timezone_of_frame(
        fields.get("site_lat"), fields.get("site_lon"), store.home_timezone(conn)
    )
    istante = night_instant(fields.get("date_obs"), mtime)
    return night_date(istante, fuso), fuso, istante


def _skip(rel, why, counts, skipped, seen, pos):  # noqa: PLR0913
    """Un file saltato si conta per motivo, non per nome (Marco, 2026-09-11)."""
    counts["skipped"] += 1
    entry = next((e for e in skipped if e["reason"] == why), None)
    if entry is None:
        entry = {"reason": why, "count": 0}
        skipped.append(entry)
    entry["count"] += 1
    if pos is not None:
        seen.add(rel)
