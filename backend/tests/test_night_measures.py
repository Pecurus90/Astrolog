"""The measures of a night (docs/domini/misure.md, ADR 0045): each frame of the night takes the
measures of its own file through the bridge (folder and path), and a night is counted as the
Nights page counts it."""

import json
import os

import pytest

from astrolog import night_measures
from conftest import LATER

KEY = "hfd_px"


class _World:
    """The two worlds side by side, by SQL: the spine's frame, night, object, filter, the
    pipeline's file and measures. Paths written differently on purpose."""

    def __init__(self, conn, base) -> None:
        self.conn = conn
        site = conn.execute(
            "INSERT INTO sites (name, latitude, longitude, timezone, is_default, created_at)"
            " VALUES ('Casa', 45.5, 11.5, 'Europe/Rome', 1, ?)",
            (LATER,),
        ).lastrowid
        self.night = self._night(site, "2026-10-12")
        self.folder = conn.execute(
            "INSERT INTO folders (root_path, created_at) VALUES (?, ?)",
            (str(base) + os.sep, LATER),
        ).lastrowid
        self.root = conn.execute(
            "INSERT INTO pipeline_roots (path, written_key, real_key, ancestors, created_at)"
            " VALUES (?, 'w', 'r', '[]', ?)",
            (os.path.normpath(str(base)), LATER),
        ).lastrowid
        self.scan = conn.execute(
            "INSERT INTO pipeline_scans (root_id, scanned_at, reachable, volume_changed, new,"
            " changed, reread, unchanged, gone, skipped, unknown_keys, unknown_more, finished)"
            " VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, '{}', '{}', 0, 1)",
            (self.root, LATER),
        ).lastrowid
        self.n = 0

    def _night(self, site: int, date: str) -> int:
        return self.conn.execute(
            "INSERT INTO nights (site_id, night_date, created_at) VALUES (?, ?, ?)",
            (site, date, LATER),
        ).lastrowid

    def object(self, name: str = "") -> int:
        obj = self.conn.execute("INSERT INTO objects (created_at) VALUES (?)", (LATER,)).lastrowid
        self.conn.execute(
            "INSERT INTO object_names (object_id, name, origin, is_primary)"
            " VALUES (?, ?, 'raw', 1)",
            (obj, name or f"Oggetto {obj}"),
        )
        return obj

    def filter(self, name: str) -> int:
        return self.conn.execute(
            "INSERT INTO filters (name, passband, created_at) VALUES (?, ?, ?)",
            (name, name, LATER),
        ).lastrowid

    def frame(self, *, night=..., obj=None, flt=None, copy_of=None, rel=None) -> int:
        self.n += 1
        frame = self.conn.execute(
            "INSERT INTO frames (frame_hash, image_type, header_json, created_at, night_id,"
            " object_id, filter_id, copy_of) VALUES (?, 'light', '[]', ?, ?, ?, ?, ?)",
            (f"h{self.n}", LATER, self.night if night is ... else night, obj, flt, copy_of),
        ).lastrowid
        self.conn.execute(
            "INSERT INTO positions (frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
            " VALUES (?, ?, ?, 1, 1, ?)",
            (frame, self.folder, rel or f"M31/f{self.n}.fits", LATER),
        )
        return frame

    def file(
        self, rel: str, *, state="present", measured: float | None = None, exp=60.0, start=None
    ) -> int:
        """The pipeline's file at `rel`; `measured`: its HFD, None: not measured yet."""
        pframe = self.conn.execute(
            "INSERT INTO pipeline_frames (fingerprint, created_at) VALUES (?, ?)", (rel, LATER)
        ).lastrowid
        file = self.conn.execute(
            "INSERT INTO pipeline_files (root_id, rel_path, size, mtime_ns, state, seen_scan_id,"
            " arrived_scan_id, gone_scan_id, frame_id) VALUES (?, ?, 1, 1, ?, ?, ?, ?, ?)",
            (self.root, rel, state, self.scan, self.scan,
             self.scan if state == "gone" else None, pframe),
        ).lastrowid  # fmt: skip
        self.conn.execute(
            "INSERT INTO pipeline_headers (file_id, program, header) VALUES (?, 'N.I.N.A.', '{}')",
            (file,),
        )
        self.conn.execute(
            "INSERT INTO pipeline_cards (file_id, frame_type, exposure_s, camera, gain, start_utc)"
            " VALUES (?, 'light', ?, 'ZWO ASI2600MM Pro', 100, ?)",
            (file, exp, start),
        )
        if measured is not None:
            self.conn.execute(
                "INSERT INTO pipeline_measures (frame_id, file_id, outcome, measured_at, hfd_px,"
                " stars, kept, background_adu, noise_adu, ceiling_adu, saturated, median_adu,"
                " sigma_adu, entropy_bits, noise_ratio, trails)"
                " VALUES (?, ?, 'measured', ?, ?, 200, 180, 900, 12, 65535, 0, 900, 12, 5, 0.5, 0)",
                (pframe, file, LATER, measured),
            )
        return pframe

    def skipped(self, rel: str, reason: str) -> None:
        """A present file the new pipeline read and gave no frame to."""
        self.conn.execute(
            "INSERT INTO pipeline_files (root_id, rel_path, size, mtime_ns, state, seen_scan_id,"
            " arrived_scan_id, skip_reason) VALUES (?, ?, 1, 1, 'present', ?, ?, ?)",
            (self.root, rel, self.scan, self.scan, reason),
        )

    def shot(self, hfd: float | None, start=None, **frame) -> int:
        """A frame of the spine and its file in the pipeline, at the same path."""
        spine = self.frame(**frame)
        rel = self.conn.execute(
            "SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)
        ).fetchone()[0]
        self.file(rel, measured=hfd, start=start)
        return spine


