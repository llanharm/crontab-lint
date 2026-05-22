"""Next-run scheduler: compute the next N execution times for a cron expression."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from .parser import ParsedCron, parse
from .overlap_detector import _expand_field


class ScheduleError(Exception):
    """Raised when next-run computation fails."""


def _matches(dt: datetime, cron: ParsedCron) -> bool:
    """Return True if *dt* matches all five cron fields."""
    minute_vals = _expand_field(cron.minute, 0, 59)
    hour_vals = _expand_field(cron.hour, 0, 23)
    dom_vals = _expand_field(cron.day_of_month, 1, 31)
    month_vals = _expand_field(cron.month, 1, 12)
    dow_vals = _expand_field(cron.day_of_week, 0, 6)

    return (
        dt.minute in minute_vals
        and dt.hour in hour_vals
        and dt.day in dom_vals
        and dt.month in month_vals
        and dt.weekday() in {d % 7 for d in dow_vals}  # isoweekday: Mon=0
    )


def next_runs(
    expression: str,
    after: datetime | None = None,
    count: int = 5,
) -> List[datetime]:
    """Return the next *count* datetimes when *expression* will fire.

    Args:
        expression: A five-field cron expression (without a command).
        after: Start searching from this moment (default: now).
        count: Number of future run-times to return.

    Returns:
        Sorted list of naive :class:`datetime` objects.

    Raises:
        ScheduleError: If no match is found within one year.
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    # Allow a bare expression without a command by appending a dummy command.
    parts = expression.strip().split()
    if len(parts) == 5:
        expression = expression.strip() + " _dummy_"

    cron = parse(expression)

    start = (after or datetime.now()).replace(second=0, microsecond=0)
    current = start + timedelta(minutes=1)

    results: List[datetime] = []
    limit = start + timedelta(days=366)

    while current <= limit and len(results) < count:
        if _matches(current, cron):
            results.append(current)
        current += timedelta(minutes=1)

    if len(results) < count:
        raise ScheduleError(
            f"Could only find {len(results)} run(s) within one year for: {expression!r}"
        )

    return results
