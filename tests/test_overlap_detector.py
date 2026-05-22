"""Tests for overlap detection and high-level linting API."""

import pytest
from crontab_lint.overlap_detector import detect_overlaps, _expand_field
from crontab_lint.linter import lint_lines


class TestExpandField:
    def test_wildcard(self):
        assert _expand_field("*", 0, 4) == {0, 1, 2, 3, 4}

    def test_single_value(self):
        assert _expand_field("5", 0, 59) == {5}

    def test_range(self):
        assert _expand_field("1-3", 0, 59) == {1, 2, 3}

    def test_step(self):
        assert _expand_field("*/15", 0, 59) == {0, 15, 30, 45}

    def test_list(self):
        assert _expand_field("1,3,5", 0, 59) == {1, 3, 5}


class TestDetectOverlaps:
    def test_no_overlap(self):
        entries = [
            "0 6 * * * /bin/morning",
            "0 18 * * * /bin/evening",
        ]
        result = detect_overlaps(entries)
        assert result == []

    def test_identical_schedules_overlap(self):
        entries = [
            "*/5 * * * * /bin/job_a",
            "*/5 * * * * /bin/job_b",
        ]
        result = detect_overlaps(entries)
        assert len(result) == 1
        assert result[0].overlap_minutes > 0

    def test_partial_overlap(self):
        entries = [
            "0 * * * * /bin/hourly",
            "0 6 * * * /bin/at_six",
        ]
        result = detect_overlaps(entries)
        assert len(result) == 1
        assert result[0].overlap_minutes > 0

    def test_comments_and_blanks_ignored(self):
        entries = [
            "# this is a comment",
            "",
            "0 1 * * * /bin/a",
            "0 2 * * * /bin/b",
        ]
        result = detect_overlaps(entries)
        assert result == []

    def test_sample_times_populated(self):
        entries = [
            "0 12 * * * /bin/noon_a",
            "0 12 * * * /bin/noon_b",
        ]
        result = detect_overlaps(entries)
        assert len(result) == 1
        assert len(result[0].sample_times) > 0

    def test_three_entries_two_overlaps(self):
        entries = [
            "0 * * * * /bin/every_hour",
            "0 6 * * * /bin/at_six",
            "0 6 * * * /bin/also_six",
        ]
        result = detect_overlaps(entries)
        assert len(result) >= 2


class TestLintLines:
    def test_clean_input(self):
        lines = ["30 4 * * 0 /bin/weekly"]
        report = lint_lines(lines)
        assert not report.has_errors
        assert not report.has_overlaps

    def test_overlap_detected_in_report(self):
        lines = [
            "*/10 * * * * /bin/a",
            "*/10 * * * * /bin/b",
        ]
        report = lint_lines(lines, source="test_input")
        assert report.has_overlaps

    def test_parse_error_captured(self):
        lines = ["not a valid cron"]
        report = lint_lines(lines)
        assert len(report.parse_errors) == 1

    def test_summary_contains_overlap_label(self):
        lines = [
            "0 8 * * * /bin/a",
            "0 8 * * * /bin/b",
        ]
        report = lint_lines(lines)
        summary = report.summary()
        assert "OVERLAP" in summary

    def test_summary_no_issues(self):
        lines = ["0 3 * * 1 /bin/weekly"]
        report = lint_lines(lines)
        assert "No issues found" in report.summary()
