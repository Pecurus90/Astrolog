"""The rig's numbers from its pieces' cards (ADR 0021): each only with all its data, else it names
the first one it lacks. Pure: who writes them is `gear_numbers`, the page only reads."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..units import scale_arcsec_px

Card = Mapping[str, Any]
Number = dict[str, Any]

# Best sampling is 1/3 to 1/2 of the seeing: read backwards, seeing from 2x to 3x the scale.
# [C astronomy.tools/calculators/ccd_suitability: Nyquist, 0.67-2"/px with 2-4" seeing]
SEEING_PER_SCALE = (2.0, 3.0)
# [U Waddington, PHD2: "preferred range is roughly between 0.5 and 4 arc-sec/px", 2022]
GUIDE_SCALE_RANGE = (0.5, 4.0)
# [C Dawes limit, astronomy.tools/calculators/telescope_capabilities: 116 / aperture mm]
DAWES_ARCSEC_MM = 116.0
# Only the percentage, a warning above the payload: no maker publishes a margin. [P ADR 0021]
FULL_LOAD_PERCENT = 100.0


@dataclass(frozen=True, slots=True)
class RigCard:
    """A rig's pieces as cards: the chosen part, else the most used. `guide` is a guide scope or
    an OAG, its `kind` says which."""

    focal_mm: float | None
    optics: Card | None = None
    camera: Card | None = None
    reducer: Card | None = None
    guide: Card | None = None
    guide_camera: Card | None = None
    wheel: Card | None = None
    focuser: Card | None = None
    mount: Card | None = None
    spacers: Sequence[Card] = ()


class _MissingError(Exception):
    """The first datum a number lacks: kind of piece, and field (None: the piece itself)."""

    def __init__(self, kind: str, field: str | None = None) -> None:
        super().__init__(kind, field)
        self.missing = {"kind": kind, "field": field}


def _need(card: Card | None, kind: str, field: str | None = None) -> Any:
    if card is None:
        raise _MissingError(kind)
    if field is None:
        return card
    value = card.get(field)
    if value is None:
        raise _MissingError(card.get("kind", kind), field)
    return value


def _focal(rig: RigCard) -> float:
    if rig.focal_mm is None:
        raise _MissingError("rig", "focal_mm")
    return rig.focal_mm


def _sensor_mm(camera: Card | None, kind: str = "camera") -> tuple[float, float]:
    pixel = _need(camera, kind, "pixel_size_um")
    return (
        pixel * _need(camera, kind, "width_px") / 1000,
        pixel * _need(camera, kind, "height_px") / 1000,
    )


def _sampling(rig: RigCard) -> float:
    pixel = _need(rig.camera, "camera", "pixel_size_um")
    scale = scale_arcsec_px(pixel, _focal(rig))
    assert scale is not None  # both checked positive by the cards
    return scale


def _guide_scale(rig: RigCard) -> float:
    guide = _need(rig.guide, "guide")
    pixel = _need(rig.guide_camera, "guide_camera", "pixel_size_um")
    # the OAG has no focal of its own: it guides through the rig's [C openphdguiding Basic_use]
    focal = _focal(rig) if guide.get("kind") == "oag" else _need(guide, "guide_scope", "focal_mm")
    scale = scale_arcsec_px(pixel, focal)
    assert scale is not None  # both checked positive by the cards
    return scale


def _focal_ratio(rig: RigCard) -> Number:
    return {"value": _focal(rig) / _need(rig.optics, "optics", "aperture_mm")}


def _sampling_number(rig: RigCard) -> Number:
    scale = _sampling(rig)
    low, high = SEEING_PER_SCALE
    return {"value": scale, "seeing_from": low * scale, "seeing_to": high * scale}


def _field(rig: RigCard) -> Number:
    width, height = _sensor_mm(rig.camera)
    focal = _focal(rig)
    side = lambda mm: math.degrees(2 * math.atan(mm / (2 * focal)))  # noqa: E731
    return {"width": side(width), "height": side(height)}


def _sensor_size(camera: Card | None, kind: str = "camera") -> Number:
    width, height = _sensor_mm(camera, kind)
    return {"width": width, "height": height}


def _back_end(rig: RigCard) -> tuple[Card, str]:
    """The reducer when there is one, else the optics: its circle and backfocus are the train's."""
    optics = _need(rig.optics, "optics")
    reducer = rig.reducer
    return (reducer, "reducer") if reducer is not None else (optics, "optics")


def _coverage(rig: RigCard) -> Number:
    by, kind = _back_end(rig)
    circle = _need(by, kind, "image_circle_mm")
    diagonal = math.hypot(*_sensor_mm(rig.camera))
    return {"diagonal_mm": diagonal, "circle_mm": circle, "covers": circle >= diagonal}


def _guide_scale_number(rig: RigCard) -> Number:
    scale = _guide_scale(rig)
    low, high = GUIDE_SCALE_RANGE
    guide = _need(rig.guide, "guide")
    return {
        "value": scale,
        "in_range": low <= scale <= high,
        "range_from": low,
        "range_to": high,
        "guide": guide.get("kind"),
        "guide_name": guide.get("name"),
    }


def _guide_ratio(rig: RigCard) -> Number:
    imaging = _sampling(rig)  # the board names the sampling first (`conti`, 353)
    return {"value": _guide_scale(rig) / imaging}


