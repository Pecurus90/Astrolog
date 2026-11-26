"""The archive's row of a frame, written by the scan from the frame's card (step 40.4): the pages
and the old stages read `frames`, the scan is the only writer. SQL only: no spine import."""

import json
import re
import sqlite3
from collections.abc import Iterable
from typing import Any

from ..clock import night_date, night_instant
from ..place import timezone_of_frame

# frame types the archive holds: calibration frames stay in the pipeline (SQM bias, darks)
ARCHIVED = {"light": "light", "unknown": "unknown"}
# SBIG names; ACQUISITION before WRITER (fits/header_keys.py, until it goes)
_SOFTWARE_KEYS = ("SWCREATE", "CREATOR")
_BAYER = re.compile(r"^(RGGB|GRBG|BGGR|GBRG|CMYG|CYGM)$", re.IGNORECASE | re.ASCII)

_CARD = (
    "SELECT fr.id, fr.fingerprint, fr.created_at, c.*, h.program, h.header, f.mtime_ns,"
    " f.rel_path, r.path AS root FROM pipeline_frames AS fr"
    " JOIN pipeline_cards AS c ON c.file_id = fr.card_file_id"
    " JOIN pipeline_headers AS h ON h.file_id = fr.card_file_id"
    " JOIN pipeline_files AS f ON f.id = fr.card_file_id"
    " JOIN pipeline_roots AS r ON r.id = f.root_id"
    " WHERE fr.id = ?"
)
# the user's answer on the folder holding the file (spine/typeless.answer_at, same key)
_FOLDER_SAYS = (
    "SELECT value FROM declarations WHERE entity_type = 'folder' AND field = 'image_type'"
    " AND entity_key = ?"
)
# shots of a root the archive could hold and does not: kept out by a folder answer since changed
LEFT_OUT = (
    "SELECT DISTINCT fr.id FROM pipeline_frames AS fr"
    " JOIN pipeline_files AS f ON f.id = fr.card_file_id"
    " JOIN pipeline_cards AS c ON c.file_id = f.id"
    " WHERE f.root_id = ? AND f.state = 'present' AND c.frame_type IN ('light', 'unknown')"
    " AND NOT EXISTS (SELECT 1 FROM frames WHERE frames.id = fr.id)"
)
# columns the card decides; a change sends the frame back through every stage
COLUMNS = (
    "frame_hash", "image_type", "date_obs", "exposure_s", "gain", "offset", "ccd_temp_c",
    "naxis1", "naxis2", "binning", "pixel_size_um", "bayer_pattern", "focal_mm_raw",
    "filter_raw", "object_raw", "telescope_raw", "instrument_raw", "filter_wheel_raw",
    "focuser_raw", "guide_camera_raw", "software_raw", "ra_hint_deg", "dec_hint_deg",
    "site_lat", "site_lon", "header_json",
)  # fmt: skip
_NIGHT = ("local_night", "local_tz", "night_instant")
# want the vocabulary: NULL until normalize judges them (spine/header_asks.fill)
_JUDGED = ("asks_camera", "asks_filter", "names_optics")
# a frame is born with every stage of the old chain pending: spine/stages.STAGES (test: same)
STAGES = ("solve", "normalize", "identify", "group", "measure")


