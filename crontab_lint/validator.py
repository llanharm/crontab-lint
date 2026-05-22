"""Crontab field validator module.

Validates each field of a parsed crontab expression against
allowed ranges and syntax rules.
"""

from typing import List
from crontab_lint.parser import CronField, ParsedCron


class ValidationError(Exception):
    pass


@dataclass_like = None  # avoid re-import; use plain class


class LintResult:
    def __init__(self, expression: str):
        self.expression = expression
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:
        status = "OK" if self.is_valid else "INVALID"
        return f"LintResult({status}, errors={self.errors}, warnings={self.warnings})"


def _validate_value(value: str, field: CronField) -> List[str]:
    """Validate a single numeric or wildcard value within a field."""
    errors = []
    if value == "*" or value == "?":
        return errors
    try:
        num = int(value)
    except ValueError:
        errors.append(
            f"[{field.name}] Non-numeric value '{value}' could not be resolved."
        )
        return errors
    if not (field.min_val <= num <= field.max_val):
        errors.append(
            f"[{field.name}] Value {num} out of range "
            f"[{field.min_val}-{field.max_val}]."
        )
    return errors


def _validate_field(field: CronField) -> List[str]:
    """Validate an individual CronField for syntax and range errors."""
    errors = []
    raw = field.raw

    for list_part in raw.split(","):
        if "/" in list_part:
            base, step = list_part.split("/", 1)
            if not step.isdigit() or int(step) == 0:
                errors.append(
                    f"[{field.name}] Invalid step value '/{step}'."
                )
            else:
                step_int = int(step)
                range_size = field.max_val - field.min_val + 1
                if step_int > range_size:
                    errors.append(
                        f"[{field.name}] Step /{step_int} exceeds field range "
                        f"({range_size}); schedule will never repeat."
                    )
            list_part = base

        if "-" in list_part:
            bounds = list_part.split("-", 1)
            errors += _validate_value(bounds[0], field)
            errors += _validate_value(bounds[1], field)
            try:
                lo, hi = int(bounds[0]), int(bounds[1])
                if lo > hi:
                    errors.append(
                        f"[{field.name}] Range start {lo} is greater than end {hi}."
                    )
            except ValueError:
                pass
        else:
            errors += _validate_value(list_part, field)

    return errors


def validate(parsed: ParsedCron) -> LintResult:
    """Run all validation checks on a ParsedCron and return a LintResult."""
    result = LintResult(parsed.raw_expression)
    for field in parsed.fields:
        result.errors.extend(_validate_field(field))
    return result