def _row(conn, night: int, key: str = KEY, obj=None, flt=None):
    return conn.execute(
        "SELECT * FROM night_measures WHERE night_id = ? AND key = ?"
        " AND object_id IS ? AND filter_id IS ?",
        (night, key, obj, flt),
    ).fetchone()


def _group(conn, night: int, obj=None, flt=None):
    return conn.execute(
        "SELECT * FROM night_measure_groups WHERE night_id = ?"
        " AND object_id IS ? AND filter_id IS ?",
        (night, obj, flt),
    ).fetchone()


@pytest.fixture
def world(conn, tmp_path):
    return _World(conn, tmp_path / "Acquisizioni")


def test_a_frame_takes_the_measures_of_its_own_file(conn, world) -> None:
    spine = world.shot(3.2)
    night_measures.rebuild(conn)
    bridged = conn.execute("SELECT * FROM night_measure_frames").fetchall()
    assert [(r["frame_id"], r["pipeline_frame_id"]) for r in bridged] == [
        (spine, conn.execute("SELECT id FROM pipeline_frames").fetchone()[0])
    ]
    row = _row(conn, world.night)
    assert (row["frames"], row["measured"], row["median"]) == (1, 1, 3.2)


def test_the_root_is_the_same_folder_written_another_way(conn, tmp_path) -> None:
    """The spine keeps the folder as the user added it, the pipeline normalised: still one."""
    world = _World(conn, tmp_path / "Acq" / ".." / "Acq")
    world.shot(2.0)
    night_measures.rebuild(conn)
    assert _row(conn, world.night)["measured"] == 1


def test_a_file_gone_from_the_pipeline_gives_no_measures(conn, world) -> None:
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.file(rel, state="gone", measured=3.0)
    night_measures.rebuild(conn)
    assert conn.execute("SELECT COUNT(*) FROM night_measure_frames").fetchone()[0] == 0
    row = _row(conn, world.night)
    assert (row["frames"], row["measured"], row["median"]) == (1, 0, None)
    assert _group(conn, world.night)["pending"] == 1


def test_a_file_the_pipeline_skips_for_good_is_not_waiting(conn, world) -> None:
    """A program the new pipeline does not read: never measured, so not
    "still to measure" either; the frame says why (scanner.py)."""
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.skipped(rel, "not_supported")
    night_measures.rebuild(conn)
    bridged = conn.execute("SELECT * FROM night_measure_frames").fetchone()
    assert (bridged["pipeline_frame_id"], bridged["skip_reason"]) == (None, "not_supported")
    group = _group(conn, world.night)
    assert (group["frames"], group["pending"]) == (1, 0)


def test_a_file_unreadable_for_now_is_still_waiting(conn, world) -> None:
    """Unreadable or incomplete is tried again at the next scan."""
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.skipped(rel, "incomplete")
    night_measures.rebuild(conn)
    assert _group(conn, world.night)["pending"] == 1


def test_the_night_counts_its_frames_as_the_nights_page(conn, world) -> None:
    """A calibrated copy is not another hour of sky, a frame without a night is in no night."""
    first = world.shot(2.0)
    world.shot(4.0, copy_of=first)
    world.shot(9.0, night=None)
    night_measures.rebuild(conn)
    row = _row(conn, world.night)
    assert (row["frames"], row["measured"], row["median"]) == (1, 1, 2.0)


