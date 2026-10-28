"""AstroLog's sky brightness beside astap.exe -sqm on the same frames (plan 25.3, ADR 0022 point
8). Rerun when the method changes; the gaps and their reasons go in docs/domini/misure.md.

Use: python tools/confronto_sqm.py FOLDER [--astap EXE] [--bias ADU]
Point it at copies: astap.exe writes its .wcs and .ini beside each frame.

What astap.exe gives: SQM (two decimals) and MZEROR in the .wcs, the solution beside them. Only
mono: from the command line its colour branch never runs (unit_sqm.pas, inside `form_exist`) and
astap.exe -sqm hangs on a colour frame, so astap_cli solves it and we alone measure it; its SQM
only with --bias, as the sqm stage. astap_cli has no -sqm.
"""

import argparse
import statistics
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from astrolog.astap import Run
from astrolog.pipeline.airmass import airmass_of
from astrolog.pipeline.pixels import Pixels, read_pixels
from astrolog.pipeline.scanner import read_header
from astrolog.pipeline.sqm import Wcs, calibrate, sky_brightness
from astrolog.pipeline.star_catalogue import catalogue_in
from confronto_misure import FRAME_SUFFIXES, _launch, card_altitude

ASTAP_EXE = Path(r"C:\Program Files\astap\astap.exe")
ASTAP_CLI = ASTAP_EXE.parent / "astap_cli.exe"
ASTAP_TIMEOUT_S = 120.0
SEARCH_RADIUS_DEG = 30  # [T] around the header's pointing: a blind search wastes minutes


@dataclass(frozen=True)
class Ours:
    sqm: float | None
    zero_point_mag: float
    stars: int
    colour: bool


@dataclass(frozen=True)
class Theirs:
    sqm: float | None
    zero_point_mag: float | None
    wcs: Wcs


type Measure = Callable[[Path, Wcs | None, float, Path], Ours | None]


def read_cards(text: str) -> dict[str, float | str]:
    """80-character cards, numbers as numbers; ASTAP writes the .wcs without line breaks."""
    cards: dict[str, float | str] = {}
    lines = (
        text.splitlines() if "\n" in text else [text[i : i + 80] for i in range(0, len(text), 80)]
    )
    for line in lines:
        if len(line) > 9 and line[8] == "=":
            value = line[10:].split("/")[0].strip().strip("'").strip()
            try:
                cards[line[:8].strip()] = float(value)
            except ValueError:
                cards[line[:8].strip()] = value
    return cards


def is_colour(frame: Path) -> bool:
    """As the sqm stage: a Bayer pattern and no binning."""
    with open(frame, "rb") as fh:
        header = read_header(fh)
    if header is None:
        return False
    return bool(header.cards.get("BAYERPAT")) and header.cards.get("XBINNING") in (None, 1)


def run_astap(exe: str, frame: Path, bias: float | None, run: Run) -> Theirs | None:
    """With bias None only the solve: astap_cli takes no -sqm."""
    cmd = [exe, "-f", str(frame), "-r", str(SEARCH_RADIUS_DEG)]
    run(cmd if bias is None else [*cmd, "-sqm", f"{bias:g}"], ASTAP_TIMEOUT_S)
    written = frame.with_suffix(".wcs")
    if not written.exists():
        return None
    cards = read_cards(written.read_text(encoding="latin-1"))
    keys = ("CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CD1_1", "CD1_2", "CD2_1", "CD2_2")
    if not all(isinstance(cards.get(k), float) for k in keys):
        return None
    c = {k: float(cards[k]) for k in keys}
    wcs = Wcs(c["CRVAL1"], c["CRVAL2"], (c["CRPIX1"], c["CRPIX2"]),
              (c["CD1_1"], c["CD1_2"], c["CD2_1"], c["CD2_2"]))  # fmt: skip
    sqm, zero_point = cards.get("SQM"), cards.get("MZEROR")
    return Theirs(
        sqm if isinstance(sqm, float) else None,
        zero_point if isinstance(zero_point, float) else None,
        wcs,
    )


def measure_ours(frame: Path, wcs: Wcs | None, bias: float, folder: Path) -> Ours | None:
    """As the sqm stage: catalogue beside astap.exe, air mass from the card at the solved centre."""
    with open(frame, "rb") as fh:
        header = read_header(fh)
    read = read_pixels(frame)
    code = catalogue_in(folder)
    if wcs is None or header is None or not isinstance(read, Pixels) or code is None:
        return None
    colour = is_colour(frame)
    found = calibrate(read.data, wcs, folder, code, colour=colour)
    altitude = card_altitude(header.cards, (wcs.ra_deg, wcs.dec_deg))
    airmass = None if altitude is None else airmass_of(altitude)
    if found is None or airmass is None:
        return None
    sqm = None
    if not colour or bias > 0:
        sqm = sky_brightness(found.zero_point_mag, found.sky_adu, bias, wcs.scale_arcsec, airmass)
    return Ours(sqm, found.zero_point_mag, found.stars, colour)


def _number(value: float | None, digits: int) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def main(
    argv: list[str],
    run: Run = _launch,
    measure: Measure = measure_ours,
    colour_of: Callable[[Path], bool] = is_colour,
) -> int:
    parser = argparse.ArgumentParser(description="AstroLog's SQM beside astap.exe -sqm")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--astap", default=str(ASTAP_EXE), help="astap.exe, not astap_cli")
    parser.add_argument("--cli", default=str(ASTAP_CLI), help="astap_cli, solves colour frames")
    parser.add_argument("--bias", type=float, default=0.0, help="bias of the camera, ADU")
    args = parser.parse_args(argv)
    frames = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in FRAME_SUFFIXES)
    print("| frame | tipo | ASTAP SQM | SQM | scarto | ASTAP MZEROR | zero point | stelle |")
    print("|---" * 8 + "|")
    gaps = []
    for frame in frames:
        mono = not colour_of(frame)
        if mono:
            theirs = run_astap(args.astap, frame, args.bias, run)
        else:
            theirs = run_astap(args.cli, frame, None, run)
        ours = measure(frame, theirs.wcs if theirs else None, args.bias, Path(args.astap).parent)
        their_sqm = theirs.sqm if theirs and mono else None
        their_zero = theirs.zero_point_mag if theirs and mono else None
        gap = (
            None if their_sqm is None or ours is None or ours.sqm is None else ours.sqm - their_sqm
        )
        if gap is not None:
            gaps.append(abs(gap))
        cells = [frame.name, "mono" if mono else "colori", _number(their_sqm, 2),
                 _number(ours.sqm if ours else None, 3), "-" if gap is None else f"{gap:+.3f}",
                 _number(their_zero, 4), _number(ours.zero_point_mag if ours else None, 4),
                 str(ours.stars) if ours else "-"]  # fmt: skip
        print("| " + " | ".join(cells) + " |")
    if gaps:
        print(f"\nscarto assoluto: mediana {statistics.median(gaps):.3f}, massimo {max(gaps):.3f} "
              f"su {len(gaps)} frame")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
