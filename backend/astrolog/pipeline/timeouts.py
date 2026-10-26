"""ASTAP's time per launch, learnt from this machine's successes (ADR 0039): prediction bound on
the logs of solved launches, per mode, floored; past a failed blind search waiting buys nothing."""

import math
import sqlite3
import statistics
from collections.abc import Sequence
from enum import StrEnum
from functools import cache

LEVEL = 0.999  # [D ADR 0039, one success in a thousand cut]
MIN_SOLVED = 20  # [D ADR 0039]
FLOOR_S = 30  # [D ADR 0039]
RECENT = 500  # [T] latest successes only: a new ASTAP or catalogue moves the times


class Mode(StrEnum):
    HINTED = "hinted"
    BLIND = "blind"


# the launch that decided is blind when it had no pointing: step blind, or no hint at all
_SOLVED = {
    Mode.HINTED: "SELECT launch_s FROM pipeline_solutions WHERE outcome = 'solved'"
    " AND machine = :machine AND launch_s > 0 AND step <> 'blind' AND hint_from IS NOT NULL"
    " ORDER BY tried_at DESC, frame_id DESC LIMIT :recent",
    Mode.BLIND: "SELECT launch_s FROM pipeline_solutions WHERE outcome = 'solved'"
    " AND machine = :machine AND launch_s > 0 AND (step = 'blind' OR hint_from IS NULL)"
    " ORDER BY tried_at DESC, frame_id DESC LIMIT :recent",
}
_FAILED_BLIND = (
    "SELECT max(launch_s) FROM pipeline_solutions WHERE outcome = 'no_solution'"
    " AND machine = :machine AND (step = 'blind' OR hint_from IS NULL)"
)


def t_quantile(p: float, df: int) -> float:
    """One-sided Student t quantile, by bisection on the exact CDF [C Abramowitz & Stegun 26.7.3-4,
    p. 948]; no scipy in the backend."""
    return _t_quantile(p, df)


@cache
def _t_quantile(p: float, df: int) -> float:
    low, high = 0.0, 1.0
    while _t_cdf(high, df) < p:
        high *= 2
    for _ in range(100):
        mid = (low + high) / 2
        low, high = (mid, high) if _t_cdf(mid, df) < p else (low, mid)
    return (low + high) / 2


def _t_cdf(t: float, df: int) -> float:
    """P(T <= t) for t >= 0: (1 + A(t|df)) / 2, A as the finite sums of A&S 26.7.3 and 26.7.4."""
    angle = math.atan(t / math.sqrt(df))
    cos2 = math.cos(angle) ** 2
    if df % 2:  # odd: 2/pi (angle + sin cos (1 + 2/3 cos^2 + 2.4/3.5 cos^4 ...))
        term, total = 1.0, 0.0
        if df > 1:
            total = term
            for k in range(2, df - 1, 2):
                term *= k / (k + 1) * cos2
                total += term
        a = 2 / math.pi * (angle + math.sin(angle) * math.cos(angle) * total)
    else:  # even: sin (1 + 1/2 cos^2 + 1.3/2.4 cos^4 ...)
        term = total = 1.0
        for k in range(1, df - 2, 2):
            term *= k / (k + 1) * cos2
            total += term
        a = math.sin(angle) * total
    return (1 + a) / 2


def prediction_limit(durations: Sequence[float]) -> float:
    """Upper bound for one more launch: mean + t(n-1) s sqrt(1 + 1/n) on the logs [C NIST Dataplot
    PREDICTION LIMITS, from Hahn & Meeker 1991 pp. 61-62]; times are lognormal (ADR 0039)."""
    logs = [math.log(d) for d in durations]
    n = len(logs)
    spread = statistics.stdev(logs) * math.sqrt(1 + 1 / n)
    return math.exp(statistics.fmean(logs) + t_quantile(LEVEL, n - 1) * spread)


def limit_of(solved: Sequence[float], failed_blind: Sequence[float], default_s: float) -> float:
    """Too few successes: the default. Else the bound, never under the floor, never over the
    slowest blind search that found nothing here."""
    if len(solved) < MIN_SOLVED:
        return default_s
    limit = prediction_limit(solved)
    if failed_blind:
        limit = min(limit, max(failed_blind))
    return max(FLOOR_S, limit)


def limits(conn: sqlite3.Connection, machine: str | None, default_s: float) -> dict[Mode, float]:
    """Read once per pass, by the pass that launches. No machine name: nothing matches."""
    asked = {"machine": machine, "recent": RECENT}
    failed = conn.execute(_FAILED_BLIND, asked).fetchone()[0]
    found = {}
    for mode, query in _SOLVED.items():
        rows = conn.execute(query, asked).fetchall()
        found[mode] = limit_of([r[0] for r in rows], [] if failed is None else [failed], default_s)
    return found