def test_medians_and_quartiles_per_object_per_filter_and_for_the_night(conn, world) -> None:
    m31, m33 = world.object(), world.object()
    lum, red = world.filter("L"), world.filter("R")
    for hfd in (1.0, 2.0, 3.0, 4.0, 5.0):
        world.shot(hfd, obj=m31, flt=lum)
    world.shot(8.0, obj=m33, flt=red)
    world.frame(obj=m33, flt=red)  # its file not scanned yet by the pipeline
    night_measures.rebuild(conn)
    whole = _row(conn, world.night)
    assert (whole["frames"], whole["measured"], whole["median"]) == (7, 6, 3.5)
    assert (whole["q1"], whole["q3"]) == (2.25, 4.75)  # type 7 (Hyndman & Fan)
    one = _row(conn, world.night, obj=m31, flt=lum)
    assert (one["frames"], one["median"], one["q1"], one["q3"]) == (5, 3.0, 2.0, 4.0)
    assert _row(conn, world.night, obj=m33)["frames"] == 2
    assert _row(conn, world.night, flt=red)["median"] == 8.0
    assert _group(conn, world.night, obj=m33)["pending"] == 1


def _at(hour: int) -> str:
    return f"2026-10-12T{hour:02d}:00:00.000000+00:00"


def test_the_trend_follows_the_shooting_order_not_the_values(conn, world) -> None:
    """24 medians along the night, each over its stretch of frames (MisureFrame:226)."""
    for hour, hfd in ((23, 9.0), (20, 1.0), (22, 5.0), (21, 3.0)):
        world.shot(hfd, start=_at(hour))
    world.shot(7.0)  # no time: after the timed ones
    night_measures.rebuild(conn)
    trend = json.loads(_row(conn, world.night)["trend"])
    assert len(trend) == night_measures.TREND == 24
    assert (trend[0], trend[-1]) == (1.0, 7.0)
    assert trend == sorted(trend[:20]) + trend[20:]  # 1, 3, 5, 9 then 7: time, not value


def test_a_long_night_takes_the_median_of_each_stretch(conn, world) -> None:
    for i in range(48):
        world.shot(float(i + 1), start=f"2026-10-12T20:{i:02d}:00.000000+00:00")
    night_measures.rebuild(conn)
    trend = json.loads(_row(conn, world.night)["trend"])
    assert (trend[0], trend[1], trend[-1]) == (1.5, 3.5, 47.5)


def test_under_four_values_there_is_no_trend(conn, world) -> None:
    for hfd in (1.0, 2.0, 3.0):
        world.shot(hfd)
    night_measures.rebuild(conn)
    assert _row(conn, world.night)["trend"] is None


def test_what_differs_among_the_measured_frames(conn, world) -> None:
    """Background and noise compare only with the same camera, gain and exposure (MisureFrame)."""
    world.shot(2.0)
    night_measures.rebuild(conn)
    assert json.loads(_group(conn, world.night)["differs"]) == []
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.file(rel, measured=2.0, exp=120.0)
    night_measures.rebuild(conn)
    assert json.loads(_group(conn, world.night)["differs"]) == ["exposure"]


def test_background_and_sky_brightness_compare_per_filter(conn, world) -> None:
    """Across two filters background, noise and SQM say "per filter" (MisureFrame:190-195,
    `perF`, 236); one filter, or another measure, gives its median."""
    lum, red = world.filter("L"), world.filter("R")
    world.shot(2.0, flt=lum)
    world.shot(3.0, flt=red)
    night_measures.rebuild(conn)
    assert _row(conn, world.night, "background_adu")["per_filter"] == 1
    assert _row(conn, world.night, "noise_adu")["per_filter"] == 1
    assert _row(conn, world.night, "hfd_px")["per_filter"] == 0
    assert _row(conn, world.night, "background_adu", flt=lum)["per_filter"] == 0
    assert _row(conn, world.night, "sqm")["per_filter"] == 0  # no filter has it


def test_a_rebuild_forgets_what_is_no_longer_there(conn, world) -> None:
    spine = world.shot(2.0)
    night_measures.rebuild(conn)
    conn.execute("UPDATE frames SET night_id = NULL WHERE id = ?", (spine,))
    night_measures.rebuild(conn)
    assert conn.execute("SELECT COUNT(*) FROM night_measures").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM night_measure_groups").fetchone()[0] == 0
