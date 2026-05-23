"""Validates parsed cron expressions and collects lint errors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import ParsedCron, ParseError, parse


class ValidationError(Exception):
    """Raised when a cron expression is structurally invalid."""


@dataclass
class LintResult:
    raw: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:
        return (
            f"LintResult(is_valid={self.is_valid}, "
            f"errors={self.errors!r}, warnings={self.warnings!r})"
        )


_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "dom": (1, 31),
    "month": (1, 12),
    "dow": (0, 7),
}


def _validate_value(value: int, lo: int, hi: int) -> bool:
    return lo <= value <= hi


def _validate_token(token: str, field_name: str, lo: int, hi: int, errors: List[str]) -> None:
    """Validate a single token (value, range, or step) against allowed bounds."""
    if token == "*":
        return
    if "/" in token:
        parts = token.split("/", 1)
        base, step_str = parts
        try:
            step = int(step_str)
        except ValueError:
            errors.append(f"{field_name}: invalid step value '{step_str}'")
            return
        if step < 1:
            errors.append(f"{field_name}: step must be >= 1, got {step}")
        if base != "*":
            _validate_token(base, field_name, lo, hi, errors)
        return
    if "-" in token:
        parts = token.split("-", 1)
        try:
            a, b = int(parts[0]), int(parts[1])
        except ValueError:
            errors.append(f"{field_name}: invalid range '{token}'")
            return
        if not _validate_value(a, lo, hi):
            errors.append(f"{field_name}: range start {a} out of [{lo},{hi}]")
        if not _validate_value(b, lo, hi):
            errors.append(f"{field_name}: range end {b} out of [{lo},{hi}]")
        if a > b:
            errors.append(f"{field_name}: range start {a} > end {b}")
        return
    try:
        v = int(token)
    except ValueError:
        errors.append(f"{field_name}: unrecognised token '{token}'")
        return
    if not _validate_value(v, lo, hi):
        errors.append(f"{field_name}: value {v} out of [{lo},{hi}]")


def _validate_field(raw: str, field_name: str, lo: int, hi: int, errors: List[str]) -> None:
    for token in raw.split(","):
        _validate_token(token.strip(), field_name, lo, hi, errors)


def validate(raw: str) -> LintResult:
    """Parse and validate *raw* cron entry, returning a LintResult."""
    result = LintResult(raw=raw)
    try:
        parsed: ParsedCron = parse(raw)
    except ParseError as exc:
        result.errors.append(str(exc))
        return result

    fields = [
        (parsed.minute, "minute"),
        (parsed.hour, "hour"),
        (parsed.dom, "dom"),
        (parsed.month, "month"),
        (parsed.dow, "dow"),
    ]
    for cron_field, name in fields:
        lo, hi = _FIELD_RANGES[name]
        _validate_field(cron_field.raw, name, lo, hi, result.errors)

    return result
