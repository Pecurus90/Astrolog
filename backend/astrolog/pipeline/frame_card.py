"""The card that stands for a shot with copies: the present file seen first, a .fz only without
a plain one (docs/domini/misure.md). Written by the scan; readers join card_file_id."""

import sqlite3
from collections.abc import Iterable

# Present file with a card, first seen; .fz after any plain: fpack keeps the header, fewer
# readers open it.
_FIRST = (
    "SELECT f.id, lower(f.rel_path) LIKE '%.fz' AS fz FROM pipeline_files AS f"
    " JOIN pipeline_cards AS c ON c.file_id = f.id"
    " WHERE f.frame_id = ? AND f.state = 'present'"
    " ORDER BY fz, f.arrived_scan_id, f.id LIMIT 1"
)
# The card held, `kept` NULL when its file no longer stands: gone, left the shot, lost its card.
_HELD = (
    "SELECT fr.card_file_id, f.id AS kept, lower(f.rel_path) LIKE '%.fz' AS fz"
    " FROM pipeline_frames AS fr LEFT JOIN pipeline_files AS f ON f.id = fr.card_file_id"
    " AND f.frame_id = fr.id AND f.state = 'present'"
    " AND EXISTS (SELECT 1 FROM pipeline_cards AS c WHERE c.file_id = f.id)"
    " WHERE fr.id = ?"
)
# Shots whose card no longer stands, any root: a file gone or moved out leaves its shot here.
_STALE = (
    "SELECT fr.id FROM pipeline_frames AS fr"
    " LEFT JOIN pipeline_files AS f ON f.id = fr.card_file_id"
    " WHERE f.id IS NULL OR f.frame_id IS NOT fr.id OR f.state <> 'present'"
    " OR NOT EXISTS (SELECT 1 FROM pipeline_cards AS c WHERE c.file_id = f.id)"
    " OR (lower(f.rel_path) LIKE '%.fz' AND EXISTS (SELECT 1 FROM pipeline_files AS p"
    "   JOIN pipeline_cards AS c ON c.file_id = p.id WHERE p.frame_id = fr.id"
    "   AND p.state = 'present' AND lower(p.rel_path) NOT LIKE '%.fz'))"
)
# A moved file is the same file: what was read from it stays, under its new row.
_READ_FROM = ("pipeline_frames SET card_file_id", "pipeline_measures SET file_id",
              "pipeline_solutions SET file_id", "pipeline_sqm SET file_id")  # fmt: skip


def settle(conn: sqlite3.Connection, frames: Iterable[int]) -> None:
    """Caller's transaction. A held card stays; a new one sends the shot to be measured again:
    measure, sky and SQM used the old card's facts (pipeline_sky, pipeline_sqm cascade)."""
    for frame in sorted(set(frames)):
        held = conn.execute(_HELD, (frame,)).fetchone()
        if held is None:  # shot dropped with its last file
            continue
        first = conn.execute(_FIRST, (frame,)).fetchone()
        if held["kept"] is not None and not (held["fz"] and first is not None and not first["fz"]):
            continue
        card = None if first is None else int(first["id"])
        if card == held["card_file_id"]:
            continue
        conn.execute("UPDATE pipeline_frames SET card_file_id = ? WHERE id = ?", (card, frame))
        if card is not None:
            conn.execute(
                "DELETE FROM pipeline_measures WHERE frame_id = ? AND file_id IS NOT ?",
                (frame, card),
            )


def settle_stale(conn: sqlite3.Connection) -> None:
    settle(conn, [row["id"] for row in conn.execute(_STALE)])


def follow_moves(
    conn: sqlite3.Connection, root_id: int, scan_id: int, pairs: list[tuple[str, str]]
) -> None:
    """Before settle_stale: a moved original keeps its card and what was read from it."""
    for was, now in pairs:
        ids = conn.execute(
            "SELECT (SELECT id FROM pipeline_files WHERE root_id = :root AND rel_path = :was"
            "   AND state = 'gone' AND gone_scan_id = :scan) AS was,"
            " (SELECT id FROM pipeline_files WHERE root_id = :root AND rel_path = :now"
            "   AND state = 'present') AS now",
            {"root": root_id, "was": was, "now": now, "scan": scan_id},
        ).fetchone()
        if ids["was"] is None or ids["now"] is None:
            continue
        for target in _READ_FROM:
            column = target.rsplit(" ", 1)[1]
            conn.execute(
                f"UPDATE {target} = ? WHERE {column} = ?",
                (ids["now"], ids["was"]),
            )
