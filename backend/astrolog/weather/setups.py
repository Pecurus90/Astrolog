"""Each setup against the night's seeing (domini/meteo.md): sampling with the mean (ADR 0021),
seeing against its floor F with the worst hour (ADR 0039). Rigs read from `gear_numbers`."""

import json
import math
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..levels import SamplingClass, Verdict

# Seeing as F: star FWHM^2 doubles, exposure x2 for stars. [P ADR 0039]
MARGINAL_PER_FLOOR = 1.0
# Seeing as sqrt(3) F: star FWHM doubles. [P ADR 0039]
NOGO_PER_FLOOR = math.sqrt(3)
# Arcsec as the page shows them, so "limite 0,7" and an hour at 0,7 agree. [T]
SHOWN_DIGITS = 1

_RIGS = "SELECT subject_id, numbers_json FROM gear_numbers WHERE subject = 'rig'"
_FRAMES = "SELECT rig_id, COUNT(*) FROM frames WHERE copy_of IS NULL GROUP BY rig_id"
_NIGHTS = "SELECT rowid, summary_json FROM weather_view"


@dataclass(frozen=True, slots=True)
class Rig:
    rig_id: int
    name: str | None
    optics: str | None
    camera: str | None
    frames: int
    scale_arcsec_px: float
    # the seeing the scale is ideal for, as `rig_numbers` writes it: one home (SEEING_PER_SCALE)
    seeing_from: float
    seeing_to: float
    floor_arcsec: float | None
    floor_missing: Mapping[str, Any] | None


def _sampling(seeing_from: float, seeing_to: float, seeing: float) -> SamplingClass:
    # ideal inside the written band, edges included (ADR 0021); all as shown, to a tenth
    seeing = round(seeing, SHOWN_DIGITS)
    if seeing < seeing_from:
        return SamplingClass.UNDER
    return SamplingClass.OVER if seeing > seeing_to else SamplingClass.IDEAL


def _level(floor: float | None, worst: float | None) -> Verdict | None:
    if floor is None or worst is None:
        return None
    if worst >= NOGO_PER_FLOOR * floor:
        return Verdict.NOGO
    return Verdict.MARGINAL if worst >= MARGINAL_PER_FLOOR * floor else Verdict.GO


def judged(seeing: Mapping[str, Any] | None, rigs: Sequence[Rig]) -> list[dict[str, Any]]:
    """Empty without a number of seeing: nothing to judge with, the page shows no card."""
    if seeing is None or seeing.get("value") is None or seeing.get("estimated_from"):
        return []
    mean, worst = seeing["value"], seeing.get("peak")
    rows = []
    for rig in sorted(rigs, key=lambda r: (-r.frames, r.rig_id)):
        floor = None if rig.floor_arcsec is None else round(rig.floor_arcsec, SHOWN_DIGITS)
        scale = rig.scale_arcsec_px
        seeing_from = round(rig.seeing_from, SHOWN_DIGITS)
        seeing_to = round(rig.seeing_to, SHOWN_DIGITS)
        rows.append(
            {
                "rig_id": rig.rig_id,
                "name": rig.name,
                "optics": rig.optics,
                "camera": rig.camera,
                "scale_arcsec_px": scale,
                "seeing_from": seeing_from,
                "seeing_to": seeing_to,
                "sampling": _sampling(seeing_from, seeing_to, mean),
                "floor_arcsec": floor,
                "floor_missing": None if floor is not None else rig.floor_missing,
                "seeing_level": _level(floor, worst),
            }
        )
    return rows


def rigs(conn: sqlite3.Connection) -> list[Rig]:
    """The rigs with a scale; the floor may lack its aperture and says so."""
    frames = dict(conn.execute(_FRAMES).fetchall())
    out = []
    for rig_id, numbers_json in conn.execute(_RIGS).fetchall():
        numbers = json.loads(numbers_json)
        sampling = numbers.get("sampling", {})
        scale = sampling.get("value")
        if scale is None:
            continue
        floor = numbers.get("seeing_floor", {})
        label = numbers.get("label") or {}
        out.append(
            Rig(
                rig_id=rig_id,
                name=label.get("name"),
                optics=label.get("optics"),
                camera=label.get("camera"),
                frames=frames.get(rig_id, 0),
                scale_arcsec_px=scale,
                seeing_from=sampling["seeing_from"],
                seeing_to=sampling["seeing_to"],
                floor_arcsec=floor.get("value"),
                floor_missing=floor.get("missing"),
            )
        )
    return out


def seeing_of(measures: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    return next((m for m in measures if m["code"] == "seeing"), None)


def step(conn: sqlite3.Connection) -> bool:
    """Every written night follows the setups as they are now: a card, a part or a name changed
    reaches the Weather at the next round. True if something was written."""
    now = rigs(conn)
    changed = False
    for rowid, summary_json in conn.execute(_NIGHTS).fetchall():
        summary = json.loads(summary_json)
        fresh = judged(seeing_of(summary.get("measures", [])), now)
        if summary.get("setups") != fresh:
            summary["setups"] = fresh
            conn.execute(
                "UPDATE weather_view SET summary_json = ? WHERE rowid = ?",
                (json.dumps(summary), rowid),
            )
            changed = True
    return changed
