"""AstroLog's measures beside the reference programs on the same frames (plan 24.05, ADR 0042):
ASTAP's -analyse and Image Analysis of PixInsight, run without a window. software-ok
Rerun at every measure sub-step; the gaps and their reasons go in docs/domini/misure.md.

Use: python tools/confronto_misure.py FOLDER [--astap EXE] [--reference EXE] [--groups FILE]
     [--out FILE] [--no-times]
Frames are read, never written: point it at copies anyway, both programs may leave files beside.

What each one gives (checked on its documentation and on a real frame):
- ASTAP -analyse 30: median HFD and star count from SNR 30; no sky, no noise. The exit code is
  HFD x 100 x 1e6 + stars (hnsky.org/astap.htm), two decimals where stdout prints the locale's one.
- Image Analysis (doc/tools/ImageAnalysis, 28/10/2026): every column of its measurements table,
  read by name; pixel values on [0,1], FWHM in px, undefined stored as 0 (Table 6, 7). No HFD.
Seconds per frame of both: ours per stage, its own with the extended measures and without.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path, PurePath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import sep  # pyright: ignore[reportMissingImports] -- compiled module, no stubs

from astrolog.astap import Run, find_exe
from astrolog.pipeline import stars
from astrolog.pipeline.airmass import airmass_of
from astrolog.pipeline.card import PierSide, read_card
from astrolog.pipeline.debayer import pattern_of
from astrolog.pipeline.pixels import Pixels, read_pixels
from astrolog.pipeline.scanner import program_of, read_header
from astrolog.pipeline.sky_measure import LIGHT, apparent_altitude_of, on_sky
from astrolog.pipeline.stars import Measured, measure_frame
from astrolog.pipeline.values import Value, as_number

FRAME_SUFFIXES = (".fits", ".fit", ".fts")
SNR_MIN = 30  # the -analyse threshold misure.md has always quoted
ADU_RANGE = 65535  # [C ImageAnalysis doc: pixel values on [0,1]; integer frames of 16 bits]
ASTAP_TIMEOUT_S = 120.0
ANALYSIS_TIMEOUT_S = 7200.0
ENV_REFERENCE = "ASTROLOG_PIXINSIGHT"  # software-ok
REFERENCE_CANDIDATES = (
    r"C:\Program Files\PixInsight\bin\PixInsight.exe",  # software-ok
    "/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight",  # software-ok
    "/opt/PixInsight/bin/PixInsight",  # software-ok
)
MONO, COLOR = "mono", "colori"
NO_GROUP = "-"
DEBAYERED = "_d"  # [C PCL DebayerParameters: outputPostfix default, the file an .xisf beside]

# The measurements table, ImageAnalysis doc Table 6, in its order; read by the index constants.
_COLUMNS = (
    "Index Approved Locked Path Weight Time Exposure Scale Stars FWHMpx FWHMpxSigma Eccentricity "
    "EccentricitySigma PSFResidual PSFResidualSigma Median Sigma Entropy Noise NoiseRatio SNR "
    "PSFSignalWeight PSFSNR PSFScale PSFScaleSNR PSFFlux PSFTotalMeanFlux PSFCount MStar NStar "
    "Azimuth Altitude Airmass Flags ElongationAngle ElongationCoherence FWHMTilt FWHMCurvature "
    "Gradient RowBanding ColumnBanding Trails RelativeExtinction CloudExtinction HourAngle "
    "PierSide MoonAltitude MoonSeparation MoonIllumination SunAltitude SensorTemperature "
    "AmbientTemperature FocuserPosition FocuserTemperature Gain GainSetting Offset"
)
NAMES = tuple(_COLUMNS.split())
NOT_MEASURES = ("Index", "Approved", "Locked", "Path", "Flags")
# Which may be a defined 0: measurementFlags bits, ImageAnalysis doc Table 7.
FLAG_BITS = {
    "ElongationAngle": 0x1, "ElongationCoherence": 0x1, "FWHMTilt": 0x2, "FWHMCurvature": 0x2,
    "Gradient": 0x4, "RowBanding": 0x4, "ColumnBanding": 0x4, "Trails": 0x8,
    "RelativeExtinction": 0x20, "CloudExtinction": 0x40, "HourAngle": 0x80, "PierSide": 0x100,
    "MoonAltitude": 0x200, "SunAltitude": 0x200, "MoonSeparation": 0x400,
    "MoonIllumination": 0x800, "SensorTemperature": 0x1000, "AmbientTemperature": 0x2000,
    "FocuserPosition": 0x4000, "FocuserTemperature": 0x8000, "Gain": 0x10000, "Offset": 0x20000,
    "GainSetting": 0x40000,
}  # fmt: skip

# Colour frames debayered first, VNG and the pattern from the header, as WBPP does; Debayer
# writes the per-channel noise the program reads (doc 2.1.4). One measure run with the extended
# measures, then each frame alone without file threads, for its seconds. Errors land in the
# file too: the program's console never reaches stdout on Windows.
_SCRIPT = """#engine v8
let mono = %s;
let colour = %s;
let work = %s;
let out = %s;
let names = %s;
let timed = %s;
let result = {names: names, rows: [], times: []};
function clock(path, label, fn) {
   let T = new ElapsedTime;
   fn();
   result.times.push([path, label, T.value]);
}
function debayer(f) {
   let D = new Debayer;
   D.cfaPattern = Debayer.Auto;
   D.debayerMethod = Debayer.VNG;
   D.targetItems = [[true, f]];
   D.outputDirectory = work;
   D.outputPostfix = "%s";
   D.overwriteExistingFiles = true;
   D.noGUIMessages = true;
   D.executeGlobal();
}
function analyse(fs, extended, threads) {
   let P = new ImageAnalysis;
   P.frames = fs.map(f => [true, f, "", ""]);
   P.task = ImageAnalysis.Task_Measure;
   P.onError = ImageAnalysis.OnError_Continue;
   P.extendedMeasurements = extended;
   P.fileCache = false;
   P.useFileThreads = threads;
   P.executeGlobal();
   return P;
}
try {
   let files = mono.slice();
   colour.forEach(f => {
      let d = work + "/" + File.extractName(f) + "%s.xisf";
      clock(d, "debayer", () => debayer(f));
      files.push(d);
   });
   let idx = names.map(n => {
      let i = ImageAnalysis["measurements_measurement" + n];
      if (i === undefined) throw new Error("no column " + n);
      return i;
   });
   let P = analyse(files, true, true);
   for (let row of P.measurements)
      result.rows.push(idx.map(i => row[i]));
   if (timed)
      files.forEach(f => {
         clock(f, "estese", () => analyse([f], true, false));
         clock(f, "base", () => analyse([f], false, false));
      });
} catch (e) {
   result.error = "" + e;
}
File.writeTextFile(out, JSON.stringify(result));
"""

# What measure_frame calls, by the name it looks up in stars.py.
OUR_STAGES = {
    "debayer VNG": "debayered",
    "rumore primo passo": "_sigma",
    "mediana 3x3": "median3x3",
    "rilevamento sep": "_found",
    "stelle utili": "_kept",
    "HFD": "_hfd",
    "forma": "shape_of",
    "fit PSF": "fit_stars",
    "stelle": "detect",
    "rumore MRS": "mrs",
    "statistiche dei pixel": "pixel_stats",
    "fondo MMT": "mstar_nstar",
    "stime per canale colore": "_estimates",
    "gradiente e banding": "_sky_field",
    "scie": "trails",
    "tilt ed elongazione": "_star_field",
}
BACKGROUND, READ, TOTAL = "fondo sep", "lettura file", "totale"


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
    seconds: dict[str, float] = field(default_factory=dict)  # by stage, and the total
    psf_residual: float | None = None  # only a fitted shape
    fwhm_sigma_px: float | None = None
    eccentricity_sigma: float | None = None
    psf_residual_sigma: float | None = None
    psf_flux_adu: float | None = None  # None: no fit
    psf_mean_flux_adu: float | None = None
    psf_count: int | None = None
    psf_signal_weight: float | None = None
    median_adu: float | None = None  # pixel statistics (pixel_stats.py, mmt.py)
    sigma_adu: float | None = None
    entropy_bits: float | None = None
    noise_ratio: float | None = None
    snr: float | None = None
    mstar_adu: float | None = None
    nstar_adu: float | None = None
    gradient_noise: float | None = None  # field (background.py, field.py)
    row_banding: float | None = None
    column_banding: float | None = None
    fwhm_tilt: float | None = None
    fwhm_curvature: float | None = None
    elongation_coherence: float | None = None
    trails: int | None = None
    azimuth_deg: float | None = None  # observation, from the card as altitude_deg
    hour_angle_h: float | None = None
    moon_altitude_deg: float | None = None
    moon_separation_deg: float | None = None
    moon_illumination: float | None = None
    sun_altitude_deg: float | None = None
    pier_side: int | None = None  # 0 East, 1 West, as his
    gain: int | None = None
    offset: int | None = None


@dataclass(frozen=True)
class Astap:
    hfd_px: float
    stars: int


@dataclass(frozen=True)
class Analysis:
    values: dict[str, float | None]  # by column name; None where undefined
    seconds: dict[str, float] = field(default_factory=dict)  # debayer, base, estese


@dataclass(frozen=True)
class Row:
    name: str
    color: bool
    group: str
    ours: Ours | None
    astap: Astap | None
    analysis: Analysis | None


type Measure = Callable[[Path], tuple[Ours, bool] | None]
type Spread = tuple[int, float, float, float]  # frames, min, median, max


def astap_from_code(code: int) -> Astap | None:
    """Under 1e6 no HFD came back: an error code, no star found, or a launch that failed (-1)."""
    if code < 1_000_000:
        return None
    return Astap(hfd_px=(code // 1_000_000) / 100, stars=code % 1_000_000)


def analysis_script(
    frames: Iterable[PurePath], colour: Iterable[PurePath], work: PurePath, out: PurePath,
    *, timed: bool,
) -> str:  # fmt: skip
    """Paths as JSON strings with forward slashes: the script reads a backslash as an escape.
    `frames` measured as they are; `colour` debayered into `work` first."""
    paths = [json.dumps([p.as_posix() for p in group]) for group in (frames, colour)]
    places = (json.dumps(work.as_posix()), json.dumps(out.as_posix()))
    flags = (json.dumps(list(NAMES)), json.dumps(timed))
    return _SCRIPT % (*paths, *places, *flags, DEBAYERED, DEBAYERED)


def debayered_name(frame: PurePath) -> str:
    """What the Image Analysis row of a colour frame is called: its debayered copy."""
    return f"{frame.stem}{DEBAYERED}.xisf"


def _defined(row: dict[str, Any]) -> dict[str, float | None]:
    flags = int(row["Flags"] or 0)
    values: dict[str, float | None] = {}
    for name in NAMES:
        if name in NOT_MEASURES:
            continue
        value = row[name]
        bit = FLAG_BITS.get(name)
        known = bool(flags & bit) if bit else value not in (0, None)
        values[name] = float(value) if known and value is not None else None
    return values


def read_analysis(text: str) -> dict[str, Analysis]:
    """By file name: the program writes the path its own way."""
    found = json.loads(text)
    if "error" in found:
        raise ValueError(f"Image Analysis: {found['error']}")
    seconds: dict[str, dict[str, float]] = {}
    for path, label, value in found["times"]:
        seconds.setdefault(PurePath(path).name, {})[label] = float(value)
    rows = (dict(zip(found["names"], row, strict=True)) for row in found["rows"])
    named = {PurePath(row["Path"]).name: _defined(row) for row in rows}
    return {name: Analysis(values, seconds.get(name, {})) for name, values in named.items()}


def read_groups(text: str) -> dict[str, str]:
    """Lines 'GROUP name-prefix': the bench's A (development) and B (check) by object."""
    pairs = (line.split(maxsplit=1) for line in text.splitlines() if line.strip())
    return {prefix.strip(): group for group, prefix in pairs}


