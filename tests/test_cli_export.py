"""Tests for crontab_lint.cli_export."""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import pytest

from crontab_lint.cli_export import build_export_parser, run_export


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmpfile(content: str) -> str:
    fh = tempfile.NamedTemporaryFile(mode="w", suffix=".crontab", delete=False)
    fh.write(content)
    fh.close()
    return fh.name


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"file": "", "fmt": "csv", "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

class TestBuildExportParser:
    def test_registers_export_subcommand(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers()
        p = build_export_parser(subs)
        assert p is not None

    def test_default_format_is_csv(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers(dest="cmd")
        build_export_parser(subs)
        ns = root.parse_args(["export", "some_file"])
        assert ns.fmt == "csv"

    def test_markdown_format_accepted(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers(dest="cmd")
        build_export_parser(subs)
        ns = root.parse_args(["export", "f", "--format", "markdown"])
        assert ns.fmt == "markdown"


# ---------------------------------------------------------------------------
# run_export behaviour
# ---------------------------------------------------------------------------

class TestRunExport:
    def setup_method(self):
        self._files: list[str] = []

    def teardown_method(self):
        for f in self._files:
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

    def _make(self, content: str) -> str:
        path = _tmpfile(content)
        self._files.append(path)
        return path

    def test_missing_file_returns_2(self):
        args = _make_args(file="/nonexistent/path.crontab")
        assert run_export(args) == 2

    def test_valid_crontab_returns_0(self):
        path = self._make("0 9 * * 1 /bin/backup\n")
        args = _make_args(file=path)
        assert run_export(args) == 0

    def test_invalid_crontab_returns_1(self):
        path = self._make("99 * * * * bad\n")
        args = _make_args(file=path)
        assert run_export(args) == 1

    def test_output_written_to_file(self, tmp_path):
        cron_path = self._make("* * * * * echo hi\n")
        out_path = str(tmp_path / "out.csv")
        args = _make_args(file=cron_path, output=out_path)
        run_export(args)
        content = Path(out_path).read_text(encoding="utf-8")
        assert "file" in content  # CSV header

    def test_markdown_output_to_file(self, tmp_path):
        cron_path = self._make("0 0 * * * /bin/run\n")
        out_path = str(tmp_path / "out.md")
        args = _make_args(file=cron_path, fmt="markdown", output=out_path)
        run_export(args)
        content = Path(out_path).read_text(encoding="utf-8")
        assert "##" in content
