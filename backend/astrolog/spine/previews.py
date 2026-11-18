"""The user's photo of an Archive production (`docs/domini/archivio.md`): shrunk to
`anteprime/<sha256>.jpg` beside the DB; its slot in `production_previews` by names, not ids."""

import base64
import hashlib
import io
import re
import sqlite3
import struct
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np
from PIL import Image

from ..clock import now_iso
from ..vocab.instruments import InstrumentKind

FOLDER: Final = "anteprime"
# [P docs/domini/archivio.md] the limit the error text names
MAX_BYTES: Final = 40 * 1024 * 1024
# [T] checked on the header before decoding: past it a PNG alone takes gigabytes on a NAS
MAX_PIXELS: Final = 60_000_000
# [T] three times the slot's 400 px at 1440: sharp on a 2x screen, a few hundred kB
LONG_SIDE: Final = 1200
QUALITY: Final = 85  # [T] Pillow's own advice: above 95 the file grows, nothing shows
_FORMATS: Final = ("JPEG", "PNG", "WEBP")
# [C CIPA DC-008 Exif 2.32, tag 0x0112 Orientation] -> the transpose that stands it up,
# the same table as PIL.ImageOps.exif_transpose
_ORIENTATION: Final = {
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_270,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_90,
}
_EXIF_ORIENTATION: Final = 0x0112  # [C CIPA DC-008 Exif 2.32: Orientation]
# What Pillow raises on a broken file is not only UnidentifiedImageError
_BROKEN = (OSError, ValueError, SyntaxError, struct.error)
# Pillow's own guard (~89 Mpx) trips in Image.open, before MAX_PIXELS: same reason
_BOMB = (Image.DecompressionBombWarning, Image.DecompressionBombError)


class PreviewError(ValueError):
    """The photo is refused; `code` is the route's error code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Slot:
    """A production's place for its photo: a mosaic has one, optics and camera `None`."""

    owner_kind: str
    owner_key: str
    optics: str | None
    camera: str | None


def folder_of(db_path: str | Path) -> Path:
    return Path(db_path).with_name(FOLDER)


def shrink(raw: bytes) -> bytes:
    """A JPEG of at most `LONG_SIDE` px, upright, in its colour profile and without its EXIF (no
    GPS leaves in an export). Only the bytes decide the format, never the declared type."""
    if len(raw) > MAX_BYTES:
        raise PreviewError("too_large")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            return _shrunk(raw)
    except PreviewError:
        raise
    except _BOMB as e:
        raise PreviewError("too_many_pixels") from e
    except _BROKEN as e:
        raise PreviewError("not_an_image") from e


def _shrunk(raw: bytes) -> bytes:
    Image.open(io.BytesIO(raw), formats=_FORMATS).verify()  # verify leaves the image unusable
    im = Image.open(io.BytesIO(raw), formats=_FORMATS)
    if im.width * im.height > MAX_PIXELS:
        raise PreviewError("too_many_pixels")
    turn = _ORIENTATION.get(im.getexif().get(_EXIF_ORIENTATION, 1))
    icc = im.info.get("icc_profile")
    im.draft("RGB", (LONG_SIDE, LONG_SIDE))  # a JPEG decodes already reduced; others ignore it
    im = _eight_bits(im)
    im.thumbnail((LONG_SIDE, LONG_SIDE), Image.Resampling.LANCZOS)
    if turn is not None:
        im = im.transpose(turn)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=QUALITY, icc_profile=icc)
    return out.getvalue()


def _eight_bits(im: Image.Image) -> Image.Image:
    """A 16-bit grey PNG (a processing export) to 8 bits by scale: `convert` would clip it white."""
    if im.mode in ("I;16", "I;16B", "I;16L", "I"):
        grey = np.asarray(im, dtype=np.float64) / 257.0
        return Image.fromarray(np.clip(grey, 0, 255).astype(np.uint8), "L").convert("RGB")
    if im.mode == "F":
        grey = np.asarray(im, dtype=np.float64)
        top = float(grey.max()) or 1.0
        return Image.fromarray(np.clip(grey / top * 255, 0, 255).astype(np.uint8), "L").convert(
            "RGB"
        )
    return im.convert("RGB")