def group_of(name: str, groups: dict[str, str]) -> str:
    matching = [prefix for prefix in groups if name.startswith(prefix)]
    return groups[max(matching, key=len)] if matching else NO_GROUP


class _Sep:
    """sep with its Background timed; the rest as it is."""

    def __init__(self, background: Callable[..., Any]) -> None:
        self.Background = background

    def __getattr__(self, name: str) -> Any:
        return getattr(sep, name)


@contextmanager
def stage_clock(seconds: dict[str, float]) -> Generator[None]:
    """Each stage of measure_frame timed where stars.py looks it up; a stage called inside
    another on its thread counts in the outer one only. Stages run side by side (cores.py): they
    add up past the total. Put back on the way out."""
    depth = threading.local()
    lock = threading.Lock()

    def timed(label: str, fn: Callable[..., Any]) -> Callable[..., Any]:
        def clocked(*args: Any, **kwargs: Any) -> Any:
            if getattr(depth, "n", 0):
                return fn(*args, **kwargs)
            depth.n = 1
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                depth.n = 0
                with lock:
                    seconds[label] = seconds.get(label, 0.0) + time.perf_counter() - start

        return clocked

    saved = {name: getattr(stars, name) for name in (*OUR_STAGES.values(), "sep")}
    for label, name in OUR_STAGES.items():
        setattr(stars, name, timed(label, saved[name]))
    stars.sep = _Sep(timed(BACKGROUND, sep.Background))
    try:
        yield
    finally:
        for name, fn in saved.items():
            setattr(stars, name, fn)


