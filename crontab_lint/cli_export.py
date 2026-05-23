"""CLI sub-command: export lint results to CSV or Markdown."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_lint.exporter import ExportFormat, export
from crontab_lint.linter import lint_file


def build_export_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *export* sub-command on *parent*."""
    p = parent.add_parser(
        "export",
        help="Export lint results to CSV or Markdown.",
        description="Lint a crontab file and write results in a structured format.",
    )
    p.add_argument("file", help="Path to the crontab file to lint.")
    p.add_argument(
        "--format",
        "-f",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.CSV.value,
        dest="fmt",
        help="Output format (default: csv).",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    return p


def run_export(args: argparse.Namespace) -> int:
    """Execute the export sub-command; returns an exit code."""
    path = args.file
    if not Path(path).exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    fmt = ExportFormat(args.fmt)
    report = lint_file(path)
    result = export(report, fmt)

    if args.output:
        Path(args.output).write_text(result.content, encoding="utf-8")
        print(f"Exported {fmt.value} to {args.output}")
    else:
        sys.stdout.write(result.content)

    return 1 if report.has_errors else 0
