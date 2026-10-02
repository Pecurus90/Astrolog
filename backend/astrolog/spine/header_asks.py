"""Three judgements on a frame's raw header, written at scan: they depend only on what the file says
and on vocab, so once written nobody rewrites them, and the review filters them in SQL."""

from collections.abc import Mapping
from typing import Any

from ..vocab.software import normalize_software
from .night_rig import asks_camera
from .rig_optics import names_the_optics
from .unfiltered import says_no_filter


def of(fields: Mapping[str, Any]) -> dict[str, int]:
    software = normalize_software(fields.get("software_raw"))
    return {
        "asks_camera": int(asks_camera(fields.get("instrument_raw"))),
        "asks_filter": int(says_no_filter(fields.get("filter_raw"))),
        "names_optics": int(names_the_optics(software, fields.get("telescope_raw"))),
    }
