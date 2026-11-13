"""The numbers of a rig and of a piece, from the cards (ADR 0021). Each comes whole or with
`missing`, the first datum it lacks: then its values are null and the page says what to write."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_review import CardField

# Who lacks it: a kind of piece, the rig (its effective focal), or the guide (scope or OAG).
MissingKind = Literal[
    "optics", "camera", "mount", "reducer", "filter_wheel", "guide_scope", "guide_camera",
    "focuser", "oag", "spacer", "rig", "guide",
]  # fmt: skip


class Missing(BaseModel):
    kind: MissingKind
    field: CardField | None = Field(description="Null: the piece itself is missing from the rig.")


class Number(BaseModel):
    value: float | None
    missing: Missing | None


class Sampling(BaseModel):
    """The scale in "/px, and the seeing it is best for: from 2x to 3x the scale."""

    value: float | None
    seeing_from: float | None
    seeing_to: float | None
    missing: Missing | None


class Sides(BaseModel):
    """Width and height: degrees for the field, millimetres for the sensor."""

    width: float | None
    height: float | None
    missing: Missing | None


class Coverage(BaseModel):
    """The sensor's diagonal against the image circle of the reducer, else of the optics."""

    diagonal_mm: float | None
    circle_mm: float | None
    covers: bool | None
    missing: Missing | None


class GuideScale(BaseModel):
    value: float | None
    in_range: bool | None = Field(description="Within 0.5-4 \"/px, PHD2's preferred range.")
    range_from: float | None = Field(description="That range, for the page to say it.")
    range_to: float | None
    guide: Literal["guide_scope", "oag"] | None = Field(
        description="What it guides through: an OAG guides with the rig's focal."
    )
    guide_name: str | None
    missing: Missing | None


class Backfocus(BaseModel):
    """The train's thickness minus the required backfocus: negative is short."""

    train_mm: float | None = Field(description="OAG, wheel, spacers and camera, summed.")
    required_mm: float | None
    required_by: Literal["reducer", "optics"] | None
    difference_mm: float | None
    tolerance_mm: float | None
    verdict: Literal["exact", "in_tolerance", "short", "long"] | None = Field(
        description="Only with the maker's tolerance on the card: without it, the difference alone."
    )
    missing: Missing | None


class Load(BaseModel):
    percent: float | None = Field(description="Of the mount's highest payload.")
    within: bool | None
    weight_kg: float | None = Field(description="Every carried piece's weight, summed.")
    payload_kg: float | None = Field(description="The highest of the mount's two payloads.")
    missing: Missing | None


class RigNumbers(BaseModel):
    focal_ratio: Number
    sampling: Sampling
    field: Sides
    sensor_size: Sides
    coverage: Coverage
    guide_scale: GuideScale
    guide_ratio: Number = Field(description="Guide scale over imaging scale, with no verdict.")
    backfocus: Backfocus
    load: Load


class PieceNumbers(BaseModel):
    """Dawes's resolving power on an optics, the sensor's size on a camera; null on the others."""

    dawes: Number | None = None
    sensor_size: Sides | None = None
