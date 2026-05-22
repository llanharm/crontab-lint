"""Summarizes a crontab file into human-readable statistics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .linter import FileLintReport
from .humanizer import describe_schedule
from .explainer import explain


@dataclass
class CrontabSummary:
    """Aggregated statistics and descriptions for a crontab file."""

    file_path: str
    total_entries: int
    valid_entries: int
    invalid_entries: int
    overlap_count: int
    descriptions: List[str] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)

    @property
    def health_score(self) -> float:
        """0.0–1.0 score: 1.0 means no errors and no overlaps."""
        if self.total_entries == 0:
            return 1.0
        penalty = (self.invalid_entries + self.overlap_count) / (
            self.total_entries + self.overlap_count
        )
        return round(max(0.0, 1.0 - penalty), 4)

    def short_report(self) -> str:
        lines = [
            f"File : {self.file_path}",
            f"Entries : {self.total_entries} total, "
            f"{self.valid_entries} valid, {self.invalid_entries} invalid",
            f"Overlaps : {self.overlap_count}",
            f"Health score: {self.health_score:.0%}",
        ]
        return "\n".join(lines)


def summarize(report: FileLintReport) -> CrontabSummary:
    """Build a :class:`CrontabSummary` from a :class:`FileLintReport`."""
    total = len(report.results)
    invalid = sum(1 for r in report.results if not r.is_valid)
    valid = total - invalid
    overlap_count = len(report.overlaps)

    descriptions: list[str] = []
    explanations: list[str] = []
    for r in report.results:
        if r.is_valid and r.parsed is not None:
            try:
                descriptions.append(describe_schedule(r.parsed))
            except Exception:
                descriptions.append("(unable to describe)")
            try:
                explanations.append(explain(r.parsed))
            except Exception:
                explanations.append("(unable to explain)")

    return CrontabSummary(
        file_path=report.file_path,
        total_entries=total,
        valid_entries=valid,
        invalid_entries=invalid,
        overlap_count=overlap_count,
        descriptions=descriptions,
        explanations=explanations,
    )
