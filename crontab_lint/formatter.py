"""Output formatters for crontab-lint results."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crontab_lint.linter import FileLintReport


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


def format_text(report: "FileLintReport") -> str:
    """Render a FileLintReport as a human-readable text block."""
    lines: list[str] = []
    lines.append(f"File: {report.path}")
    lines.append(f"  Lines checked : {report.total_lines}")
    lines.append(f"  Valid entries : {report.valid_count}")
    lines.append(f"  Errors        : {len(report.errors)}")
    lines.append(f"  Overlaps      : {len(report.overlaps)}")

    if report.errors:
        lines.append("\nErrors:")
        for err in report.errors:
            lines.append(f"  [line {err.line_number}] {err.message}")
            if err.expression:
                lines.append(f"    Expression: {err.expression}")

    if report.overlaps:
        lines.append("\nOverlapping schedules:")
        for ov in report.overlaps:
            lines.append(
                f"  Lines {ov.line_a} & {ov.line_b}: "
                f"{ov.overlap_count} overlapping minute(s) per week"
            )

    lines.append("")
    lines.append(report.summary())
    return "\n".join(lines)


def format_json(report: "FileLintReport") -> str:
    """Render a FileLintReport as a JSON string."""
    import json

    data = {
        "path": str(report.path),
        "total_lines": report.total_lines,
        "valid_count": report.valid_count,
        "errors": [
            {
                "line": e.line_number,
                "message": e.message,
                "expression": e.expression,
            }
            for e in report.errors
        ],
        "overlaps": [
            {
                "line_a": o.line_a,
                "line_b": o.line_b,
                "overlap_minutes_per_week": o.overlap_count,
            }
            for o in report.overlaps
        ],
        "status": "ok" if not report.has_errors() and not report.has_overlaps() else "fail",
    }
    return json.dumps(data, indent=2)


def render(report: "FileLintReport", fmt: OutputFormat = OutputFormat.TEXT) -> str:
    """Dispatch to the correct formatter."""
    if fmt == OutputFormat.JSON:
        return format_json(report)
    return format_text(report)
