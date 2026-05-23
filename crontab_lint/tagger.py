"""Tag crontab entries with human-readable category labels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import ParsedCron, parse, ParseError


_FREQUENT_MINUTES_THRESHOLD = 15  # runs more often than every N minutes


@dataclass
class TaggedEntry:
    raw: str
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedEntry(raw={self.raw!r}, tags={self.tags})"


def _is_wildcard(token: str) -> bool:
    return token == "*"


def _step_value(token: str) -> int | None:
    """Return the step integer if token is */N, else None."""
    if token.startswith("*/"):
        try:
            return int(token[2:])
        except ValueError:
            return None
    return None


def _tag_cron(parsed: ParsedCron) -> List[str]:
    tags: List[str] = []
    minute = parsed.minute
    hour = parsed.hour
    dom = parsed.day_of_month
    month = parsed.month
    dow = parsed.day_of_week

    # Frequency tags
    if _is_wildcard(minute):
        tags.append("frequent")
    else:
        step = _step_value(minute)
        if step is not None and step <= _FREQUENT_MINUTES_THRESHOLD:
            tags.append("frequent")

    if _is_wildcard(minute) and _is_wildcard(hour):
        tags.append("every-minute")
    elif _is_wildcard(hour):
        tags.append("sub-hourly")
    elif _is_wildcard(dom) and _is_wildcard(month) and _is_wildcard(dow):
        tags.append("daily")
    elif not _is_wildcard(dow):
        tags.append("weekly")
    elif not _is_wildcard(dom) or not _is_wildcard(month):
        tags.append("monthly")

    # Midnight tag
    if minute == "0" and hour == "0":
        tags.append("midnight")

    # Business-hours tag: weekdays (1-5) during 8-18
    if dow in ("1-5", "MON-FRI", "mon-fri"):
        tags.append("business-hours")

    return sorted(set(tags))


def tag(expression: str) -> TaggedEntry:
    """Return a TaggedEntry for *expression* (schedule + command string)."""
    try:
        parsed = parse(expression)
    except ParseError:
        return TaggedEntry(raw=expression, tags=["invalid"])
    return TaggedEntry(raw=expression, tags=_tag_cron(parsed))
