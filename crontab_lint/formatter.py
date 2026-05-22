"""Output formatters for lint reports."""

import json
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .linter import FileLintReport

try:
    from .explainer import explain
    _EXPLAINER_AVAILABLE = True
except ImportError:
    _EXPLAINER_AVAILABLE = False


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


def format_text(report: "FileLintReport", *, show_explanation: bool = False) -> str:
    lines = [f"File: {report.path}"]

    if not report.results:
        lines.append("  (no cron entries found)")
        return "\n".join(lines)

    for r in report.results:
        status = "OK" if r.is_valid else "ERROR"
        lines.append(f"  [{status}] Line {r.line_number}: {r.raw_line}")
        if show_explanation and _EXPLAINER_AVAILABLE and r.parsed:
            try:
                lines.append(f"         Explanation: {explain(r.parsed)}")
            except Exception:
                pass
        for err in r.errors:
            lines.append(f"         Error: {err.message} (field: {err.field})")

    if report.overlaps:
        lines.append("  Overlaps detected:")
        for ov in report.overlaps:
            lines.append(
                f"    Lines {ov.line_a} and {ov.line_b} share "
                f"{ov.shared_minutes} overlapping minute(s) per week."
            )

    lines.append(report.summary())
    return "\n".join(lines)


def format_json(report: "FileLintReport", *, show_explanation: bool = False) -> str:
    entries = []
    for r in report.results:
        entry = {
            "line": r.line_number,
            "raw": r.raw_line,
            "valid": r.is_valid,
            "errors": [{"field": e.field, "message": e.message} for e in r.errors],
        }
        if show_explanation and _EXPLAINER_AVAILABLE and r.parsed:
            try:
                entry["explanation"] = explain(r.parsed)
            except Exception:
                pass
        entries.append(entry)

    overlaps = [
        {"line_a": ov.line_a, "line_b": ov.line_b, "shared_minutes": ov.shared_minutes}
        for ov in report.overlaps
    ]

    payload = {
        "file": str(report.path),
        "entries": entries,
        "overlaps": overlaps,
        "summary": report.summary(),
    }
    return json.dumps(payload, indent=2)


def render(
    report: "FileLintReport",
    fmt: OutputFormat = OutputFormat.TEXT,
    *,
    show_explanation: bool = False,
) -> str:
    if fmt == OutputFormat.JSON:
        return format_json(report, show_explanation=show_explanation)
    return format_text(report, show_explanation=show_explanation)
