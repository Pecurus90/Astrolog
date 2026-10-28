# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of
# the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""ASTAP's .1476 star catalogues read as ASTAP reads them (ADR 0022 point 8): ported from ASTAP
unit_star_database.pas, (c) Han Kleijn, MPL-2.0. Degrees in and out."""

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Gaia BP catalogues in ASTAP's own order (select_star_database). v50 is Johnson V: another band.
CODES = ("d80", "d50", "d20", "d05")  # [C ASTAP unit_star_database.pas select_star_database]
# Cells per ring from the South pole [C ASTAP unit_star_database.pas area_and_boundaries1476]
RING_CELLS = (1, 3, 9, 15, 21, 27, 33, 38, 43, 48, 52, 56, 60, 63, 65, 67, 68, 69,
              69, 68, 67, 65, 63, 60, 56, 52, 48, 43, 38, 33, 27, 21, 15, 9, 3, 1)  # fmt: skip
RING_DEG = 90 / 17.5  # [C ASTAP unit_star_database.pas dec_boundaries1476]
# Ring edges, polar caps half a ring [C ASTAP unit_star_database.pas dec_boundaries1476]
DEC_EDGES = (-90.0, *(-90 + RING_DEG / 2 + RING_DEG * k for k in range(35)), 90.0)
HEADER_BYTES = 110  # [C ASTAP astap.htm Appendix 3: 110 byte header, record size in the last]
RA_STEP = 360.0 / (2**24 - 1)  # [C ASTAP readdatabase1476: 3 byte RA]
DEC_STEP = 90.0 / (128 * 2**16 - 1)  # [C ASTAP readdatabase1476: 3 byte two's complement Dec]
MAGNITUDE_RECORD = 0xFFFFFF  # [C ASTAP readdatabase1476: RA all ones marks a header record]
# Wider fields are cropped: an area beyond the next one would be missed.
MAX_FIELD_DEG = 5.142857  # [C ASTAP find_areas]
MIN_SHARE = 0.01  # [C ASTAP find_areas: too small, ignore]


@dataclass(frozen=True)
class Stars:
    ra_deg: np.ndarray
    dec_deg: np.ndarray
    mag: np.ndarray  # the catalogue's band, Gaia BP for the d catalogues


@dataclass(frozen=True)
class Area:
    number: int  # 1 at the South pole, 1476 at the North
    name: str  # in the file name, d80_0101.1476
    space: tuple[float, float, float, float]  # degrees to the E, W, N, S edges


def catalogue_in(folder: Path) -> str | None:
    """The first Gaia BP catalogue there, as ASTAP looks for it; none: None."""
    for code in CODES:
        if (folder / f"{code}_0101.1476").is_file():
            return code
    return None


def decode(buf: bytes) -> Stars:
    """One area file, bright to faint as stored. Records of 5 or 6 bytes; colour, 6th, unread."""
    size = 11 if buf[109:110] == b" " else buf[109]
    if size not in (5, 6):
        raise ValueError(f"record size {size} not read")
    rec = np.frombuffer(buf, np.uint8, offset=HEADER_BYTES).reshape(-1, size).astype(np.int64)
    ra_raw = rec[:, 0] | rec[:, 1] << 8 | rec[:, 2] << 16
    header = ra_raw == MAGNITUDE_RECORD
    if not len(rec):
        return Stars(np.zeros(0), np.zeros(0), np.zeros(0))
    if not header[0]:
        raise ValueError("no header record first")
    owner = np.flatnonzero(header)[np.cumsum(header) - 1]
    high = rec[owner, 3] - 128
    star = ~header
    dec_raw = (high << 16) + (rec[:, 4] << 8) + rec[:, 3]
    return Stars(
        ra_raw[star] * RA_STEP, dec_raw[star] * DEC_STEP, (rec[owner, 4][star] - 16) / 10.0
    )


def read_area(folder: Path, code: str, area: Area) -> Stars:
    return decode((folder / f"{code}_{area.name}.1476").read_bytes())


def area_of(ra_deg: float, dec_deg: float) -> Area:
    """area_and_boundaries1476: the area and how far its edges are."""
    ring = sum(dec_deg > edge for edge in DEC_EDGES[1:36])
    if ring in (0, 35):
        polar = DEC_EDGES[1] - DEC_EDGES[0]
        north, south = (polar, dec_deg - DEC_EDGES[35]) if ring else (DEC_EDGES[1] - dec_deg, polar)
        return Area(1 if ring == 0 else 1476, f"{ring + 1:02d}01", (360.0, 360.0, north, south))
    cells = RING_CELLS[ring]
    turn = (ra_deg % 360.0) * cells / 360.0
    cell = math.trunc(turn)
    part, width = turn - cell, 360.0 / cells * math.cos(math.radians(dec_deg))
    space = ((1 - part) * width, part * width, DEC_EDGES[ring + 1] - dec_deg,
             dec_deg - DEC_EDGES[ring])  # fmt: skip
    return Area(sum(RING_CELLS[:ring]) + cell + 1, f"{ring + 1:02d}{cell + 1:02d}", space)


def find_areas(ra_deg: float, dec_deg: float, field_deg: float) -> list[tuple[Area, float]]:
    """Up to four areas under the field's corners, each with its share of the field."""
    field = min(field_deg, MAX_FIELD_DEG)
    half = field / 2
    corners: list[tuple[Area, float]] = []
    for dec, ns in ((dec_deg + half, 3), (dec_deg - half, 2)):
        step = half / math.cos(math.radians(dec))
        for ra, ew in ((ra_deg + step, 1), (ra_deg - step, 0)):
            area = area_of(ra % 360.0, dec)
            share = min(area.space[ew], field) * min(area.space[ns], field) / field**2
            corners.append((area, share))
    # a repeated area drops before the small ones, as in ASTAP
    numbers = [a.number for a, _ in corners]
    return [
        (area, share)
        for i, (area, share) in enumerate(corners)
        if area.number not in numbers[:i] and share >= MIN_SHARE
    ]


def window(stars: Stars, ra_deg: float, dec_deg: float, field_deg: float) -> Stars:
    """readdatabase1476's square: |dRA| cos(Dec0) and |dDec| under half the field."""
    d_ra = np.abs(stars.ra_deg - ra_deg)
    d_ra = np.where(d_ra > 180.0, 360.0 - d_ra, d_ra)
    near = (d_ra * math.cos(math.radians(dec_deg)) < field_deg / 2) & (
        np.abs(stars.dec_deg - dec_deg) < field_deg / 2
    )
    return Stars(stars.ra_deg[near], stars.dec_deg[near], stars.mag[near])
