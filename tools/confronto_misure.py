"""AstroLog's measures beside the reference programs on the same frames (plan 24.05): ASTAP's
-analyse and the SubframeSelector of PixInsight, run without a window. software-ok
Rerun at every measure sub-step; the gaps and their reasons go in docs/domini/misure.md.

Use: python tools/confronto_misure.py FOLDER [--astap EXE] [--subframe EXE]
Frames are read, never written: point it at copies anyway, both programs may leave files beside.

What each one gives (checked on its sources and on a real frame):
- ASTAP -analyse 30: median HFD and star count from SNR 30; no sky, no noise. The exit code is
  HFD x 100 x 1e6 + stars (hnsky.org/astap.htm), two decimals where stdout prints the locale's one.
- SubframeSelector (PCL SubframeSelectorProcess.cpp, column order fixed there): FWHM in px and
  eccentricity from a PSF fit, median and MRS noise on [0,1] of the 16-bit range, star count.
  No HFD.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass, fields
from pathlib import Path, PurePath

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from astrolog.astap import Run, find_exe
from astrolog.pipeline.card import read_card
from astrolog.pipeline.debayer import pattern_of
from astrolog.pipeline.pixels import Pixels, read_pixels
from astrolog.pipeline.scanner import program_of, read_header
from astrolog.pipeline.sky_measure import apparent_altitudes
from astrolog.pipeline.stars import Measured, measure_frame
from astrolog.pipeline.values import Value

FRAME_SUFFIXES = (".fits", ".fit", ".fts")
SNR_MIN = 30  # the -analyse threshold misure.md has always quoted
ADU_RANGE = 65535  # [C PCL: integer images read on [0,1] of the 16-bit range]
ASTAP_TIMEOUT_S = 120.0
SUBFRAME_TIMEOUT_S = 1800.0
ENV_SUBFRAME = "ASTROLOG_PIXINSIGHT"  # software-ok
SUBFRAME_CANDIDATES = (
    r"C:\Program Files\PixInsight\bin\PixInsight.exe",  # software-ok
    "/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight",  # software-ok
    "/opt/PixInsight/bin/PixInsight",  # software-ok
)
MONO, COLOR = "mono", "colori"

DEBAYERED = "_d"  # [C PCL DebayerParameters: outputPostfix default, the file an .xisf beside]

# Colour frames debayered first, VNG and the pattern from the header, as WBPP does.
# Measurements columns: 3 path, 5 FWHM, 6 eccentricity, 10 median, 12 noise, 14 stars
# (SubframeSelectorProcess.cpp); 28 PSF SNR, found on the 24 copies: c3 F^2 / (c4 sigma^2)
# from column 21 (PSF flux) and 12 gives it back within 3% (misure.md); 20 altitude, degrees.
# Errors land in the file too: the program's console never reaches stdout on Windows.
_SCRIPT = """var files = %s;
var colour = %s;
var work = %s;
var out = %s;
var lines = ["path,fwhm_px,eccentricity,median,noise,stars,psf_snr,altitude_deg"];
try {
   if (colour.length > 0) {
      var D = new Debayer;
      D.cfaPattern = Debayer.prototype.Auto;
      D.debayerMethod = Debayer.prototype.VNG;
      D.targetItems = colour.map(function (f) { return [true, f]; });
      D.outputDirectory = work;
      D.outputPostfix = "%s";
      D.overwriteExistingFiles = true;
      D.noGUIMessages = true;
      D.executeGlobal();
      colour.forEach(function (f) {
         files.push(work + "/" + File.extractName(f) + "%s.xisf");
      });
   }
   var SS = new SubframeSelector;
   SS.routine = SubframeSelector.prototype.MeasureSubframes;
   SS.nonInteractive = true;
   SS.fileCache = false;
   SS.noNoiseAndSignalWarnings = true;
   SS.subframes = files.map(function (f) { return [true, f, "", ""]; });
   SS.executeGlobal();
   for (var i = 0; i < SS.measurements.length; ++i) {
      var m = SS.measurements[i];
      lines.push([m[3], m[5], m[6], m[10], m[12], m[14], m[28], m[20]].join(","));
   }
} catch (e) {
   lines.push("error," + e);
}
File.writeTextFile(out, lines.join("\\n") + "\\n");
"""


@dataclass(frozen=True)
class Ours:
    stars: int
    hfd_px: float | None  # None: too few stars kept
    background_adu: float
    noise_adu: float
    fwhm_px: float | None = None  # None: no shape, or not measurable
    eccentricity: float | None = None
    psf_snr: float | None = None
    altitude_deg: float | None = None  # from the card: pointing, site, mid exposure


@dataclass(frozen=True)
class Astap:
    hfd_px: float
    stars: int


@dataclass(frozen=True)
class Subframe:
    fwhm_px: float
    median_adu: float
    noise_adu: float
    stars: int
    eccentricity: float | None = None
    psf_snr: float | None = None
    altitude_deg: float | None = None


@dataclass(frozen=True)
class Row:
    name: str
    color: bool
    ours: Ours | None
    astap: Astap | None
    subframe: Subframe | None


type Measure = Callable[[Path], tuple[Ours, bool] | None]
type Ratio = tuple[float, float, float]  # min, median, max


def astap_from_code(code: int) -> Astap | None:
    """Under 1e6 no HFD came back: an error code, no star found, or a launch that failed (-1)."""
    if code < 1_000_000:
        return None
    return Astap(hfd_px=(code // 1_000_000) / 100, stars=code % 1_000_000)


def subframe_script(
    frames: Iterable[PurePath], colour: Iterable[PurePath], work: PurePath, out: PurePath
) -> str:
    """Paths as JSON strings with forward slashes: the script reads a backslash as an escape.
    `frames` measured as they are; `colour` debayered into `work` first."""
    paths = [json.dumps([p.as_posix() for p in group]) for group in (frames, colour)]
    places = (json.dumps(work.as_posix()), json.dumps(out.as_posix()))
    return _SCRIPT % (*paths, *places, DEBAYERED, DEBAYERED)


def debayered_name(frame: PurePath) -> str:
    """What the SubframeSelector row of a colour frame is called: its debayered copy."""
    return f"{frame.stem}{DEBAYERED}.xisf"


def read_subframes(text: str) -> dict[str, Subframe]:
    """By file name: the program writes the path its own way."""
    found = {}
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        if line.startswith("error,"):
            raise ValueError(f"SubframeSelector: {line.removeprefix('error,')}")
        path, fwhm, eccentricity, median, noise, stars, snr, alt = line.rsplit(
            ",", 7
        )  # comma in a path
        found[Path(path).name] = Subframe(
            fwhm_px=float(fwhm),
            median_adu=float(median) * ADU_RANGE,
            noise_adu=float(noise) * ADU_RANGE,
            stars=int(float(stars)),
            eccentricity=float(eccentricity),
            psf_snr=float(snr),
            altitude_deg=float(alt) if alt.strip() else None,
        )
    return found


def card_altitude(cards: dict[str, Value]) -> float | None:
    """As the sky stage on a shot not solved: the card's pointing, site and mid exposure."""
    program = program_of(cards)
    if program is None:
        return None
    card = read_card(program, cards)
    start = None if card.start_utc is None else card.start_utc.isoformat(timespec="microseconds")
    row = {f.name: getattr(card, f.name) for f in fields(card)} | {"start_utc": start}
    [altitude] = apparent_altitudes([row | {"ra_deg": None, "dec_deg": None}])
    return altitude