OBSERVATION = ("altitude_deg", "azimuth_deg", "hour_angle_h", *LIGHT, "pier_side", "gain",
               "offset")  # fmt: skip
PIER_SIDES = {PierSide.EAST: 0, PierSide.WEST: 1}  # [C ImageAnalysis par. 2.1.1, as ASCOM]


def card_observation(
    cards: dict[str, Value], centre: tuple[float, float] | None = None
) -> dict[str, Any]:
    """As the sky stage: the solved centre, else the card's pointing; site and mid exposure.
    Keys of OBSERVATION; unknown: None."""
    program = program_of(cards)
    if program is None:
        return dict.fromkeys(OBSERVATION)
    card = read_card(program, cards)
    start = None if card.start_utc is None else card.start_utc.isoformat(timespec="microseconds")
    row = {f.name: getattr(card, f.name) for f in fields(card)} | {"start_utc": start}
    ra, dec = centre or (None, None)
    [sky] = on_sky([row | {"ra_deg": ra, "dec_deg": dec}])
    pointed, lit = sky.pointed, sky.lit
    return {
        "altitude_deg": apparent_altitude_of(sky),
        "azimuth_deg": None if pointed is None else pointed.azimuth_deg,
        "hour_angle_h": None if pointed is None else pointed.hour_angle_h,
        **{name: None if lit is None else getattr(lit, name) for name in LIGHT},
        "pier_side": None if card.pier_side is None else PIER_SIDES[card.pier_side],
        "gain": card.gain, "offset": card.offset,
    }  # fmt: skip


