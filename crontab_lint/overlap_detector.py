"""Detects overlapping cron schedules between multiple crontab entries."""

from dataclasses import dataclass, field
from typing import List, Set, Tuple

from .parser import ParsedCron, parse, ParseError


@dataclass
class OverlapResult:
    entry_a: str
    entry_b: str
    overlap_minutes: int
    sample_times: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"OverlapResult(entry_a={self.entry_a!r}, entry_b={self.entry_b!r}, "
            f"overlap_minutes={self.overlap_minutes})"
        )


def _expand_field(values: str, min_val: int, max_val: int) -> Set[int]:
    """Expand a cron field string into a set of matching integers."""
    result: Set[int] = set()
    for part in values.split(","):
        if part == "*":
            result.update(range(min_val, max_val + 1))
        elif "/" in part:
            base, step = part.split("/", 1)
            step = int(step)
            start = min_val if base == "*" else int(base.split("-")[0])
            end = max_val if base == "*" else (int(base.split("-")[1]) if "-" in base else max_val)
            result.update(range(start, end + 1, step))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            result.update(range(int(lo), int(hi) + 1))
        else:
            result.add(int(part))
    return result


def _schedule_minutes(cron: ParsedCron) -> Set[Tuple[int, int, int, int, int]]:
    """Return a set of (minute, hour, dom, month, dow) tuples for the cron entry."""
    minutes = _expand_field(cron.minute, 0, 59)
    hours = _expand_field(cron.hour, 0, 23)
    doms = _expand_field(cron.day_of_month, 1, 31)
    months = _expand_field(cron.month, 1, 12)
    dows = _expand_field(cron.day_of_week, 0, 7)
    result: Set[Tuple[int, int, int, int, int]] = set()
    for mo in months:
        for d in doms:
            for dw in dows:
                for h in hours:
                    for m in minutes:
                        result.add((m, h, d, mo, dw % 7))
    return result


def detect_overlaps(entries: List[str]) -> List[OverlapResult]:
    """Given a list of raw crontab lines, detect pairwise schedule overlaps."""
    parsed: List[Tuple[str, ParsedCron]] = []
    for entry in entries:
        entry = entry.strip()
        if not entry or entry.startswith("#"):
            continue
        try:
            parsed.append((entry, parse(entry)))
        except ParseError:
            continue

    overlaps: List[OverlapResult] = []
    for i in range(len(parsed)):
        times_i = _schedule_minutes(parsed[i][1])
        for j in range(i + 1, len(parsed)):
            times_j = _schedule_minutes(parsed[j][1])
            common = times_i & times_j
            if common:
                samples = sorted(common)[:3]
                sample_strs = [
                    f"{mo:02d}-{d:02d} {h:02d}:{m:02d}"
                    for (m, h, d, mo, _) in samples
                ]
                overlaps.append(
                    OverlapResult(
                        entry_a=parsed[i][0],
                        entry_b=parsed[j][0],
                        overlap_minutes=len(common),
                        sample_times=sample_strs,
                    )
                )
    return overlaps
