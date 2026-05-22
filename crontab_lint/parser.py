"""Crontab expression parser module.

Parses a crontab expression string into its component fields
and validates basic structural correctness.
"""

from dataclasses import dataclass
from typing import List, Optional

CRON_FIELDS = ["minute", "hour", "day_of_month", "month", "day_of_week"]

FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7),
}

MONTH_ALIASES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

WEEKDAY_ALIASES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3,
    "thu": 4, "fri": 5, "sat": 6,
}


@dataclass
class CronField:
    name: str
    raw: str
    min_val: int
    max_val: int


@dataclass
class ParsedCron:
    raw_expression: str
    fields: List[CronField]
    command: Optional[str] = None


class ParseError(ValueError):
    pass


def _resolve_aliases(value: str, field_name: str) -> str:
    """Replace named aliases with their numeric equivalents."""
    aliases = {}
    if field_name == "month":
        aliases = MONTH_ALIASES
    elif field_name == "day_of_week":
        aliases = WEEKDAY_ALIASES
    for alias, num in aliases.items():
        value = value.lower().replace(alias, str(num))
    return value


def parse(expression: str) -> ParsedCron:
    """Parse a crontab expression into a ParsedCron object.

    Args:
        expression: A standard 5-field cron expression, optionally
                    followed by a command.

    Returns:
        A ParsedCron instance with resolved fields.

    Raises:
        ParseError: If the expression does not have exactly 5 cron fields.
    """
    parts = expression.strip().split()
    if len(parts) < 5:
        raise ParseError(
            f"Expected at least 5 fields, got {len(parts)}: '{expression}'"
        )

    cron_parts = parts[:5]
    command = " ".join(parts[5:]) if len(parts) > 5 else None

    fields = []
    for raw, name in zip(cron_parts, CRON_FIELDS):
        min_val, max_val = FIELD_RANGES[name]
        resolved = _resolve_aliases(raw, name)
        fields.append(CronField(name=name, raw=resolved, min_val=min_val, max_val=max_val))

    return ParsedCron(raw_expression=expression, fields=fields, command=command)
