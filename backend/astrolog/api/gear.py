"""The rows come from `spine/inventory.py` with the counts the Archive and Nights already use; what
is unknown arrives `null`, not zero, so the page can say why it is missing."""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends

from ..spine import gear, inventory, rig_card
from ..units import MOON_DIAMETER_DEG
from . import instrument_answer
from .deps import get_db
from .models_gear import GearList

router = APIRouter(prefix="/api/v1", tags=["gear"])


@router.get("/gear", response_model=GearList)
def gear_list(conn: sqlite3.Connection = Depends(get_db)) -> GearList:
    """The pieces you own, by kind, with the rigs and the filters.

    No pagination, and not by oversight: anyone's gear fits in one screen -- whoever has a hundred
    thousand frames still has a handful of telescopes -- and paging it would mean one more round to
    see what fits in one."""
    pieces = inventory.instruments(conn)
    for p in pieces:
        # only the merges the spine accepts: the same rule as the answer
        p["mergeable_into"] = [o["id"] for o in pieces if gear.mergeable(p, o)]
    filters = inventory.filters(conn)
    for f in filters:
        f["mergeable_into"] = [o["id"] for o in filters if gear.filter_mergeable(f, o)]
    rigs = inventory.rigs(conn)
    for r in rigs:
        _card(r)
    return GearList.model_validate(
        {
            "instruments": pieces,
            "rigs": rigs,
            "filters": filters,
            # The api, not the spine, knows which fields a kind's card asks for: the same table
            # with which the answer rejects a field that kind does not have.
            "cards": instrument_answer.CARD,
            "moon_deg": MOON_DIAMETER_DEG,
        }
    )


def _card(rig: dict[str, Any]) -> None:
    """The index card of a rig: title and slots, from the row it already has."""

    def piece(role: str) -> rig_card.Piece | None:
        name = rig[role]
        return name and rig_card.Piece(name, rig[f"{role}_brand"], rig[f"{role}_model"])

    rig["title"] = rig_card.title(rig["name"], piece("optics"), piece("camera"))
    held = rig_card.slots(rig["optics"], rig["camera"], (p["kind"] for p in rig["parts"]))
    rig["slots"] = [{"kind": k, "filled": v} for k, v in held.items()]
    rig["slots_missing"] = sum(not v for v in held.values())