def _train(rig: RigCard) -> list[tuple[Card | None, str]]:
    """What sits between the back of the reducer (or optics) and the sensor. The filter does not
    count: its focus shift is not verified (ADR 0021)."""
    train: list[tuple[Card | None, str]] = []
    if rig.guide is not None and rig.guide.get("kind") == "oag":
        train.append((rig.guide, "oag"))
    if rig.wheel is not None:
        train.append((rig.wheel, "filter_wheel"))
    train += [(spacer, "spacer") for spacer in rig.spacers]
    return [*train, (rig.camera, "camera")]


def _backfocus(rig: RigCard) -> Number:
    by, kind = _back_end(rig)
    required = _need(by, kind, "required_backfocus_mm")
    train = sum(_need(card, k, "thickness_mm") for card, k in _train(rig))
    difference = train - required
    tolerance = by.get("backfocus_tolerance_mm")
    return {
        "train_mm": train,
        "required_mm": required,
        "required_by": kind,
        "difference_mm": difference,
        "tolerance_mm": tolerance,
        "verdict": _backfocus_verdict(difference, tolerance),
    }


def _backfocus_verdict(difference: float, tolerance: float | None) -> str | None:
    """Only with the maker's tolerance: no single convention, it depends on the optics."""
    if tolerance is None:
        return None
    if round(difference, 2) == 0:
        return "exact"
    if abs(difference) <= tolerance:
        return "in_tolerance"
    return "short" if difference < 0 else "long"


def _carried(rig: RigCard) -> list[tuple[Card | None, str]]:
    pieces = [
        (rig.optics, "optics"), (rig.camera, "camera"), (rig.reducer, "reducer"),
        (rig.wheel, "filter_wheel"), (rig.focuser, "focuser"), (rig.guide, "guide"),
        (rig.guide_camera, "guide_camera"),
    ]  # fmt: skip
    pieces += [(spacer, "spacer") for spacer in rig.spacers]
    return [(card, kind) for card, kind in pieces if card is not None]


def _load(rig: RigCard) -> Number:
    mount = _need(rig.mount, "mount")
    payloads = [p for p in (mount.get("payload_kg"), mount.get("payload_no_cw_kg")) if p]
    if not payloads:
        raise _MissingError("mount", "payload_kg")
    weight = sum(_need(card, kind, "weight_kg") for card, kind in _carried(rig))
    payload = max(payloads)
    percent = weight / payload * 100
    return {
        "percent": percent,
        "within": percent <= FULL_LOAD_PERCENT,
        "weight_kg": weight,
        "payload_kg": payload,
    }


_EMPTY = {
    "focal_ratio": ("value",),
    "sampling": ("value", "seeing_from", "seeing_to"),
    "field": ("width", "height"),
    "sensor_size": ("width", "height"),
    "coverage": ("diagonal_mm", "circle_mm", "covers"),
    "guide_scale": ("value", "in_range", "range_from", "range_to", "guide", "guide_name"),
    "guide_ratio": ("value",),
    "backfocus": (
        "train_mm",
        "required_mm",
        "required_by",
        "difference_mm",
        "tolerance_mm",
        "verdict",
    ),  # fmt: skip
    "load": ("percent", "within", "weight_kg", "payload_kg"),
    "dawes": ("value",),
}


def _one(name: str, compute: Any, *args: Any) -> Number:
    try:
        return {**compute(*args), "missing": None}
    except _MissingError as missing:
        return {**dict.fromkeys(_EMPTY[name]), "missing": missing.missing}


def numbers(rig: RigCard) -> dict[str, Number]:
    """Every number of the rig, in the board's reading order."""
    return {
        "focal_ratio": _one("focal_ratio", _focal_ratio, rig),
        "sampling": _one("sampling", _sampling_number, rig),
        "field": _one("field", _field, rig),
        "sensor_size": _one("sensor_size", _sensor_size, rig.camera),
        "coverage": _one("coverage", _coverage, rig),
        "guide_scale": _one("guide_scale", _guide_scale_number, rig),
        "guide_ratio": _one("guide_ratio", _guide_ratio, rig),
        "backfocus": _one("backfocus", _backfocus, rig),
        "load": _one("load", _load, rig),
    }


def pieces(rig: RigCard) -> dict[str, Any]:
    """The pieces the numbers read, by id: the optical train draws the same ones."""
    of = lambda card: None if card is None else card["id"]  # noqa: E731
    return {
        "optics": of(rig.optics),
        "camera": of(rig.camera),
        "reducer": of(rig.reducer),
        "guide": of(rig.guide),
        "guide_camera": of(rig.guide_camera),
        "wheel": of(rig.wheel),
        "focuser": of(rig.focuser),
        "mount": of(rig.mount),
        "spacers": [card["id"] for card in rig.spacers],
    }


def _dawes(optics: Card) -> Number:
    return {"value": DAWES_ARCSEC_MM / _need(optics, "optics", "aperture_mm")}


def _native_ratio(optics: Card) -> Number:
    return {"value": _need(optics, "optics", "focal_mm") / _need(optics, "optics", "aperture_mm")}


def piece_numbers(card: Card) -> dict[str, Number]:
    """The numbers on a piece's own card: Dawes and the native focal ratio on an optics, the
    sensor on a camera."""
    kind = card.get("kind")
    if kind == "optics":
        return {
            "dawes": _one("dawes", _dawes, card),
            "focal_ratio": _one("focal_ratio", _native_ratio, card),
        }
    if kind in ("camera", "guide_camera"):
        return {"sensor_size": _one("sensor_size", _sensor_size, card, kind)}
    return {}
