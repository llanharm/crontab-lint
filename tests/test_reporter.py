"""Tests for crontab_lint.reporter."""
from __future__ import annotations

import os
import tempfile

import pytest

from crontab_lint.reporter import report_files, MultiFileReport


def _tmpfile(lines: list[str]) -> str:
    fh = tempfile.NamedTemporaryFile(
        mode="w", suffix=".crontab", delete=False
    )
    fh.write("\n".join(lines) + "\n")
    fh.close()
    return fh.name


class TestMultiFileReport:
    def setup_method(self):
        self._files: list[str] = []

    def teardown_method(self):
        for p in self._files:
            try:
                os.unlink(p)
            except OSError:
                pass

    def _make(self, lines: list[str]) -> str:
        p = _tmpfile(lines)
        self._files.append(p)
        return p

    def test_empty_paths(self):
        report = report_files([])
        assert report.total_files == 0
        assert report.overall_health == 1.0

    def test_single_valid_file(self):
        p = self._make(["* * * * * echo hi", "0 0 * * * echo daily"])
        report = report_files([p])
        assert report.total_files == 1
        assert report.files_with_errors == 0
        assert report.overall_health == 1.0

    def test_file_with_invalid_entry(self):
        p = self._make(["* * * * * echo ok", "BROKEN LINE"])
        report = report_files([p])
        assert report.files_with_errors >= 1
        assert report.overall_health < 1.0

    def test_multiple_files(self):
        p1 = self._make(["* * * * * echo a"])
        p2 = self._make(["0 6 * * * echo b", "30 6 * * * echo c"])
        report = report_files([p1, p2])
        assert report.total_files == 2

    def test_missing_file_counted(self):
        report = report_files(["/nonexistent/path/crontab"])
        assert report.total_files == 1
        assert report.files_with_errors == 1

    def test_text_report_contains_header(self):
        p = self._make(["* * * * * echo hi"])
        report = report_files([p])
        text = report.text_report()
        assert "Multi-File Report" in text
        assert "Files scanned" in text
        assert "Overall health" in text

    def test_text_report_contains_file_path(self):
        p = self._make(["0 12 * * * echo noon"])
        report = report_files([p])
        text = report.text_report()
        assert p in text
