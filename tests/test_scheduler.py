"""Tests for crontab_lint.scheduler and crontab_lint.humanizer."""

from __future__ import annotations

import pytest
from datetime import datetime

from crontab_lint.scheduler import next_runs, ScheduleError
from crontab_lint.humanizer import humanize_next_runs, describe_schedule
from crontab_lint.schedule_diff import diff_schedules


ANCHOR = datetime(2024, 1, 1, 0, 0)  # Monday midnight


class TestNextRuns:
    def test_every_minute_returns_count(self):
        runs = next_runs("* * * * *", after=ANCHOR, count=5)
        assert len(runs) == 5

    def test_every_minute_consecutive(self):
        runs = next_runs("* * * * *", after=ANCHOR, count=3)
        from datetime import timedelta
        assert runs[1] - runs[0] == timedelta(minutes=1)

    def test_hourly_expression(self):
        runs = next_runs("0 * * * *", after=ANCHOR, count=3)
        for dt in runs:
            assert dt.minute == 0

    def test_daily_midnight(self):
        runs = next_runs("0 0 * * *", after=ANCHOR, count=3)
        for dt in runs:
            assert dt.hour == 0 and dt.minute == 0

    def test_weekday_only(self):
        # 0 9 * * 1-5  → weekdays at 09:00
        runs = next_runs("0 9 * * 1-5", after=ANCHOR, count=5)
        for dt in runs:
            assert dt.weekday() in range(0, 5)  # Mon–Fri
            assert dt.hour == 9

    def test_count_zero_raises(self):
        with pytest.raises(ValueError):
            next_runs("* * * * *", after=ANCHOR, count=0)

    def test_expression_with_command_accepted(self):
        runs = next_runs("* * * * * /usr/bin/true", after=ANCHOR, count=2)
        assert len(runs) == 2


class TestHumanizer:
    def test_humanize_returns_strings(self):
        result = humanize_next_runs("0 12 * * *", after=ANCHOR, count=2)
        assert all(isinstance(s, str) for s in result)
        assert len(result) == 2

    def test_humanize_format(self):
        result = humanize_next_runs("0 6 * * *", after=ANCHOR, count=1)
        # Should match YYYY-MM-DD HH:MM
        datetime.strptime(result[0], "%Y-%m-%d %H:%M")

    def test_describe_schedule_contains_next_runs(self):
        desc = describe_schedule("0 8 * * *", count=2)
        assert "Next 2 run" in desc


class TestScheduleDiff:
    def test_identical_schedules_no_diff(self):
        diff = diff_schedules("* * * * *", "* * * * *", after=ANCHOR, count=10)
        assert not diff.has_differences
        assert len(diff.common) == 10

    def test_different_schedules_have_diffs(self):
        diff = diff_schedules("0 * * * *", "30 * * * *", after=ANCHOR, count=5)
        assert diff.has_differences
        assert not diff.common  # no overlap between :00 and :30

    def test_summary_string(self):
        diff = diff_schedules("* * * * *", "0 * * * *", after=ANCHOR, count=5)
        summary = diff.summary()
        assert "Common" in summary
        assert "Only in first" in summary
