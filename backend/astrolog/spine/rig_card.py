"""A rig's card in the Gear index (board v82): its short title and its ten slots, from what the
rig already holds. Pure: the read hands it the rows, nothing is stored."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class Slot(StrEnum):
    """The ten parts of a rig, in the card's order (board v82 `PARTI`)."""

    OPTICS = "optics"
    CAMERA = "camera"
    REDUCER = "reducer"
    FILTER_WHEEL = "filter_wheel"
    SPACER = "spacer"
    MOUNT = "mount"
    FOCUSER = "focuser"
    GUIDE = "guide"
    GUIDE_CAMERA = "guide_camera"
    SOFTWARE = "software"


# A rig guides with a scope or an OAG (ADR 0021): either fills the one slot.
_SLOT_OF_PART = {
    "reducer": Slot.REDUCER,
    "filter_wheel": Slot.FILTER_WHEEL,
    "spacer": Slot.SPACER,
    "mount": Slot.MOUNT,
    "focuser": Slot.FOCUSER,
    "guide_scope": Slot.GUIDE,
    "oag": Slot.GUIDE,
    "guide_camera": Slot.GUIDE_CAMERA,
    "software": Slot.SOFTWARE,
}


@dataclass(frozen=True)
class Piece:
    """An optics or camera as the title reads it."""

    name: str
    brand: str | None
    model: str | None


def slots(optics: str | None, camera: str | None, part_kinds: Iterable[str]) -> dict[Slot, bool]:
    """Which slots hold something, in card order. Filters are not a slot: they sit in the ring."""
    held = {_SLOT_OF_PART[k] for k in part_kinds if k in _SLOT_OF_PART}
    if optics:
        held.add(Slot.OPTICS)
    if camera:
        held.add(Slot.CAMERA)
    return {s: s in held for s in Slot}


def short(piece: Piece) -> str:
    """The model if written, else the name without its brand, else the whole name. No list of
    brands: only the one written on the piece."""
    if piece.model:
        return piece.model
    brand = piece.brand
    if brand and piece.name.lower().startswith(brand.lower() + " "):
        return piece.name[len(brand) + 1 :].strip() or piece.name
    return piece.name


def title(name: str | None, optics: Piece | None, camera: Piece | None) -> str | None:
    """The rig's name, else its two pieces short, "?" for the missing one (board `corto`).
    None only without either piece."""
    if name:
        return name
    if not (optics or camera):
        return None
    return " · ".join(short(p) if p else "?" for p in (optics, camera))  # glifo-ok: board sep
