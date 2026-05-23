"""Tests for crontab_lint.humanizer — human-readable schedule descriptions."""

import pytest
from datetime import datetime
from unittest.mock import patch

from crontab_lint.humanizer import humanize_next_runs, describe_schedule
from crontab_lint.scheduler import ScheduleError


class TestDescribeSchedule:
    """Unit tests for describe_schedule()."""

    def test_every_minute(self):
        result = describe_schedule("* * * * *")
        assert "every minute" in result.lower()

    def test_hourly(self):
        result = describe_schedule("0 * * * *")
        assert "hour" in result.lower()

    def test_daily_midnight(self):
        result = describe_schedule("0 0 * * *")
        assert "day" in result.lower() or "midnight" in result.lower()

    def test_specific_minute(self):
        result = describe_schedule("30 * * * *")
        assert "30" in result

    def test_specific_hour_and_minute(self):
        result = describe_schedule("15 9 * * *")
        assert "9" in result or "09" in result
        assert "15" in result

    def test_weekday_only(self):
        result = describe_schedule("0 9 * * 1")
        # Should mention Monday or weekday
        assert any(word in result.lower() for word in ("mon", "monday", "weekday", "1"))

    def test_monthly(self):
        result = describe_schedule("0 0 1 * *")
        assert any(word in result.lower() for word in ("month", "1st", "first", "day 1"))

    def test_step_expression(self):
        result = describe_schedule("*/15 * * * *")
        assert "15" in result

    def test_invalid_expression_raises(self):
        with pytest.raises((ValueError, ScheduleError, Exception)):
            describe_schedule("invalid expression here")

    def test_returns_string(self):
        result = describe_schedule("0 12 * * *")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_range_expression(self):
        result = describe_schedule("0 9-17 * * *")
        assert "9" in result and "17" in result


class TestHumanizeNextRuns:
    """Unit tests for humanize_next_runs()."""

    def _fixed_now(self):
        return datetime(2024, 1, 15, 12, 0, 0)

    def test_returns_list(self):
        with patch("crontab_lint.humanizer.datetime") as mock_dt:
            mock_dt.utcnow.return_value = self._fixed_now()
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = humanize_next_runs("* * * * *", count=3)
        assert isinstance(result, list)

    def test_correct_count(self):
        with patch("crontab_lint.scheduler.datetime") as mock_dt:
            mock_dt.utcnow.return_value = self._fixed_now()
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = humanize_next_runs("0 * * * *", count=4)
        assert len(result) == 4

    def test_each_entry_is_string(self):
        result = humanize_next_runs("0 0 * * *", count=2)
        for entry in result:
            assert isinstance(entry, str)
            assert len(entry) > 0

    def test_default_count_is_five(self):
        result = humanize_next_runs("*/10 * * * *")
        assert len(result) == 5

    def test_invalid_expression_raises(self):
        with pytest.raises(Exception):
            humanize_next_runs("not a cron")

    def test_strings_contain_time_info(self):
        result = humanize_next_runs("0 6 * * *", count=1)
        # Should contain some recognisable date/time fragment
        assert any(char.isdigit() for char in result[0])