def measure_ours(path: Path) -> tuple[Ours, bool] | None:
    """measure_frame as the pipeline calls it; colour from BAYERPAT and its offsets."""
    with open(path, "rb") as fh:
        header = read_header(fh)
    read = read_pixels(path)
    if header is None or not isinstance(read, Pixels):
        return None
    pattern = pattern_of(header.cards)
    if pattern is None and header.cards.get("BAYERPAT"):
        return None  # a matrix not R G B: the pipeline says not_supported, so does this
    found = measure_frame(read.data, saturation=read.saturation, pattern=pattern)
    hfd = found.hfd_px if isinstance(found, Measured) else None
    shape = found.shape
    fwhm, eccentricity = (shape.fwhm_px, shape.eccentricity) if shape else (None, None)
    ours = Ours(found.stars, hfd, found.background_adu, found.noise_adu, fwhm, eccentricity,
                found.psf_snr, card_altitude(header.cards))  # fmt: skip
    return ours, pattern is not None


def _pairs(row: Row) -> dict[str, float | None]:
    """Ours over theirs, one entry per measure both programs give."""
    ours, astap, sub = row.ours, row.astap, row.subframe
    if ours is None:
        return {}
    hfd, fwhm, eccentricity = ours.hfd_px, ours.fwhm_px, ours.eccentricity
    theirs = sub.eccentricity if sub else None
    return {
        "stelle / ASTAP": ours.stars / astap.stars if astap and astap.stars else None,
        "HFD / ASTAP HFD": hfd / astap.hfd_px if astap and hfd else None,
        "stelle / SubframeSelector": ours.stars / sub.stars if sub and sub.stars else None,
        "HFD / SubframeSelector FWHM": hfd / sub.fwhm_px if sub and hfd and sub.fwhm_px else None,
        "FWHM / SubframeSelector FWHM": (
            fwhm / sub.fwhm_px if sub and fwhm and sub.fwhm_px else None
        ),
        "eccentricita' / SubframeSelector": (
            eccentricity / theirs if eccentricity is not None and theirs else None
        ),
        "fondo / SubframeSelector": (
            ours.background_adu / sub.median_adu if sub and sub.median_adu else None
        ),
        "rumore / SubframeSelector": (
            ours.noise_adu / sub.noise_adu if sub and sub.noise_adu else None
        ),
        "PSF SNR / SubframeSelector": (
            ours.psf_snr / sub.psf_snr if sub and sub.psf_snr and ours.psf_snr else None
        ),
        "altezza / SubframeSelector": (
            ours.altitude_deg / sub.altitude_deg
            if sub and sub.altitude_deg and ours.altitude_deg is not None
            else None
        ),
    }