def measure_ours(path: Path) -> tuple[Ours, bool] | None:
    """measure_frame as the pipeline calls it, timed by stage; colour from BAYERPAT."""
    start = time.perf_counter()
    with open(path, "rb") as fh:
        header = read_header(fh)
    read = read_pixels(path)
    if header is None or not isinstance(read, Pixels):
        return None
    pattern = pattern_of(header.cards)
    if pattern is None and header.cards.get("BAYERPAT"):
        return None  # a matrix not R G B: the pipeline says not_supported, so does this
    seconds = {READ: time.perf_counter() - start}
    with stage_clock(seconds):
        found = measure_frame(
            read.data,
            saturation=read.saturation,
            pattern=pattern,
            pedestal=as_number(header.cards.get("PEDESTAL")) or 0.0,
        )
    seconds[TOTAL] = time.perf_counter() - start
    hfd = found.hfd_px if isinstance(found, Measured) else None
    shape = found.shape
    fwhm, eccentricity = (shape.fwhm_px, shape.eccentricity) if shape else (None, None)
    spread = shape.spread if shape else None
    seen = card_observation(header.cards)
    ours = Ours(found.stars, hfd, found.background_adu, found.noise_adu, fwhm, eccentricity,
                found.psf_snr, seen["altitude_deg"], seconds,
                shape.psf_residual if shape else None, spread.fwhm_px if spread else None,
                spread.eccentricity if spread else None,
                spread.psf_residual if spread else None, found.psf_flux_adu,
                found.psf_mean_flux_adu, found.psf_count, found.psf_signal_weight,
                found.median_adu, found.sigma_adu, found.entropy_bits, found.noise_ratio,
                found.snr, found.mstar_adu, found.nstar_adu, found.gradient_noise,
                found.row_banding, found.column_banding, found.fwhm_tilt, found.fwhm_curvature,
                found.elongation_coherence, found.trails,
                **{k: v for k, v in seen.items() if k != "altitude_deg"})  # fmt: skip
    return ours, pattern is not None


