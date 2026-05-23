"""Tests for crontab_lint.comparator."""

import pytest
from crontab_lint.comparator import compare, CompareResult, FieldDiff


class TestComparitor:
    def test_identical_expressions_are_equivalent(self):
        result = compare("0 * * * * /bin/job", "0 * * * * /bin/job")
        assert result.is_equivalent
        assert result.error is None

    def test_different_minute_detected(self):
        result = compare("0 * * * * /bin/job", "5 * * * * /bin/job")
        assert not result.is_equivalent
        assert any(d.field_name == "minute" for d in result.field_diffs)

    def test_different_hour_detected(self):
        result = compare("0 1 * * * /bin/job", "0 2 * * * /bin/job")
        assert not result.is_equivalent
        assert any(d.field_name == "hour" for d in result.field_diffs)

    def test_month_alias_normalised_before_compare(self):
        # JAN and 1 should normalise to the same token
        result = compare("0 0 1 JAN * /bin/job", "0 0 1 1 * /bin/job")
        assert result.is_equivalent, result.summary()

    def test_command_change_detected(self):
        result = compare("0 * * * * /bin/job_a", "0 * * * * /bin/job_b")
        assert result.command_changed
        assert not result.is_equivalent

    def test_multiple_field_diffs(self):
        result = compare("0 1 * * * /bin/job", "30 6 * * * /bin/job")
        names = {d.field_name for d in result.field_diffs}
        assert "minute" in names
        assert "hour" in names

    def test_summary_equivalent(self):
        result = compare("* * * * * /bin/job", "* * * * * /bin/job")
        assert "equivalent" in result.summary().lower()

    def test_summary_shows_diff(self):
        result = compare("0 * * * * /bin/job", "5 * * * * /bin/job")
        assert "minute" in result.summary()

    def test_invalid_expression_returns_error(self):
        result = compare("not_a_cron", "* * * * * /bin/job")
        assert result.error is not None
        assert not result.is_equivalent

    def test_error_summary_contains_error_text(self):
        result = compare("bad", "* * * * * /bin/job")
        assert "Error" in result.summary()

    def test_field_diff_repr(self):
        d = FieldDiff(field_name="minute", value_a="0", value_b="5")
        assert "minute" in repr(d)

    def test_wildcard_vs_wildcard_equivalent(self):
        result = compare("* * * * * /bin/task", "* * * * * /bin/task")
        assert result.is_equivalent

    def test_step_expressions_compared(self):
        result = compare("*/5 * * * * /bin/job", "*/10 * * * * /bin/job")
        assert not result.is_equivalent
        assert any(d.field_name == "minute" for d in result.field_diffs)