RATIO_NAMES = tuple(_pairs(Row("", False, Ours(1, 1.0, 1.0, 1.0), None, None)))


def ratios(rows: Iterable[Row]) -> dict[str, dict[str, Ratio]]:
    """Per measure, per sensor kind: a colour frame is measured on its debayered intensity."""
    gathered: dict[str, dict[str, list[float]]] = {name: {} for name in RATIO_NAMES}
    for row in rows:
        for name, value in _pairs(row).items():
            if value is not None:
                gathered[name].setdefault(COLOR if row.color else MONO, []).append(value)
    return {
        name: {kind: (min(v), statistics.median(v), max(v)) for kind, v in kinds.items()}
        for name, kinds in gathered.items()
    }


def _launch(cmd: list[str], timeout_s: float) -> tuple[int, str]:
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"  {cmd[0]}: {error}")
        return -1, ""
    return done.returncode, done.stdout


def run_astap(exe: str, frame: Path, run: Run) -> Astap | None:
    code, _ = run([exe, "-f", str(frame), "-analyse", str(SNR_MIN)], ASTAP_TIMEOUT_S)
    return astap_from_code(code)


def run_subframes(
    exe: str, frames: list[Path], colour: list[Path], run: Run
) -> dict[str, Subframe]:
    with tempfile.TemporaryDirectory() as work:
        script, out = Path(work) / "subframes.js", Path(work) / "subframes.csv"
        script.write_text(subframe_script(frames, colour, Path(work), out), encoding="utf-8")
        cmd = [exe, "-n", "--automation-mode", "--no-startup-scripts", f"-r={script.as_posix()}"]
        run([*cmd, "--force-exit"], SUBFRAME_TIMEOUT_S)
        if not out.exists():
            print("  SubframeSelector: nessun risultato scritto")
            return {}
        return read_subframes(out.read_text(encoding="utf-8"))


