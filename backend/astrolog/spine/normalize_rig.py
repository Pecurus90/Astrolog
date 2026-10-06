"""The half of `normalize` that turns raw header values into pieces and rigs."""

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass

from ..units import known_focal, same_focal
from ..vocab.software import telescope_is_mount
from . import counts, declarations, gear_create, rigs
from .night_rig import NightRig
from .signature import Answer


@dataclass(frozen=True)
class Given:
    """What a frame is given where its header is silent, decided before the round writes: the
    camera, the signature's answer, the night's rig."""

    camera: str | None
    answer: Answer | None
    night: NightRig | None


@dataclass(frozen=True)
class Writing:
    """What every write of the round shares."""

    counts: dict[str, int]
    now: str
    buckets: Mapping[float, float]


def instrument_named(
    conn: sqlite3.Connection, kind: str, name: str | None, counts: dict[str, int], now: str
) -> int | None:
    """Created if missing: a name the user wrote gives birth to a piece just as a header does."""
    if not name:
        return None
    instrument_id = declarations.instrument_id(conn, kind, name)
    return instrument_id if instrument_id is not None else _created(conn, kind, name, counts, now)


def _created(
    conn: sqlite3.Connection, kind: str, name: str, counts: dict[str, int], now: str
) -> int:
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
    conn: sqlite3.Connection, frame: sqlite3.Row, tally: dict[str, int], now: str
) -> dict[str, int | None]:
    """On the frame, not in the rig's fingerprint: files tie them to the single shot, and changing a
    wheel would otherwise give birth to a second rig. Names and pieces read once for all kinds."""
    raws = {kind: frame[f"{kind}_raw"] for kind in counts.ON_THE_FRAME}
    named = {k: name for k, name in declarations.instrument_names(conn, raws).items() if name}
    found = declarations.instrument_ids(conn, named)
    carried: dict[str, int | None] = {}
    for kind in counts.ON_THE_FRAME:
        if kind not in named:
            carried[kind] = None
        elif kind in found:
            carried[kind] = found[kind]
        else:
            carried[kind] = _created(conn, kind, named[kind], tally, now)
    return carried


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
    from_file = (
        instrument_for(conn, "mount", frame["telescope_raw"], counts, now)
        if telescope_is_mount(software)
        else None
    )
    declared = rigs.declared_mount(conn, rig_id) if rig_id is not None else None
    return declared if declared is not None else from_file


def rig_for_frame(
    conn: sqlite3.Connection,
    frame: sqlite3.Row,
    writing: Writing,
    given: Given,
    software: str | None,
) -> int | None:
    """Optics + camera at a focal. Where `TELESCOP` is the mount the file gives no optics: the
    answer's optics, or the night's rig at its focal, fill it. The answer's optics wins."""
    counts, now, answer, night_rig = writing.counts, writing.now, given.answer, given.night
    if telescope_is_mount(software):
        optics_id = None  # it is the mount, written by `mount_for_frame`
    else:
        optics_id = instrument_for(conn, "optics", frame["telescope_raw"], counts, now)
    camera_id = instrument_named(conn, "camera", given.camera, counts, now)
    focal = known_focal(writing.buckets.get(frame["focal_mm"], frame["focal_mm"]))
    declared = answer is not None and answer.optics is not None
    if answer is not None:
        optics_id = instrument_named(conn, "optics", answer.optics, counts, now) or optics_id
        # the declared focal fills a silent one, or the rig born here would twin the detected one
        focal = focal if focal is not None else answer.focal_mm
    if (
        night_rig is not None
        and optics_id is None
        and (focal is None or same_focal(night_rig.focal_mm, focal))
    ):
        optics_id = instrument_named(conn, "optics", night_rig.optics, counts, now)
        focal = night_rig.focal_mm if focal is None else focal
    if optics_id is None and camera_id is None:
        return None
    rig_id, created = rigs.rig_for(conn, optics_id, camera_id, focal, now)
    counts["rigs"] += 1 if created else 0
    # a rig born from an answer takes the name and mount given to the optics-less one; an existing
    # rig keeps its own word
    optics_less = rigs.optics_less_key(conn, given.camera, focal) if declared and created else None
    if optics_less is not None:
        rigs.carry_declarations(conn, optics_less, rig_id, now)
    return rig_id
