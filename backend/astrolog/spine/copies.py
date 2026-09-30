"""Chi e' la copia riscritta di chi, deciso una volta per corsa sulle nidiate delle pose in coda.

Vincolo non ovvio: una posa e' una copia **solo se un gemello e' piu' originale di lei**
(`spine/rewrite.py`), e a pari indizi si contano tutte e due (Marco, 10/9/2026): indovinare
fonderebbe due pose vere riprese nello stesso istante. La copia punta al capofila -- il piu'
originale, e fra pari il primo entrato -- cosi' `copy_of` porta all'originale in un passo. Le righe
le legge `normalize` (`normalize_store.broods`), che lo chiama prima del giro.
"""

from itertools import groupby

from . import rewrite


def _shot(row):
    return row["date_obs"], row["instrument_raw"], row["exposure_s"]


def decide(rows, frame_ids):
    """`(copia di, marchio, gemelli da rifare)` per le pose in coda `frame_ids` e le loro nidiate
    (`rows`, ordinate per scatto): `{posa: originale o None}`, `{posa: marchio}` e l'elenco dei
    gemelli gia' fatti che puntano altrove. Quelli vanno rifatti: il grezzo puo' arrivare dopo la
    sua copia, e senza la copia resterebbe contata come un'altra ora di cielo.

    Si tiene in mano una nidiata alla volta, e di lei solo cio' che si e' deciso: su una prima
    corsa la coda e' l'archivio intero."""
    in_queue = set(frame_ids)
    copy_of, marks, redo = dict.fromkeys(frame_ids), {}, []
    for _, brood in groupby(rows, key=_shot):
        seen = []
        for r in brood:
            marks[r["id"]] = mark = rewrite.mark_of(r)
            seen.append((r["id"], rewrite.originality(r, mark), r["copy_of"]))
        best = min(rank for _, rank, _ in seen)
        leader = min(i for i, rank, _ in seen if rank == best)
        for i, rank, was in seen:
            copy_of[i] = None if rank == best else leader
            if i not in in_queue and was != copy_of[i]:
                redo.append(i)
    return copy_of, marks, redo