def _number(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def _print_rows(rows: list[Row]) -> None:
    print("| frame | tipo | stelle | HFD | FWHM | eccentricita' | fondo | rumore "
          "| ASTAP stelle | ASTAP HFD | SubframeSelector stelle | FWHM | eccentricita' "
          "| mediana | rumore | PSF SNR | PSF SNR SubframeSelector | altezza "
          "| altezza SubframeSelector |")  # fmt: skip
    print("|---" * 19 + "|")
    for row in rows:
        o, a, s = row.ours, row.astap, row.subframe
        cells = [
            row.name,
            COLOR if row.color else MONO,
            str(o.stars) if o else "-",
            _number(o.hfd_px if o else None),
            _number(o.fwhm_px if o else None),
            _number(o.eccentricity if o else None),
            _number(o.background_adu if o else None, 1),
            _number(o.noise_adu if o else None, 1),
            str(a.stars) if a else "-",
            _number(a.hfd_px if a else None),
            str(s.stars) if s else "-",
            _number(s.fwhm_px if s else None),
            _number(s.eccentricity if s else None),
            _number(s.median_adu if s else None, 1),
            _number(s.noise_adu if s else None, 1),
            _number(o.psf_snr if o else None, 4),
            _number(s.psf_snr if s else None, 4),
            _number(o.altitude_deg if o else None),
            _number(s.altitude_deg if s else None),
        ]
        print("| " + " | ".join(cells) + " |")


def _print_ratios(table: dict[str, dict[str, Ratio]]) -> None:
    print("\nNostro diviso il loro: minimo, mediana, massimo")
    for name, kinds in table.items():
        for kind, (low, mid, high) in sorted(kinds.items()):
            print(f"- {name}, {kind}: {low:.2f} / {mid:.2f} / {high:.2f}")


def main(argv: list[str], run: Run = _launch, measure: Measure = measure_ours) -> int:
    parser = argparse.ArgumentParser(description="AstroLog's measures beside the references")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--astap", help="astap_cli; default: the app's own search")
    parser.add_argument("--subframe", help=f"the program's executable; default: {ENV_SUBFRAME}")
    args = parser.parse_args(argv)
    frames = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in FRAME_SUFFIXES)
    if not frames:
        print(f"nessun frame in {args.folder}")
        return 1
    astap = args.astap or find_exe(env=os.environ)
    subframe = args.subframe or _subframe_exe()
    print(f"{len(frames)} frame; ASTAP: {astap or 'non trovato'}; SubframeSelector: "
          f"{subframe or 'non trovato'}")  # fmt: skip
    measured = {frame: measure(frame) or (None, False) for frame in frames}
    colour = [frame for frame, (_, color) in measured.items() if color]
    mono = [frame for frame in frames if frame not in colour]
    subs = run_subframes(subframe, mono, colour, run) if subframe else {}
    rows = []
    for frame, (ours, color) in measured.items():
        found = run_astap(astap, frame, run) if astap else None
        sub = subs.get(debayered_name(frame) if color else frame.name)
        rows.append(Row(frame.name, color, ours, found, sub))
    _print_rows(rows)
    _print_ratios(ratios(rows))
    return 0


def _subframe_exe() -> str | None:
    declared = os.environ.get(ENV_SUBFRAME)
    if declared:
        return declared
    return next((c for c in SUBFRAME_CANDIDATES if Path(c).is_file()), None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
