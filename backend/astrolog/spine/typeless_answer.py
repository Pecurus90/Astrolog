"""La risposta dell'utente su una cartella di frame che non dicono **che file sono**: cosa rimette
in coda, e cosa stacca.

Sta accanto alla domanda (`spine/typeless.py`) e non dentro di lei perche' la domanda la legge
anche lo stadio di scansione, prima di far entrare un file: se le due cose stessero insieme,
`scan` arriverebbe per un passo agli store di `identify` e di `group`, che sono di quegli stadi e
di nessun altro (il contratto in `backend/pyproject.toml`).
"""

from ..fits.frame_type import UNKNOWN
from . import (
    camera_sky,
    gear_usage,
    group_store,
    identify_store,
    mosaic,
    object_candidates,
    solve_store,
    typeless_folders,
)
from . import frame_folder as folder
from . import typeless as domanda
from .stages import FOLDER_SAYS, WAITING_FROM, WAITING_SQL, invalidate


def detach(conn, frame_ids):
    """Stacca da quei frame cio' che il cielo aveva scritto: l'oggetto, la notte, la sessione, il
    cielo misurato e il pannello del mosaico.

    Serve a chi cambia idea. Un frame che una risposta di prima aveva mandato avanti e' stato
    risolto e attaccato a un oggetto: da adesso aspetta di nuovo una risposta, quindi gli stadi
    che quei conti li avrebbero rifatti non lo prendono piu', e senza questo stacco le sue ore
    resterebbero li' per sempre. Gli oggetti, le sessioni e le notti rimasti senza frame li
    spazzano `identify` e `group` alla prima corsa -- e chi risponde ne avvia una, perche' i
    frame tornano nell'elenco di quelli rimessi in coda."""
    if not frame_ids:
        return
    identify_store.detach(conn, frame_ids)
    group_store.detach(conn, frame_ids)
    # Anche cio' che il cielo aveva misurato, e non e' pulizia di comodo: il solver cerca un cielo
    # gia' trovato per lo STESSO `OBJECT` (`solve_store.sister_solution`), quindi un frame di
    # calibrazione che si tenesse il suo WCS continuerebbe a suggerire dove puntare agli altri.
    solve_store.detach(conn, frame_ids)
    # senza cielo la posa non sta in un pannello ne' in un mosaico, e i mosaici che lascia si pesano
    mosaic.settle(conn, mosaic.leave(conn, frame_ids))


def apply_answer(conn, row, now=None):
    """Porta la risposta sui frame di quel gruppo e torna quelli rimessi in coda.

    "Sono foto del cielo": vanno avanti, perche' aspettavano gia' in fila davanti all'oggetto; e
    quelli risolti a cui una risposta "calibrazione" di prima ha staccato il cielo tornano in fila
    **dal cielo**, che lo rimette dalla sua cache. Una rinuncia del cielo non si rifa': non e' in
    cache, e costerebbe fino al tempo massimo per lo stesso esito. "Sono file di calibrazione": si
    fermano davanti all'oggetto, anche se una risposta di prima li aveva gia' mandati avanti, e si
    staccano. Le cartelle della domanda non si riscrivono: una risposta non cambia quante pose
    conta la sua, e la risposta stessa si legge dalla sua casa."""
    frames = domanda.frames_of(conn, row)
    if row["answer"] == domanda.LIGHT:
        invalidate(conn, solve_store.lost_sky(conn, frames), "solve", now)
    else:
        _stop(conn, frames, now)
    return frames


# Chi aspetta in una cartella viva e porta ancora cio' che gli stadi dopo il cielo hanno scritto. Si
# guarda cio' che porta, non lo stato di `identify`: una `invalidate` passata nel frattempo lo
# rimette `pending` senza staccare niente. **Senza cartella viva non si stacca**: il file sparito o
# la cartella ritirata tengono le loro ore come ogni altro frame, e nessuno potrebbe rispondere.
_WAITING_AND_ATTACHED = f"""
SELECT f.id FROM frames f
WHERE {WAITING_SQL} AND (f.object_id IS NOT NULL OR f.night_id IS NOT NULL)
  AND ({folder.KEY_OF_FRAME}) IS NOT NULL
"""  # noqa: S608 - frammenti costanti della spina


# Chi ha perso il cielo per uno stacco e sta in una cartella viva che non lo ferma -- senza risposta
# o detta "foto del cielo" --: il cielo lo rimette solo il solver, dalla sua cache. Senza cartella
# viva, o in una detta di calibrazione, resta fermo com'e'.
_TYPELESS = f"SELECT f.id FROM frames f WHERE f.image_type = '{UNKNOWN}'"  # noqa: S608 - costanti
_LET_GO = (
    f"SELECT ({folder.KEY_OF_FRAME}) IS NOT NULL"  # noqa: S608 - frammenti costanti della spina
    f" AND IFNULL({FOLDER_SAYS}, '') <> '{domanda.CALIBRATION}' FROM frames f WHERE f.id = ?"
)


def detach_waiting(conn, now=None):
    """Ferma e stacca i frame che aspettano di nuovo di sapere che file sono, e rimette in fila dal
    cielo quelli che l'avevano perso e stanno in una cartella viva che non li ferma; torna le due
    liste. Un frame che una risposta aveva mandato avanti, finito in una cartella che non ha
    risposto, torna ad aspettare, e cosi' qualunque frame senza tipo finito in una cartella detta di
    calibrazione: senza lo stacco terrebbe l'oggetto e le ore. Rimesso in una cartella che non lo
    ferma, il cielo glielo rida' la cache del solver. La chiama chi cambia la cartella di un frame:
    la corsa dopo la scansione, il ritiro e la riattivazione di una cartella. Legge il segno
    dell'attesa, che chi ha cambiato la cartella ha gia' riscritto, e alla fine riscrive le
    cartelle della domanda."""
    frames = [r[0] for r in conn.execute(_WAITING_AND_ATTACHED)]
    if frames:
        _stop(conn, frames, now)
    lost = solve_store.lost_sky(conn, [r[0] for r in conn.execute(_TYPELESS)])
    requeued = [i for i in lost if conn.execute(_LET_GO, (i,)).fetchone()[0]]
    invalidate(conn, requeued, "solve", now)
    typeless_folders.write(conn)
    return frames, requeued


def _stop(conn, frames, now):
    """Rimette quei frame davanti all'oggetto e stacca cio' che il cielo aveva scritto."""
    invalidate(conn, frames, WAITING_FROM, now)
    detach(conn, frames)
    # il cielo, l'oggetto e la notte staccati spostano il pixel ricavato, l'uso dell'attrezzatura
    # e i candidati: si rifanno qui, perche' nessuno stadio lavora piu' questi frame
    camera_sky.write(conn)
    gear_usage.write(conn)
    object_candidates.write(conn)
