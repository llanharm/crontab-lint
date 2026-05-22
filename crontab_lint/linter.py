"""High-level linting API combining validation and overlap detection."""

from dataclasses import dataclass, field
from typing import List

from .parser import parse, ParseError
from .validator import LintResult, validate
from .overlap_detector import OverlapResult, detect_overlaps


@dataclass
class FileLintReport:
    filename: str
    parse_errors: List[str] = field(default_factory=list)
    lint_results: List[LintResult] = field(default_factory=list)
    overlaps: List[OverlapResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.parse_errors) or any(
            not r.is_valid for r in self.lint_results
        )

    @property
    def has_overlaps(self) -> bool:
        return bool(self.overlaps)

    def summary(self) -> str:
        lines = [f"=== {self.filename} ==="]
        if not self.parse_errors and not self.lint_results and not self.overlaps:
            lines.append("  No issues found.")
            return "\n".join(lines)
        for err in self.parse_errors:
            lines.append(f"  [PARSE ERROR] {err}")
        for result in self.lint_results:
            if not result.is_valid:
                for warn in result.warnings:
                    lines.append(f"  [WARN] {warn}")
                for err in result.errors:
                    lines.append(f"  [ERROR] {err}")
        for overlap in self.overlaps:
            lines.append(
                f"  [OVERLAP] Schedules overlap ({overlap.overlap_minutes} slots): "
                f"{overlap.entry_a!r} <-> {overlap.entry_b!r}"
            )
            if overlap.sample_times:
                lines.append(f"    Sample times: {', '.join(overlap.sample_times)}")
        return "\n".join(lines)


def lint_file(filename: str) -> FileLintReport:
    """Read a crontab file and produce a full lint report."""
    report = FileLintReport(filename=filename)
    try:
        with open(filename, "r") as fh:
            raw_lines = fh.readlines()
    except OSError as exc:
        report.parse_errors.append(str(exc))
        return report

    entries = []
    for lineno, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            cron = parse(stripped)
            result = validate(cron)
            report.lint_results.append(result)
            entries.append(stripped)
        except ParseError as exc:
            report.parse_errors.append(f"Line {lineno}: {exc}")

    report.overlaps = detect_overlaps(entries)
    return report


def lint_lines(lines: List[str], source: str = "<input>") -> FileLintReport:
    """Lint a list of crontab line strings directly."""
    report = FileLintReport(filename=source)
    entries = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            cron = parse(stripped)
            result = validate(cron)
            report.lint_results.append(result)
            entries.append(stripped)
        except ParseError as exc:
            report.parse_errors.append(f"Line {lineno}: {exc}")
    report.overlaps = detect_overlaps(entries)
    return report
