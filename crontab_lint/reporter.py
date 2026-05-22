"""Generates a consolidated multi-file report for a set of crontab files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .linter import FileLintReport, lint_file
from .summarizer import CrontabSummary, summarize


@dataclass
class MultiFileReport:
    """Holds per-file summaries and aggregated totals."""

    summaries: List[CrontabSummary] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.summaries)

    @property
    def files_with_errors(self) -> int:
        return sum(1 for s in self.summaries if s.invalid_entries > 0)

    @property
    def files_with_overlaps(self) -> int:
        return sum(1 for s in self.summaries if s.overlap_count > 0)

    @property
    def overall_health(self) -> float:
        if not self.summaries:
            return 1.0
        return round(
            sum(s.health_score for s in self.summaries) / len(self.summaries), 4
        )

    def text_report(self) -> str:
        sections: list[str] = [
            "=== Crontab Lint — Multi-File Report ===",
            f"Files scanned : {self.total_files}",
            f"Files with errors : {self.files_with_errors}",
            f"Files with overlaps: {self.files_with_overlaps}",
            f"Overall health : {self.overall_health:.0%}",
            "",
        ]
        for s in self.summaries:
            sections.append(s.short_report())
            sections.append("")
        return "\n".join(sections).rstrip()


def report_files(paths: list[str]) -> MultiFileReport:
    """Lint *paths* and return a :class:`MultiFileReport`."""
    multi = MultiFileReport()
    for path in paths:
        try:
            file_report: FileLintReport = lint_file(path)
        except OSError as exc:
            # Create a minimal summary for unreadable files.
            multi.summaries.append(
                CrontabSummary(
                    file_path=path,
                    total_entries=0,
                    valid_entries=0,
                    invalid_entries=1,
                    overlap_count=0,
                    descriptions=[],
                    explanations=[],
                )
            )
            continue
        multi.summaries.append(summarize(file_report))
    return multi
