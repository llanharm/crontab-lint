"""Normalize crontab expressions to a canonical form."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .parser import ParsedCron, parse, ParseError

# Aliases for months and weekdays to their numeric equivalents
_MONTH_NAMES = {
    "jan": "1", "feb": "2", "mar": "3", "apr": "4",
    "may": "5", "jun": "6", "jul": "7", "aug": "8",
    "sep": "9", "oct": "10", "nov": "11", "dec": "12",
}

_DOW_NAMES = {
    "sun": "0", "mon": "1", "tue": "2", "wed": "3",
    "thu": "4", "fri": "5", "sat": "6",
}

# Common shorthand macros
_MACROS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


@dataclass
class NormalizedCron:
    original: str
    normalized: str
    command: str
    was_macro: bool

    def __repr__(self) -> str:  # pragma: no cover
        return f"NormalizedCron(original={self.original!r}, normalized={self.normalized!r})"


def _normalize_token(token: str, alias_map: dict) -> str:
    """Replace named aliases in a single cron field token."""
    parts = token.split(",")
    result: List[str] = []
    for part in parts:
        lower = part.lower()
        for name, num in alias_map.items():
            lower = lower.replace(name, num)
        result.append(lower)
    return ",".join(result)


def _normalize_field(field: str, alias_map: dict) -> str:
    """Normalize a cron field, handling step and range syntax."""
    if "/" in field:
        base, step = field.split("/", 1)
        return f"{_normalize_token(base, alias_map)}/{step}"
    return _normalize_token(field, alias_map)


def normalize(expression: str) -> NormalizedCron:
    """Normalize a full crontab line to a canonical form.

    Expands macros like @daily and replaces month/weekday names
    with their numeric equivalents.

    Raises ParseError if the expression cannot be parsed.
    """
    stripped = expression.strip()
    parts = stripped.split(None, 1)
    first = parts[0].lower() if parts else ""

    if first in _MACROS:
        schedule = _MACROS[first]
        command = parts[1] if len(parts) > 1 else ""
        full_normalized = f"{schedule} {command}".strip()
        return NormalizedCron(
            original=stripped,
            normalized=full_normalized,
            command=command,
            was_macro=True,
        )

    # Validate via parser first
    parsed: ParsedCron = parse(stripped)

    fields = [
        parsed.minute,
        parsed.hour,
        parsed.day_of_month,
        _normalize_field(parsed.month, _MONTH_NAMES),
        _normalize_field(parsed.day_of_week, _DOW_NAMES),
    ]
    normalized_schedule = " ".join(fields)
    full_normalized = f"{normalized_schedule} {parsed.command}".strip()

    return NormalizedCron(
        original=stripped,
        normalized=full_normalized,
        command=parsed.command,
        was_macro=False,
    )
