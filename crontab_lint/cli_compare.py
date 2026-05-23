"""CLI sub-command: compare two crontab expressions."""

import argparse
import sys
from typing import List, Optional

from .comparator import compare


def build_compare_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *compare* sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "compare",
        help="Compare two crontab expressions and show field-level differences.",
    )
    parser.add_argument("expr_a", help="First crontab expression (quoted)")
    parser.add_argument("expr_b", help="Second crontab expression (quoted)")
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress output; exit 0 if equivalent, 1 if different.",
    )
    return parser


def run_compare(args: argparse.Namespace) -> int:
    """Execute the compare sub-command.  Returns an exit code."""
    result = compare(args.expr_a, args.expr_b)

    if result.error:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(result.summary())

    return 0 if result.is_equivalent else 1


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover
    """Standalone entry-point for the compare sub-command."""
    root = argparse.ArgumentParser(prog="crontab-compare")
    subs = root.add_subparsers(dest="command")
    build_compare_parser(subs)
    args = root.parse_args(argv)
    if args.command is None:
        root.print_help()
        return 0
    return run_compare(args)
