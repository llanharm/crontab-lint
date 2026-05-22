"""Human-readable explanation of cron expressions."""

from typing import List
from .parser import ParsedCron, CronField

_WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
_MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _explain_field(field: CronField, unit: str, names: List[str] = None) -> str:
    """Return a human-readable description of a single cron field."""
    raw = field.raw

    if raw == "*":
        return f"every {unit}"

    if raw.startswith("*/"):
        step = raw[2:]
        return f"every {step} {unit}s"

    if "-" in raw and "/" in raw:
        base, step = raw.split("/")
        start, end = base.split("-")
        s = names[int(start)] if names else start
        e = names[int(end)] if names else end
        return f"every {step} {unit}s from {s} through {e}"

    if "-" in raw:
        start, end = raw.split("-")
        s = names[int(start)] if names else start
        e = names[int(end)] if names else end
        return f"{unit}s {s} through {e}"

    if "," in raw:
        parts = raw.split(",")
        labels = [names[int(p)] if names else p for p in parts]
        return f"{unit}s " + ", ".join(labels[:-1]) + f" and {labels[-1]}"

    label = names[int(raw)] if names else raw
    return f"{unit} {label}"


def explain(cron: ParsedCron) -> str:
    """Return a full human-readable explanation of a parsed cron expression."""
    minute = _explain_field(cron.minute, "minute")
    hour = _explain_field(cron.hour, "hour")
    dom = _explain_field(cron.day_of_month, "day-of-month")
    month = _explain_field(cron.month, "month", _MONTHS)
    dow = _explain_field(cron.day_of_week, "weekday", _WEEKDAYS)

    parts: List[str] = []

    if cron.minute.raw == "*" and cron.hour.raw == "*":
        parts.append("every minute")
    elif cron.minute.raw == "*":
        parts.append(f"every minute of {hour}")
    else:
        parts.append(f"at {minute} past {hour}")

    if cron.day_of_month.raw != "*" and cron.day_of_week.raw != "*":
        parts.append(f"on {dom} and on {dow}")
    elif cron.day_of_month.raw != "*":
        parts.append(f"on {dom}")
    elif cron.day_of_week.raw != "*":
        parts.append(f"on {dow}")

    if cron.month.raw != "*":
        parts.append(f"in {month}")

    return ", ".join(parts) + "."
