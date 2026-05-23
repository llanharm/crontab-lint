"""Suggests fixes and improvements for invalid or suspicious cron expressions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import ParsedCron, ParseError, parse
from .validator import LintResult


@dataclass
class Suggestion:
    code: str
    message: str
    fix: str | None = None

    def __repr__(self) -> str:  # pragma: no cover
        fix_part = f", fix={self.fix!r}" if self.fix else ""
        return f"Suggestion(code={self.code!r}, message={self.message!r}{fix_part})"


@dataclass
class RecommendationReport:
    raw: str
    suggestions: List[Suggestion] = field(default_factory=list)

    @property
    def has_suggestions(self) -> bool:
        return bool(self.suggestions)

    def summary(self) -> str:
        if not self.suggestions:
            return "No suggestions."
        lines = [f"  [{s.code}] {s.message}" + (f" => {s.fix}" if s.fix else "") for s in self.suggestions]
        return "\n".join(lines)


def _check_every_minute(parsed: ParsedCron, report: RecommendationReport) -> None:
    """Warn when a job runs every minute (often unintentional)."""
    if all(f.raw == "*" for f in (parsed.minute, parsed.hour, parsed.dom, parsed.month, parsed.dow)):
        report.suggestions.append(
            Suggestion(
                code="W001",
                message="Expression runs every minute — is that intentional?",
                fix="Consider '0 * * * * <cmd>' to run once per hour instead.",
            )
        )


def _check_dom_and_dow_both_restricted(parsed: ParsedCron, report: RecommendationReport) -> None:
    """Warn when both DOM and DOW are non-wildcard (ambiguous OR semantics)."""
    if parsed.dom.raw != "*" and parsed.dow.raw != "*":
        report.suggestions.append(
            Suggestion(
                code="W002",
                message="Both day-of-month and day-of-week are restricted; cron uses OR semantics which may be surprising.",
                fix="Set one of them to '*' to avoid unintended schedules.",
            )
        )


def _check_high_frequency(parsed: ParsedCron, report: RecommendationReport) -> None:
    """Warn about step values that produce very high frequency runs."""
    minute_raw = parsed.minute.raw
    if minute_raw.startswith("*/"):
        try:
            step = int(minute_raw[2:])
            if step < 5:
                report.suggestions.append(
                    Suggestion(
                        code="W003",
                        message=f"Minute step '*/{step}' runs very frequently ({60 // step}x/hour).",
                        fix="Consider '*/5' or higher to reduce load.",
                    )
                )
        except ValueError:
            pass


def recommend(raw: str, lint_result: LintResult | None = None) -> RecommendationReport:
    """Return a RecommendationReport with suggestions for *raw* cron entry."""
    report = RecommendationReport(raw=raw)

    if lint_result is not None and not lint_result.is_valid:
        for err in lint_result.errors:
            report.suggestions.append(Suggestion(code="E001", message=f"Validation error: {err}"))
        return report

    try:
        parsed = parse(raw)
    except ParseError as exc:
        report.suggestions.append(Suggestion(code="E000", message=f"Parse error: {exc}"))
        return report

    _check_every_minute(parsed, report)
    _check_dom_and_dow_both_restricted(parsed, report)
    _check_high_frequency(parsed, report)
    return report