def _over(ours: float | None, theirs: float | None, scale: float = 1.0) -> float | None:
    return ours / (theirs * scale) if ours is not None and theirs else None


def _minus(ours: float | None, theirs: float | None) -> float | None:
    """A count mostly 0 on both sides: the difference, not a ratio."""
    return ours - theirs if ours is not None and theirs is not None else None


def _turn(ours: float | None, theirs: float | None, full: float) -> float | None:
    """An angle's difference the short way round: 359.9 against 0.1 is -0.2."""
    if ours is None or theirs is None:
        return None
    return (ours - theirs + full / 2) % full - full / 2


def _pairs(row: Row) -> dict[str, float | None]:
    """Ours over theirs, one entry per measure both programs give."""
    o, astap = row.ours, row.astap
    if o is None:
        return {}
    v = row.analysis.values if row.analysis else {}
    airmass = None if o.altitude_deg is None else airmass_of(o.altitude_deg)
    return {
        "stelle / ASTAP": _over(o.stars, astap.stars if astap else None),
        "HFD / ASTAP HFD": _over(o.hfd_px, astap.hfd_px if astap else None),
        "stelle / Image Analysis": _over(o.stars, v.get("Stars")),
        "FWHM / Image Analysis": _over(o.fwhm_px, v.get("FWHMpx")),
        "HFD / FWHM Image Analysis": _over(o.hfd_px, v.get("FWHMpx")),
        "eccentricita' / Image Analysis": _over(o.eccentricity, v.get("Eccentricity")),
        "FWHM Sigma / Image Analysis": _over(o.fwhm_sigma_px, v.get("FWHMpxSigma")),
        "eccentricita' Sigma / Image Analysis": _over(
            o.eccentricity_sigma, v.get("EccentricitySigma")
        ),
        "PSFResidual / Image Analysis": _over(o.psf_residual, v.get("PSFResidual")),
        "PSFResidual Sigma / Image Analysis": _over(
            o.psf_residual_sigma, v.get("PSFResidualSigma")
        ),
        "fondo / mediana Image Analysis": _over(o.background_adu, v.get("Median"), ADU_RANGE),
        "rumore / Image Analysis": _over(o.noise_adu, v.get("Noise"), ADU_RANGE),
        "PSF SNR / Image Analysis": _over(o.psf_snr, v.get("PSFSNR")),
        "flusso PSF / Image Analysis": _over(o.psf_flux_adu, v.get("PSFFlux"), ADU_RANGE),
        "flusso medio PSF / Image Analysis": _over(
            o.psf_mean_flux_adu, v.get("PSFTotalMeanFlux"), ADU_RANGE
        ),
        "fit PSF / Image Analysis": _over(o.psf_count, v.get("PSFCount")),
        "PSF Signal Weight / Image Analysis": _over(o.psf_signal_weight, v.get("PSFSignalWeight")),
        "mediana / Image Analysis": _over(o.median_adu, v.get("Median"), ADU_RANGE),
        "Sigma / Image Analysis": _over(o.sigma_adu, v.get("Sigma"), ADU_RANGE),
        "entropia / Image Analysis": _over(o.entropy_bits, v.get("Entropy")),
        "NoiseRatio / Image Analysis": _over(o.noise_ratio, v.get("NoiseRatio")),
        "SNR / Image Analysis": _over(o.snr, v.get("SNR")),
        "M* / Image Analysis": _over(o.mstar_adu, v.get("MStar"), ADU_RANGE),
        "N* / Image Analysis": _over(o.nstar_adu, v.get("NStar"), ADU_RANGE),
        "gradiente / Image Analysis": _over(o.gradient_noise, v.get("Gradient")),
        "banding righe / Image Analysis": _over(o.row_banding, v.get("RowBanding")),
        "banding colonne / Image Analysis": _over(o.column_banding, v.get("ColumnBanding")),
        "tilt FWHM / Image Analysis": _over(o.fwhm_tilt, v.get("FWHMTilt")),
        "curvatura FWHM / Image Analysis": _over(o.fwhm_curvature, v.get("FWHMCurvature")),
        "coerenza / Image Analysis": _over(o.elongation_coherence, v.get("ElongationCoherence")),
        "scie meno Image Analysis": _minus(o.trails, v.get("Trails")),
        "altezza / Image Analysis": _over(o.altitude_deg, v.get("Altitude")),
        "massa d'aria / Image Analysis": _over(airmass, v.get("Airmass")),
        "azimut meno Image Analysis (gradi)": _turn(o.azimuth_deg, v.get("Azimuth"), 360.0),
        "angolo orario meno Image Analysis (gradi)": _turn(
            None if o.hour_angle_h is None else o.hour_angle_h * 15,
            None if v.get("HourAngle") is None else v["HourAngle"] * 15,
            360.0,
        ),
        "Luna alta meno Image Analysis": _minus(o.moon_altitude_deg, v.get("MoonAltitude")),
        "distanza Luna meno Image Analysis": _minus(o.moon_separation_deg, v.get("MoonSeparation")),
        "Luna illuminata meno Image Analysis": _minus(
            o.moon_illumination, v.get("MoonIllumination")
        ),
        "Sole alto meno Image Analysis": _minus(o.sun_altitude_deg, v.get("SunAltitude")),
        "lato del pilastro meno Image Analysis": _minus(o.pier_side, v.get("PierSide")),
        "gain meno Image Analysis": _minus(o.gain, v.get("GainSetting")),
        "offset meno Image Analysis": _minus(o.offset, v.get("Offset")),
    }


