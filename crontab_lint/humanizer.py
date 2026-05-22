"""Human-readable summaries of next scheduled runs."""

from __future__ import annotations

from datetime import datetime
from typing import List

from .scheduler import next_runs

_FMT = "%Y-%m-%d %H:%M"


def humanize_next_runs(
    expression: str,
    after: datetime | None = None,
    count: int = 5,
) -> List[str]:
    """Return a list of formatted strings for the next *count* run times.

    Example::

        >>> humanize_next_runs("0 9 * * 1-5")
        ['2024-01-15 09:00', '2024-01-16 09:00', ...]
    """
    runs = next_runs(expression, after=after, count=count)
    return [dt.strftime(_FMT) for dt in runs]


def describe_schedule(expression: str, count: int = 3) -> str:
    """Return a one-paragraph description including next run times.

    Args:
        expression: Five-field cron expression (no command).
        count: How many upcoming runs to include.

    Returns:
        A human-friendly string.
    """
    from .explainer import explain  # local import to avoid circular deps

    parts = expression.strip().split()
    if len(parts) == 5:
        full_expr = expression.strip() + " _"
    else:
        full_expr = expression

    human = explain(full_expr)
    try:
        upcoming = humanize_next_runs(expression, count=count)
        runs_str = ", ".join(upcoming)
        return f"{human}\nNext {count} run(s): {runs_str}"
    except Exception as exc:  # pragma: no cover
        return f"{human}\n(Could not compute next runs: {exc})"
