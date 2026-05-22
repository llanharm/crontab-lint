"""Command-line interface for crontab-lint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_lint.formatter import OutputFormat, render
from crontab_lint.linter import lint_file


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crontab-lint",
        description="Static analyzer and validator for crontab expressions.",
    )
    p.add_argument(
        "files",
        metavar="FILE",
        nargs="+",
        type=Path,
        help="Crontab file(s) to lint.",
    )
    p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--no-overlaps",
        action="store_true",
        help="Skip overlap detection.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    fmt = OutputFormat(args.fmt)

    exit_code = 0
    for path in args.files:
        if not path.exists():
            print(f"crontab-lint: {path}: file not found", file=sys.stderr)
            exit_code = 2
            continue

        report = lint_file(path, detect_overlaps=not args.no_overlaps)
        print(render(report, fmt))

        if report.has_errors() or report.has_overlaps():
            exit_code = 1

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