RATIO_NAMES = tuple(_pairs(Row("", False, NO_GROUP, Ours(1, 1.0, 1.0, 1.0), None, None)))


def _kind(row: Row) -> str:
    return COLOR if row.color else MONO


def ratios(rows: Iterable[Row]) -> dict[str, dict[str, Spread]]:
    """Per measure, per sensor kind and group ('mono A'): a colour frame on its debayered copy."""
    gathered: dict[str, dict[str, list[float]]] = {name: {} for name in RATIO_NAMES}
    for row in rows:
        for name, value in _pairs(row).items():
            if value is not None:
                gathered[name].setdefault(f"{_kind(row)} {row.group}", []).append(value)
    return {
        name: {key: (len(v), min(v), statistics.median(v), max(v)) for key, v in keys.items()}
        for name, keys in gathered.items()
    }


def times(rows: Iterable[Row]) -> dict[str, dict[str, float]]:
    """Median seconds a frame per kind: ours by stage, the program's by label."""
    gathered: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        kind = gathered.setdefault(_kind(row), {})
        for label, value in (row.ours.seconds if row.ours else {}).items():
            kind.setdefault(f"AstroLog {label}", []).append(value)
        theirs = row.analysis.seconds if row.analysis else {}
        for label, value in theirs.items():
            kind.setdefault(f"Image Analysis {label}", []).append(value)
        if "debayer" in theirs and "estese" in theirs:
            both = theirs["debayer"] + theirs["estese"]
            kind.setdefault("Image Analysis estese + debayer", []).append(both)
    return {k: {label: statistics.median(v) for label, v in t.items()} for k, t in gathered.items()}


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


def run_analysis(
    exe: str, frames: list[Path], colour: list[Path], run: Run, *, timed: bool
) -> dict[str, Analysis]:
    with tempfile.TemporaryDirectory() as work:
        script, out = Path(work) / "analysis.js", Path(work) / "analysis.json"
        text = analysis_script(frames, colour, Path(work), out, timed=timed)
        script.write_text(text, encoding="utf-8")
        cmd = [exe, "-n", "--automation-mode", "--no-startup-scripts", f"-r={script.as_posix()}"]
        run([*cmd, "--force-exit"], ANALYSIS_TIMEOUT_S)
        if not out.exists():
            print("  Image Analysis: nessun risultato scritto")
            return {}
        return read_analysis(out.read_text(encoding="utf-8"))


