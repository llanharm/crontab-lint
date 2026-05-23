"""Tests for crontab_lint.tagger."""

import pytest
from crontab_lint.tagger import tag, TaggedEntry


def _tags(expr: str):
    return tag(expr).tags


class TestTagger:
    def test_returns_tagged_entry(self):
        result = tag("* * * * * /bin/true")
        assert isinstance(result, TaggedEntry)

    def test_every_minute_tags(self):
        tags = _tags("* * * * * /bin/true")
        assert "every-minute" in tags
        assert "frequent" in tags

    def test_step_5_is_frequent(self):
        tags = _tags("*/5 * * * * /bin/true")
        assert "frequent" in tags
        assert "sub-hourly" in tags

    def test_step_30_not_frequent(self):
        tags = _tags("*/30 * * * * /bin/true")
        assert "frequent" not in tags

    def test_hourly_not_frequent(self):
        tags = _tags("0 * * * * /bin/true")
        assert "frequent" not in tags
        assert "sub-hourly" in tags

    def test_daily_tag(self):
        tags = _tags("30 6 * * * /bin/backup")
        assert "daily" in tags

    def test_midnight_tag(self):
        tags = _tags("0 0 * * * /bin/cleanup")
        assert "midnight" in tags
        assert "daily" in tags

    def test_weekly_tag(self):
        tags = _tags("0 9 * * 1 /bin/report")
        assert "weekly" in tags

    def test_monthly_tag(self):
        tags = _tags("0 0 1 * * /bin/monthly")
        assert "monthly" in tags

    def test_business_hours_tag(self):
        tags = _tags("0 9 * * 1-5 /bin/work")
        assert "business-hours" in tags

    def test_invalid_expression_tagged_invalid(self):
        tags = _tags("not a cron")
        assert tags == ["invalid"]

    def test_raw_preserved(self):
        expr = "0 12 * * * /bin/noon"
        result = tag(expr)
        assert result.raw == expr

    def test_tags_are_sorted(self):
        tags = _tags("0 0 * * * /bin/cleanup")
        assert tags == sorted(tags)

    def test_no_duplicate_tags(self):
        tags = _tags("* * * * * /bin/true")
        assert len(tags) == len(set(tags))
