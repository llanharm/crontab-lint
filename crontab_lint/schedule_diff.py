"""Diff two cron schedules: show when they diverge over a time window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set

from .scheduler import next_runs


@dataclass
class ScheduleDiff:
    """Result of comparing two cron schedules."""

    only_in_a: List[datetime] = field(default_factory=list)
    only_in_b: List[datetime] = field(default_factory=list)
    common: List[datetime] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_a or self.only_in_b)

    def summary(self) -> str:
        lines = [
            f"Common runs   : {len(self.common)}",
            f"Only in first : {len(self.only_in_a)}",
            f"Only in second: {len(self.only_in_b)}",
        ]
        return "\n".join(lines)


def diff_schedules(
    expr_a: str,
    expr_b: str,
    after: datetime | None = None,
    count: int = 20,
) -> ScheduleDiff:
    """Compare the next *count* runs of two cron expressions.

    Args:
        expr_a: First cron expression (five fields, no command).
        expr_b: Second cron expression (five fields, no command).
        after: Window start (default: now).
        count: How many runs to sample per expression.

    Returns:
        A :class:`ScheduleDiff` instance.
    """
    runs_a: Set[datetime] = set(next_runs(expr_a, after=after, count=count))
    runs_b: Set[datetime] = set(next_runs(expr_b, after=after, count=count))

    return ScheduleDiff(
        only_in_a=sorted(runs_a - runs_b),
        only_in_b=sorted(runs_b - runs_a),
        common=sorted(runs_a & runs_b),
    )