def _number(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def _cells(row: Row) -> list[str]:
    o, a = row.ours, row.astap
    v = row.analysis.values if row.analysis else {}

    def ia(name: str, scale: float = 1.0) -> float | None:
        value = v.get(name)
        return None if value is None else value * scale

    stars_ia = ia("Stars")
    return [
        row.name, _kind(row), row.group,
        str(o.stars) if o else "-", "-" if stars_ia is None else str(int(stars_ia)),
        _number(o.fwhm_px if o else None), _number(ia("FWHMpx")),
        _number(o.eccentricity if o else None), _number(ia("Eccentricity")),
        _number(o.background_adu if o else None, 1), _number(ia("Median", ADU_RANGE), 1),
        _number(o.noise_adu if o else None, 1), _number(ia("Noise", ADU_RANGE), 1),
        _number(o.psf_snr if o else None, 4), _number(ia("PSFSNR"), 4),
        _number(o.altitude_deg if o else None), _number(ia("Altitude")),
        _number(o.hfd_px if o else None), _number(a.hfd_px if a else None),
        str(a.stars) if a else "-",
        _number(o.seconds.get(TOTAL) if o else None),
        _number(row.analysis.seconds.get("estese") if row.analysis else None),
    ]  # fmt: skip


def _print_rows(rows: list[Row]) -> None:
    print("| frame | tipo | gruppo | stelle | IA | FWHM | IA | eccentricita' | IA | fondo "
          "| IA mediana | rumore | IA | PSF SNR | IA | altezza | IA | HFD | ASTAP HFD "
          "| ASTAP stelle | s | IA s |")  # fmt: skip
    print("|---" * 22 + "|")
    for row in rows:
        print("| " + " | ".join(_cells(row)) + " |")


def _print_ratios(table: dict[str, dict[str, Spread]]) -> None:
    print("\nNostro diviso il loro: frame, minimo / mediana / massimo (IA = Image Analysis)")
    for name, keys in table.items():
        for key, (n, low, mid, high) in sorted(keys.items()):
            print(f"- {name}, {key}: n={n} {low:.3f} / {mid:.3f} / {high:.3f}")


def _print_times(table: dict[str, dict[str, float]]) -> None:
    print("\nSecondi a frame, mediana")
    for kind, labels in sorted(table.items()):
        print(f"== {kind}")
        for label, value in labels.items():
            print(f"  {label:40s} {value:7.3f}")


def _arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AstroLog's measures beside the references")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--astap", help="astap_cli; default: the app's own search")
    parser.add_argument("--reference", help=f"its executable; default: {ENV_REFERENCE}")
    parser.add_argument("--groups", type=Path, help="lines 'GROUP name-prefix'")
    parser.add_argument("--out", type=Path, help="every row as JSON, for the next sub-steps")
    parser.add_argument("--no-times", action="store_true", help="skip timing each frame alone")
    return parser.parse_args(argv)


def main(argv: list[str], run: Run = _launch, measure: Measure = measure_ours) -> int:
    args = _arguments(argv)
    frames = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in FRAME_SUFFIXES)
    if not frames:
        print(f"nessun frame in {args.folder}")
        return 1
    astap = args.astap or find_exe(env=os.environ)
    reference = args.reference or _reference_exe()
    groups = read_groups(args.groups.read_text(encoding="utf-8")) if args.groups else {}
    print(f"{len(frames)} frame; ASTAP: {astap or 'non trovato'}; Image Analysis: "
          f"{reference or 'non trovato'}")  # fmt: skip
    measured = {frame: measure(frame) or (None, False) for frame in frames}
    colour = [frame for frame, (_, color) in measured.items() if color]
    mono = [frame for frame in frames if frame not in colour]
    found = run_analysis(reference, mono, colour, run, timed=not args.no_times) if reference else {}
    rows = []
    for frame, (ours, color) in measured.items():
        theirs = found.get(debayered_name(frame) if color else frame.name)
        star = run_astap(astap, frame, run) if astap else None
        rows.append(Row(frame.name, color, group_of(frame.name, groups), ours, star, theirs))
    _print_rows(rows)
    _print_ratios(ratios(rows))
    _print_times(times(rows))
    if args.out:
        args.out.write_text(json.dumps([asdict(r) for r in rows], indent=1), encoding="utf-8")
    return 0


def _reference_exe() -> str | None:
    declared = os.environ.get(ENV_REFERENCE)
    if declared:
        return declared
    return next((c for c in REFERENCE_CANDIDATES if Path(c).is_file()), None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
