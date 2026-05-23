"""Compare two crontab expressions and report structural differences."""

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import parse, ParseError
from .normalizer import normalize


@dataclass
class FieldDiff:
    """Difference in a single cron field."""
    field_name: str
    value_a: str
    value_b: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"FieldDiff({self.field_name}: {self.value_a!r} -> {self.value_b!r})"


@dataclass
class CompareResult:
    """Result of comparing two crontab expressions."""
    expr_a: str
    expr_b: str
    field_diffs: List[FieldDiff] = field(default_factory=list)
    command_changed: bool = False
    error: Optional[str] = None

    @property
    def is_equivalent(self) -> bool:
        """True when both expressions are semantically identical after normalisation."""
        if self.error:
            return False
        return not self.field_diffs and not self.command_changed

    def summary(self) -> str:
        if self.error:
            return f"Error: {self.error}"
        if self.is_equivalent:
            return "Expressions are equivalent."
        parts: List[str] = []
        for d in self.field_diffs:
            parts.append(f"  {d.field_name}: {d.value_a!r} -> {d.value_b!r}")
        if self.command_changed:
            parts.append("  command differs")
        return "Differences found:\n" + "\n".join(parts)


_FIELD_NAMES = ["minute", "hour", "day_of_month", "month", "day_of_week"]


def compare(expr_a: str, expr_b: str) -> CompareResult:
    """Compare two crontab lines and return a :class:`CompareResult`."""
    try:
        norm_a = normalize(expr_a)
        norm_b = normalize(expr_b)
    except Exception as exc:  # noqa: BLE001
        return CompareResult(expr_a=expr_a, expr_b=expr_b, error=str(exc))

    try:
        parsed_a = parse(norm_a.normalized_expression + " " + (norm_a.command or ""))
        parsed_b = parse(norm_b.normalized_expression + " " + (norm_b.command or ""))
    except ParseError as exc:
        return CompareResult(expr_a=expr_a, expr_b=expr_b, error=str(exc))

    fields_a = [
        parsed_a.minute, parsed_a.hour,
        parsed_a.day_of_month, parsed_a.month, parsed_a.day_of_week,
    ]
    fields_b = [
        parsed_b.minute, parsed_b.hour,
        parsed_b.day_of_month, parsed_b.month, parsed_b.day_of_week,
    ]

    diffs: List[FieldDiff] = []
    for name, fa, fb in zip(_FIELD_NAMES, fields_a, fields_b):
        if fa != fb:
            diffs.append(FieldDiff(field_name=name, value_a=fa, value_b=fb))

    command_changed = (norm_a.command or "").strip() != (norm_b.command or "").strip()

    return CompareResult(
        expr_a=expr_a,
        expr_b=expr_b,
        field_diffs=diffs,
        command_changed=command_changed,
    )
