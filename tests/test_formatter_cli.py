"""Tests for the formatter module and CLI entry-point."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from crontab_lint.formatter import OutputFormat, format_json, format_text, render
from crontab_lint.cli import build_parser, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(tmp_path: Path, content: str) -> object:
    """Write *content* to a temp crontab file and return a FileLintReport."""
    from crontab_lint.linter import lint_file

    cron_file = tmp_path / "crontab"
    cron_file.write_text(textwrap.dedent(content))
    return lint_file(cron_file)


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------

class TestFormatter:
    def test_text_contains_file_path(self, tmp_path):
        report = _make_report(tmp_path, "* * * * * /bin/true\n")
        out = format_text(report)
        assert str(report.path) in out

    def test_text_ok_status(self, tmp_path):
        report = _make_report(tmp_path, "0 * * * * /bin/true\n")
        out = format_text(report)
        assert "OK" in out or "ok" in out.lower()

    def test_text_shows_error(self, tmp_path):
        report = _make_report(tmp_path, "99 * * * * /bin/true\n")
        out = format_text(report)
        assert "Error" in out or "error" in out.lower()

    def test_json_is_valid_json(self, tmp_path):
        report = _make_report(tmp_path, "0 12 * * 1 /bin/backup\n")
        raw = format_json(report)
        data = json.loads(raw)
        assert "path" in data
        assert "errors" in data
        assert "overlaps" in data

    def test_json_status_ok(self, tmp_path):
        report = _make_report(tmp_path, "0 6 * * * /bin/true\n")
        data = json.loads(format_json(report))
        assert data["status"] == "ok"

    def test_json_status_fail_on_error(self, tmp_path):
        report = _make_report(tmp_path, "bad line\n")
        data = json.loads(format_json(report))
        assert data["status"] == "fail"

    def test_render_dispatches_json(self, tmp_path):
        report = _make_report(tmp_path, "0 0 * * * /bin/true\n")
        out = render(report, OutputFormat.JSON)
        json.loads(out)  # must not raise

    def test_render_dispatches_text(self, tmp_path):
        report = _make_report(tmp_path, "0 0 * * * /bin/true\n")
        out = render(report, OutputFormat.TEXT)
        assert "File:" in out


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class TestCLI:
    def test_missing_file_returns_2(self, tmp_path):
        code = main([str(tmp_path / "nonexistent")])
        assert code == 2

    def test_valid_file_returns_0(self, tmp_path):
        f = tmp_path / "crontab"
        f.write_text("0 12 * * 1 /bin/backup\n")
        code = main([str(f)])
        assert code == 0

    def test_invalid_file_returns_1(self, tmp_path):
        f = tmp_path / "crontab"
        f.write_text("not a cron expression\n")
        code = main([str(f)])
        assert code == 1

    def test_json_format_flag(self, tmp_path, capsys):
        f = tmp_path / "crontab"
        f.write_text("0 0 * * * /bin/true\n")
        main(["--format", "json", str(f)])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "status" in data

    def test_no_overlaps_flag_accepted(self, tmp_path):
        f = tmp_path / "crontab"
        f.write_text("0 0 * * * /bin/true\n")
        code = main(["--no-overlaps", str(f)])
        assert code == 0