def write(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> set[int]:
    """Caller's transaction. Frame without a standing card (every file gone): row kept, its hours
    too. Returns the frames born now."""
    home = conn.execute("SELECT timezone FROM sites WHERE is_default = 1").fetchone()
    home_tz = None if home is None else home["timezone"]
    born: set[int] = set()
    for frame_id in sorted(set(frame_ids)):
        card = conn.execute(_CARD, (frame_id,)).fetchone()
        if card is None:
            continue
        if card["frame_type"] not in ARCHIVED:
            conn.execute("DELETE FROM frames WHERE id = ?", (frame_id,))
            continue
        if _upsert(conn, card, home_tz):
            born.add(frame_id)
    return born


def left_out(conn: sqlite3.Connection, root_id: int) -> set[int]:
    """Shots of the root without their row: a folder answer kept them out and may have changed
    since (the file is not read again, so the scan asks here)."""
    return {row["id"] for row in conn.execute(LEFT_OUT, (root_id,))}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def values_of(card: sqlite3.Row) -> dict[str, Any]:
    """The old scan's raw columns, from the card and, where it kept the raw text, the header."""
    header: dict[str, Any] = json.loads(card["header"])
    bayer = _text(header.get("BAYERPAT"))
    software = next((t for k in _SOFTWARE_KEYS if (t := _text(header.get(k)))), None)
    start = card["start_utc"]
    return {
        "frame_hash": card["fingerprint"],
        "image_type": ARCHIVED[card["frame_type"]],
        "date_obs": None if start is None else start[:23],  # UTC with milliseconds
        "exposure_s": card["exposure_s"],
        "gain": card["gain"],
        "offset": card["offset"],
        "ccd_temp_c": card["ccd_temp_c"] if card["ccd_temp_c"] is not None else card["set_temp_c"],
        "naxis1": card["width"],
        "naxis2": card["height"],
        "binning": card["bin_x"],
        "pixel_size_um": card["pixel_um"],
        "bayer_pattern": bayer.upper() if bayer and _BAYER.match(bayer) else None,
        "focal_mm_raw": card["focal_mm"],
        "filter_raw": card["filter"],
        "object_raw": _text(header.get("OBJECT")),  # raw: N.I.N.A.'s placeholder is the stage's
        "telescope_raw": _text(header.get("TELESCOP")),  # ASIAIR's mount too: normalize knows
        "instrument_raw": card["camera"],
        "filter_wheel_raw": card["filter_wheel"],
        "focuser_raw": card["focuser"],
        "guide_camera_raw": card["guide_camera"],
        "software_raw": software,
        "ra_hint_deg": card["pointing_ra_deg"],
        "dec_hint_deg": card["pointing_dec_deg"],
        "site_lat": card["site_lat_deg"],
        "site_lon": card["site_lon_deg"],
        "header_json": json.dumps(list(header.items()), ensure_ascii=False),
    }


def folder_key(root: str, rel_path: str) -> str:
    """spine/frame_folder.key_of_path: forward slashes, the folder holding the file."""
    inside = rel_path.rsplit("/", 1)[0] if "/" in rel_path else ""
    base = root.replace("\\", "/").rstrip("/")
    return f"{base}/{inside.strip('/')}" if inside.strip("/") else base


def _kept_out(conn: sqlite3.Connection, card: sqlite3.Row) -> bool:
    """A file that does not say its type, in a folder the user called calibration: it does not
    enter (docs/domini/spina-scan.md); a frame already in the archive stays and waits."""
    if card["frame_type"] != "unknown":
        return False
    said = conn.execute(_FOLDER_SAYS, (folder_key(card["root"], card["rel_path"]),)).fetchone()
    return said is not None and said["value"] == "calibration"


def _upsert(conn: sqlite3.Connection, card: sqlite3.Row, home_tz: str | None) -> bool:
    """True when born. A card that changed what the frame says sends it back to every stage."""
    values = values_of(card)
    held = conn.execute(
        f"SELECT {', '.join(_quoted(c) for c in (*COLUMNS, 'night_instant'))}"  # noqa: S608
        " FROM frames WHERE id = ?",
        (card["id"],),
    ).fetchone()
    if held is None and _kept_out(conn, card):
        return False
    instant = night_instant(values["date_obs"], card["mtime_ns"] / 1e9)
    if held is not None and values["date_obs"] is None:
        instant = held["night_instant"]  # the file's date moves every time it is touched
    zone = timezone_of_frame(values["site_lat"], values["site_lon"], home_tz)
    night = {"local_night": night_date(instant, zone), "local_tz": zone, "night_instant": instant}
    if held is None:
        names = (*COLUMNS, *_NIGHT, "created_at", *_JUDGED)
        conn.execute(
            f"INSERT INTO frames (id, {', '.join(_quoted(c) for c in names)})"  # noqa: S608
            f" VALUES (?{', ?' * len(names)})",
            (card["id"], *(values[c] for c in COLUMNS), *night.values(), card["created_at"],
             *(None for _ in _JUDGED)),
        )  # fmt: skip
        conn.executemany(
            "INSERT OR IGNORE INTO frame_stages (frame_id, stage, status, updated_at)"
            " VALUES (?, ?, 'pending', ?)",
            [(card["id"], stage, card["created_at"]) for stage in STAGES],
        )
        return True
    if all(held[c] == values[c] for c in COLUMNS):
        return False
    sets = ", ".join(f"{_quoted(c)} = ?" for c in (*COLUMNS, *_NIGHT, *_JUDGED))
    conn.execute(
        f"UPDATE frames SET {sets} WHERE id = ?",  # noqa: S608
        (*(values[c] for c in COLUMNS), *night.values(), *(None for _ in _JUDGED), card["id"]),
    )
    conn.execute(
        "UPDATE frame_stages SET status = 'pending', reason = NULL WHERE frame_id = ?",
        (card["id"],),
    )
    return False


def _quoted(column: str) -> str:
    return f'"{column}"'  # `offset` is a keyword
