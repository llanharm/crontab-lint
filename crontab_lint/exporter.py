"""Export crontab lint results to various formats (CSV, Markdown)."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from enum import Enum
from typing import List

from crontab_lint.linter import FileLintReport


class ExportFormat(str, Enum):
    CSV = "csv"
    MARKDOWN = "markdown"


@dataclass
class ExportResult:
    format: ExportFormat
    content: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"ExportResult(format={self.format}, lines={len(self.content.splitlines())})"


def _report_rows(report: FileLintReport) -> List[dict]:
    """Flatten a FileLintReport into a list of row dicts."""
    rows: List[dict] = []
    for result in report.results:
        base = {
            "file": report.path,
            "line": result.line_number,
            "expression": result.raw_line,
            "valid": result.lint.is_valid,
            "errors": "; ".join(e.message for e in result.lint.errors),
        }
        rows.append(base)
    return rows


def export_csv(report: FileLintReport) -> ExportResult:
    """Serialise *report* as CSV text."""
    fieldnames = ["file", "line", "expression", "valid", "errors"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in _report_rows(report):
        writer.writerow(row)
    return ExportResult(format=ExportFormat.CSV, content=buf.getvalue())


def export_markdown(report: FileLintReport) -> ExportResult:
    """Serialise *report* as a Markdown table."""
    lines: List[str] = [
        f"## {report.path}",
        "",
        "| Line | Expression | Valid | Errors |",
        "|------|------------|-------|--------|" ,
    ]
    for row in _report_rows(report):
        valid_mark = "✅" if row["valid"] else "❌"
        errors = row["errors"] or "—"
        expr = row["expression"].replace("|", "\\|")
        lines.append(f"| {row['line']} | `{expr}` | {valid_mark} | {errors} |")
    lines.append("")
    return ExportResult(format=ExportFormat.MARKDOWN, content="\n".join(lines))


def export(report: FileLintReport, fmt: ExportFormat) -> ExportResult:
    """Dispatch to the correct exporter based on *fmt*."""
    if fmt == ExportFormat.CSV:
        return export_csv(report)
    if fmt == ExportFormat.MARKDOWN:
        return export_markdown(report)
    raise ValueError(f"Unsupported export format: {fmt}")
