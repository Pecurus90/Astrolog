"""The half of `normalize` that turns raw header values into pieces and rigs."""

import sqlite3
from collections.abc import Mapping
from typing import Any

from ..units import known_focal, same_focal
from ..vocab.software import telescope_is_mount
from . import counts, declarations, gear, gear_create, rig_optics
from . import rigs as corredi

# a rig as the group's answer or the night gives it
GivenRig = Mapping[str, Any]


def instrument_named(
    conn: sqlite3.Connection, kind: str, name: str | None, counts: dict[str, int], now: str
) -> int | None:
    """Created if missing: a name the user wrote gives birth to a piece just as a header does."""
    if not name:
        return None
    instrument_id = gear.instrument_id(conn, kind, name)
    if instrument_id is None:
        instrument_id = gear_create.instrument(conn, kind, name, now, detected=True)
        counts["instruments"] += 1
    return instrument_id


def instrument_for(
    conn: sqlite3.Connection, kind: str, raw: str | None, counts: dict[str, int], now: str
) -> int | None:
    """The caller decides the kind: no list of mount names, which differ per user and would go
    stale; the software that wrote the file says whether a value is a mount."""
    return instrument_named(conn, kind, declarations.instrument_name(conn, kind, raw), counts, now)


def instruments_on_frame(
    conn: sqlite3.Connection, frame: sqlite3.Row, conti: dict[str, int], now: str
) -> dict[str, int | None]:
    """On the frame, not in the rig's fingerprint: files tie them to the single shot, and changing a
    wheel would otherwise give birth to a second rig."""
    return {
        kind: instrument_for(conn, kind, frame[f"{kind}_raw"], conti, now)
        for kind in counts.ON_THE_FRAME
    }


def mount_for_frame(  # noqa: PLR0913
    conn: sqlite3.Connection,
    frame: sqlite3.Row,
    rig_id: int | None,
    software: str | None,
    counts: dict[str, int],
    now: str,
) -> int | None:
    """The user's mount on the rig wins; the file's mount is created anyway, because the user's word
    chooses what goes on the frame, it does not delete a piece the files name."""
    dal_file = (
        instrument_for(conn, "mount", frame["telescope_raw"], counts, now)
        if telescope_is_mount(software)
        else None
    )
    detta = corredi.declared_mount(conn, rig_id) if rig_id is not None else None
    return detta if detta is not None else dal_file


def rig_for_frame(  # noqa: PLR0913
    conn: sqlite3.Connection,
    frame: sqlite3.Row,
    buckets: Mapping[float, float],
    counts: dict[str, int],
    now: str,
    camera: str | None,
    detto: GivenRig | None,
    software: str | None,
    notte: GivenRig | None = None,
) -> int | None:
    """Optics + camera at a focal. Where `TELESCOP` is the mount the file gives no optics: the
    declared optics, the night's rig (at its focal) or the camera+focal answer fill it."""
    if telescope_is_mount(software):
        optics_id = None  # it is the mount, written by `mount_for_frame`
    else:
        optics_id = instrument_for(conn, "optics", frame["telescope_raw"], counts, now)
    camera_id = instrument_named(conn, "camera", camera, counts, now)
    focal = known_focal(buckets.get(frame["focal_mm_raw"], frame["focal_mm_raw"]))
    if detto is not None:
        optics_id = instrument_named(conn, "optics", detto["optics"], counts, now) or optics_id
        # the declared focal fills a silent one, or the rig born here would twin the detected one
        focal = focal if focal is not None else detto["focal_mm"]
    if (
        notte is not None
        and optics_id is None
        and (focal is None or same_focal(notte["focal_mm"], focal))
    ):
        optics_id = instrument_named(conn, "optics", notte["optics"], counts, now)
        focal = notte["focal_mm"] if focal is None else focal
    detta = rig_optics.declared(conn, camera, focal) if optics_id is None and camera else None
    if detta is not None:
        optics_id = instrument_named(conn, "optics", detta[1], counts, now)
    if optics_id is None and camera_id is None:
        return None
    rig_id, created = corredi.rig_for(conn, optics_id, camera_id, focal, now)
    counts["rigs"] += 1 if created else 0
    # a rig born from an answer takes the name and mount given to the optics-less one; an existing
    # rig keeps its own word
    if detta is not None and created:
        corredi.carry_declarations(conn, detta[0], rig_id, now)
    return rig_id
