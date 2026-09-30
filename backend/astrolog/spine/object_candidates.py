"""I candidati del cielo per gli oggetti in dubbio: cio' che Da confermare fa cliccare.

Una lettura non calcola mai (Marco, 22/9/2026): il cono sul catalogo per ogni oggetto in dubbio si
fa qui, a fine giro di `identify` -- e quando un catalogo nuovo o una risposta "sono file di
calibrazione" cambiano cio' da cui dipende -- e si scrive in `object_candidates`. La pagina li legge
(`api/review_page.py`).

Vincolo non ovvio: solo gli oggetti **in dubbio**. Uno sicuro non ha niente da cliccare, e il cono
costa: pagarlo per tutto l'archivio sarebbe pagarlo per niente.
"""

from ..db.replace_table import replace_rows
from . import identify
from . import objects as obj
from .identify_decide import DOUBT

_COLONNE = ("object_id", "rank", "slug", "name", "common_name", "in_frame")


def write(conn):
    """Rifa' e scrive i candidati di tutti gli oggetti in dubbio, dal piu' probabile; tutto o
    niente (`db.replace_table.replace_rows`)."""
    righe = []
    for (object_id,) in conn.execute(
        "SELECT id FROM objects WHERE identity_confidence = ?", (DOUBT,)
    ).fetchall():
        cielo = obj.a_frame_of(conn, object_id)
        for rank, c in enumerate(identify.candidates(conn, cielo) if cielo else []):
            righe.append(
                (object_id, rank, *(c[k] for k in ("slug", "name", "common_name")),
                 c["in_frame"])
            )  # fmt: skip
    replace_rows(conn, "object_candidates", _COLONNE, righe)
