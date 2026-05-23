"""Tests for crontab_lint.exporter."""
from __future__ import annotations

import pytest

from crontab_lint.exporter import ExportFormat, export, export_csv, export_markdown
from crontab_lint.linter import FileLintReport
from crontab_lint.validator import LintResult, ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(lines: list[str]) -> FileLintReport:
    """Build a minimal FileLintReport from raw cron lines."""
    from crontab_lint.linter import lint_file
    import tempfile, os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".crontab", delete=False) as fh:
        fh.write("\n".join(lines) + "\n")
        path = fh.name
    try:
        return lint_file(path)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# CSV tests
# ---------------------------------------------------------------------------

class TestExportCsv:
    def test_csv_has_header(self):
        report = _make_report(["* * * * * echo hi"])
        result = export_csv(report)
        assert result.content.startswith("file,line,expression,valid,errors")

    def test_csv_format_enum(self):
        report = _make_report(["* * * * * echo hi"])
        result = export_csv(report)
        assert result.format == ExportFormat.CSV

    def test_csv_valid_row(self):
        report = _make_report(["0 9 * * 1 /usr/bin/backup"])
        result = export_csv(report)
        assert "True" in result.content

    def test_csv_invalid_row_contains_error(self):
        report = _make_report(["99 * * * * bad"])
        result = export_csv(report)
        assert "False" in result.content
        # error message present
        assert len(result.content.splitlines()) >= 2

    def test_csv_multiple_rows(self):
        report = _make_report(["* * * * * cmd1", "0 0 * * * cmd2"])
        result = export_csv(report)
        # header + 2 data rows
        assert len(result.content.strip().splitlines()) == 3


# ---------------------------------------------------------------------------
# Markdown tests
# ---------------------------------------------------------------------------

class TestExportMarkdown:
    def test_markdown_has_heading(self):
        report = _make_report(["* * * * * echo hi"])
        result = export_markdown(report)
        assert result.content.startswith("## ")

    def test_markdown_format_enum(self):
        report = _make_report(["* * * * * echo hi"])
        result = export_markdown(report)
        assert result.format == ExportFormat.MARKDOWN

    def test_markdown_table_header(self):
        report = _make_report(["* * * * * echo hi"])
        result = export_markdown(report)
        assert "| Line |" in result.content
        assert "| Expression |" in result.content

    def test_markdown_valid_checkmark(self):
        report = _make_report(["0 12 * * * /bin/run"])
        result = export_markdown(report)
        assert "✅" in result.content

    def test_markdown_invalid_cross(self):
        report = _make_report(["99 * * * * bad"])
        result = export_markdown(report)
        assert "❌" in result.content


# ---------------------------------------------------------------------------
# Dispatch tests
# ---------------------------------------------------------------------------

class TestExportDispatch:
    def test_dispatch_csv(self):
        report = _make_report(["* * * * * echo"])
        result = export(report, ExportFormat.CSV)
        assert result.format == ExportFormat.CSV

    def test_dispatch_markdown(self):
        report = _make_report(["* * * * * echo"])
        result = export(report, ExportFormat.MARKDOWN)
        assert result.format == ExportFormat.MARKDOWN

    def test_dispatch_unknown_raises(self):
        report = _make_report(["* * * * * echo"])
        with pytest.raises(ValueError, match="Unsupported export format"):
            export(report, "xml")  # type: ignore[arg-type]
