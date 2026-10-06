"""Three judgements on a frame's raw header, written at scan: they depend only on what the file says
and on vocab, so once written nobody rewrites them, and the review filters them in SQL."""

from collections.abc import Mapping
from typing import Any

from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from .night_rig import asks_camera
from .unfiltered import says_no_filter


def names_the_optics(software: str | None, telescope_raw: str | None) -> bool:
    """`TELESCOP` written, by a software that does not put the mount there: the same reading as
    `normalize_rig.rig_for_frame`."""
    return not telescope_is_mount(software) and bool(normalize_header_value(telescope_raw))


def of(fields: Mapping[str, Any]) -> dict[str, int]:
    software = normalize_software(fields.get("software_raw"))
    return {
        "asks_camera": int(asks_camera(fields.get("instrument_raw"))),
        "asks_filter": int(says_no_filter(fields.get("filter_raw"))),
        "names_optics": int(names_the_optics(software, fields.get("telescope_raw"))),
    }