def digest_of(jpeg: bytes) -> str:
    return hashlib.sha256(jpeg).hexdigest()


def _keep(db_path: str | Path, jpeg: bytes) -> str:
    """Written once: the same photo twice is one file."""
    digest = digest_of(jpeg)
    target = folder_of(db_path) / f"{digest}.jpg"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(jpeg)
        tmp.replace(target)
    return digest


def _is_digest(value: object) -> bool:
    """An imported name only as `digest_of` writes it: no '../' reaches the folder's path."""
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None


def read(db_path: str | Path, digest: str) -> bytes | None:
    path = folder_of(db_path) / f"{digest}.jpg"
    return path.read_bytes() if path.exists() else None


_SLOT = "owner_kind = ? AND owner_key = ? AND optics IS ? AND camera IS ?"


def _key(s: Slot) -> tuple[str, str, str | None, str | None]:
    return s.owner_kind, s.owner_key, s.optics, s.camera


def put(conn: sqlite3.Connection, db_path: str | Path, slot: Slot, raw: bytes) -> str:
    """Shrinks, keeps the file, writes the slot; the photo it replaces goes if nothing uses it."""
    digest = _keep(db_path, shrink(raw))
    old = digest_in(conn, slot)
    conn.execute(f"DELETE FROM production_previews WHERE {_SLOT}", _key(slot))  # noqa: S608
    conn.execute(
        "INSERT INTO production_previews"
        " (owner_kind, owner_key, optics, camera, sha256, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (*_key(slot), digest, now_iso()),
    )
    if old and old != digest:
        _drop_if_unused(conn, db_path, old)
    return digest


def remove(conn: sqlite3.Connection, db_path: str | Path, slot: Slot) -> bool:
    old = digest_in(conn, slot)
    if old is None:
        return False
    conn.execute(f"DELETE FROM production_previews WHERE {_SLOT}", _key(slot))  # noqa: S608
    _drop_if_unused(conn, db_path, old)
    return True


def digest_in(conn: sqlite3.Connection, slot: Slot) -> str | None:
    row = conn.execute(
        f"SELECT sha256 FROM production_previews WHERE {_SLOT}",  # noqa: S608
        _key(slot),
    ).fetchone()
    return None if row is None else row[0]


def updated_at(conn: sqlite3.Connection, slot: Slot) -> str | None:
    row = conn.execute(
        f"SELECT updated_at FROM production_previews WHERE {_SLOT}",  # noqa: S608
        _key(slot),
    ).fetchone()
    return None if row is None else row[0]


def _drop_if_unused(conn: sqlite3.Connection, db_path: str | Path, digest: str) -> None:
    used = conn.execute("SELECT 1 FROM production_previews WHERE sha256 = ?", (digest,)).fetchone()
    if used is None:
        (folder_of(db_path) / f"{digest}.jpg").unlink(missing_ok=True)


def drop_unused(conn: sqlite3.Connection, db_path: str | Path, digests: Iterable[str]) -> None:
    for digest in set(digests):
        _drop_if_unused(conn, db_path, digest)


