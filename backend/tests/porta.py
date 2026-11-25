"""La porta sola fra le prove e la pipeline che riempie un archivio (passo 40.2): `populate`,
`scan`, `run_normalize` e la fixture `archive` del conftest passano tutte da qui. Una fetta del 40
che toglie uno stadio vecchio cambia questo file, non le prove."""

import sqlite3
from enum import IntEnum
from typing import Any

from astrolog.spine import stages, typeless_folders
from astrolog.spine.identify import identify_frames
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder


class Upto(IntEnum):
    """Fin dove si riempie: ogni passo comprende quelli prima."""

    SCANNED = 1
    NORMALIZED = 2
    IDENTIFIED = 3


def fill(conn: sqlite3.Connection, folder_id: int | None, upto: Upto) -> Any:
    """Porta l'archivio fino a `upto` e torna la ricevuta dell'ultimo stadio girato. Senza
    `folder_id` non si scansiona: si riprendono gli stadi sui frame che ci sono."""
    receipt = None
    if folder_id is not None:
        receipt = list(scan_folder(conn, folder_id))[-1]
    if upto >= Upto.NORMALIZED:
        receipt = list(normalize_frames(conn))[-1]
    if upto >= Upto.IDENTIFIED:
        # Nella suite il solver non gira: le pose che avrebbe preso restano "stelle ma nessuna
        # soluzione", il cielo che non sa dire (`stages.ready`).
        solve, failed = stages.StageName.SOLVE, stages.StageStatus.FAILED
        for frame_id in stages.ready(conn, solve):
            stages.set_status(conn, frame_id, solve, failed, reason="no_solution")
        typeless_folders.write(conn)  # come a fine cielo
        receipt = identify(conn)
    return receipt


def identify(conn: sqlite3.Connection) -> Any:
    """Solo il riconoscimento, per i banchi che scrivono le pose a mano col loro cielo."""
    return list(identify_frames(conn))[-1]
