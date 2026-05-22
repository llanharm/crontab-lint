"""Tests for crontab_lint.summarizer."""
from __future__ import annotations

import pytest

from crontab_lint.linter import FileLintReport
from crontab_lint.validator import LintResult
from crontab_lint.overlap_detector import OverlapResult
from crontab_lint.summarizer import summarize, CrontabSummary


def _make_report(
    lines: list[str],
    overlaps: list[OverlapResult] | None = None,
    path: str = "/etc/cron.d/test",
) -> FileLintReport:
    from crontab_lint.linter import lint_file
    import tempfile, os

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".crontab", delete=False
    ) as fh:
        fh.write("\n".join(lines) + "\n")
        tmp = fh.name
    try:
        return lint_file(tmp)
    finally:
        os.unlink(tmp)


class TestSummarizer:
    def test_empty_file(self):
        report = _make_report([])
        summary = summarize(report)
        assert summary.total_entries == 0
        assert summary.valid_entries == 0
        assert summary.invalid_entries == 0
        assert summary.health_score == 1.0

    def test_all_valid(self):
        report = _make_report(
            [
                "* * * * * echo hello",
                "0 9 * * 1 echo weekly",
            ]
        )
        summary = summarize(report)
        assert summary.total_entries == 2
        assert summary.valid_entries == 2
        assert summary.invalid_entries == 0
        assert summary.health_score == 1.0

    def test_invalid_entry_lowers_score(self):
        report = _make_report(
            [
                "* * * * * echo hello",
                "NOT_A_CRON_LINE",
            ]
        )
        summary = summarize(report)
        assert summary.invalid_entries >= 1
        assert summary.health_score < 1.0

    def test_descriptions_populated_for_valid(self):
        report = _make_report(["0 12 * * * echo noon"])
        summary = summarize(report)
        assert len(summary.descriptions) == 1
        assert isinstance(summary.descriptions[0], str)
        assert len(summary.descriptions[0]) > 0

    def test_explanations_populated_for_valid(self):
        report = _make_report(["30 6 * * * echo morning"])
        summary = summarize(report)
        assert len(summary.explanations) == 1
        assert "6" in summary.explanations[0] or "30" in summary.explanations[0]

    def test_short_report_contains_file_path(self):
        report = _make_report(["* * * * * echo hi"])
        summary = summarize(report)
        text = summary.short_report()
        assert summary.file_path in text
        assert "Health score" in text

    def test_health_score_bounds(self):
        report = _make_report(
            ["INVALID1", "INVALID2", "INVALID3"]
        )
        summary = summarize(report)
        assert 0.0 <= summary.health_score <= 1.0