def in_use(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT sha256 FROM production_previews")}


def drop_unused_here(conn: sqlite3.Connection, digests: Iterable[str]) -> None:
    """As `drop_unused`, beside the connection's own file; an in-memory DB has no photos."""
    main = [r[2] for r in conn.execute("PRAGMA database_list") if r[1] == "main"]
    if main and main[0]:
        drop_unused(conn, main[0], digests)


def of(
    conn: sqlite3.Connection, keys: Iterable[str]
) -> dict[tuple[str, str, str | None, str | None], str]:
    """`{(kind, key, optics, camera): updated_at}` for the page's rows, as written."""
    wanted = list(dict.fromkeys(keys))
    if not wanted:
        return {}
    marks = ", ".join("?" * len(wanted))  # segnaposto-ok: one per key of the page
    sql = f"SELECT owner_kind, owner_key, optics, camera, updated_at FROM production_previews WHERE owner_key IN ({marks})"  # noqa: E501, S608 - placeholders only
    rows = conn.execute(sql, wanted)
    return {(r[0], r[1], r[2], r[3]): r[4] for r in rows}


def follow_instrument(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, *, merging: bool
) -> None:
    """As the declarations: on a rename what moves wins, on a merge the kept piece's photo."""
    column = {InstrumentKind.OPTICS: "optics", InstrumentKind.CAMERA: "camera"}.get(
        InstrumentKind(kind)
    )
    if column is None:
        return
    if not merging:
        conn.execute(
            f"DELETE FROM production_previews WHERE {column} = ? AND EXISTS ("  # noqa: S608
            f" SELECT 1 FROM production_previews o WHERE o.{column} = ?"
            " AND o.owner_kind = production_previews.owner_kind"
            " AND o.owner_key = production_previews.owner_key"
            f" AND o.{_other(column)} IS production_previews.{_other(column)})",
            (new_name, old_name),
        )
    conn.execute(
        f"UPDATE OR IGNORE production_previews SET {column} = ? WHERE {column} = ?",  # noqa: S608
        (new_name, old_name),
    )
    conn.execute(f"DELETE FROM production_previews WHERE {column} = ?", (old_name,))  # noqa: S608


def _other(column: str) -> str:
    return "camera" if column == "optics" else "optics"


def follow_object(conn: sqlite3.Connection, old_key: str, new_key: str) -> None:
    """A corrected object takes its photos along; where the target has one, the target's stays."""
    if old_key == new_key:
        return
    conn.execute(
        "UPDATE OR IGNORE production_previews SET owner_key = ?"
        " WHERE owner_kind = 'object' AND owner_key = ?",
        (new_key, old_key),
    )


_COLUMNS = ("owner_kind", "owner_key", "optics", "camera", "sha256", "updated_at")


def for_backup(conn: sqlite3.Connection, embed_from: Path | None) -> list[dict[str, Any]]:
    """The slots by their names; `embed_from` (an export) carries each photo too, in base64."""
    out = []
    rows = conn.execute(
        f"SELECT {', '.join(_COLUMNS)} FROM production_previews"  # noqa: S608 - constant columns
        " ORDER BY owner_kind, owner_key, optics, camera"
    )
    for r in rows:
        item: dict[str, Any] = dict(zip(_COLUMNS, r, strict=True))
        if embed_from is not None:
            path = embed_from / f"{r[4]}.jpg"
            if not path.exists():
                continue  # a photo lost on disk does not travel as a slot without a photo
            item["jpeg"] = base64.b64encode(path.read_bytes()).decode("ascii")
        out.append(item)
    return out


def restore(
    conn: sqlite3.Connection, db_path: str | Path, items: list[dict[str, Any]]
) -> list[str]:
    """Photo checked as an upload; slot without file here or in item skipped. Adds, replaces,
    never deletes; gives replaced photos, for `drop_unused` after the commit."""
    replaced: list[str] = []
    for item in items:
        slot = Slot(item["owner_kind"], item["owner_key"], item["optics"], item["camera"])
        if "jpeg" in item:
            raw = base64.b64decode(item["jpeg"], validate=True)
            digest = _keep(db_path, shrink(raw))
        elif _is_digest(item["sha256"]) and read(db_path, item["sha256"]) is not None:
            digest = item["sha256"]
        else:
            continue
        old = digest_in(conn, slot)
        if old is not None and old != digest:
            replaced.append(old)
        conn.execute(f"DELETE FROM production_previews WHERE {_SLOT}", _key(slot))  # noqa: S608
        conn.execute(
            "INSERT INTO production_previews (owner_kind, owner_key, optics, camera, sha256,"
            " updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (*_key(slot), digest, item["updated_at"]),
        )
    return replaced
