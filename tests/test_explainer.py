"""Tests for crontab_lint.explainer."""

import pytest
from crontab_lint.parser import parse
from crontab_lint.explainer import explain


class TestExplainer:
    def _explain(self, expr: str) -> str:
        """Parse a cron expression and return its human-readable explanation."""
        return explain(parse(expr + " /usr/bin/cmd"))

    def test_every_minute(self):
        result = self._explain("* * * * *")
        assert "every minute" in result

    def test_specific_minute_and_hour(self):
        result = self._explain("30 6 * * *")
        assert "30" in result
        assert "6" in result

    def test_step_minutes(self):
        result = self._explain("*/15 * * * *")
        assert "every 15 minutes" in result

    def test_specific_weekday(self):
        result = self._explain("0 9 * * 1")
        assert "Monday" in result

    def test_specific_month(self):
        result = self._explain("0 0 1 6 *")
        assert "June" in result

    def test_range_hours(self):
        result = self._explain("0 9-17 * * *")
        assert "9" in result
        assert "17" in result

    def test_comma_weekdays(self):
        result = self._explain("0 8 * * 1,3,5")
        assert "Monday" in result
        assert "Wednesday" in result
        assert "Friday" in result

    def test_dom_and_dow_both_set(self):
        result = self._explain("0 0 15 * 0")
        assert "day-of-month" in result
        assert "Sunday" in result

    def test_month_alias_resolved(self):
        # parser resolves JUN -> 6 before explainer sees it
        result = self._explain("0 12 * JUN *")
        assert "June" in result

    def test_returns_string_ending_with_period(self):
        result = self._explain("5 4 * * *")
        assert result.endswith(".")

    def test_step_range(self):
        result = self._explain("0 8-18/2 * * *")
        assert "every 2 hours" in result
        assert "8" in result
        assert "18" in result

    def test_returns_non_empty_string(self):
        """Explanation should always return a non-empty string for any valid expression."""
        expressions = [
            "* * * * *",
            "0 0 * * *",
            "59 23 31 12 6",
            "*/5 */2 * * *",
            "0 0 1 1 *",
        ]
        for expr in expressions:
            result = self._explain(expr)
            assert isinstance(result, str), f"Expected str for {expr!r}, got {type(result)}"
            assert len(result) > 0, f"Expected non-empty result for {expr!r}"
