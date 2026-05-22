"""Additional edge-case tests for schedule_diff module."""

from __future__ import annotations

from datetime import datetime

import pytest

from crontab_lint.schedule_diff import diff_schedules, ScheduleDiff


ANCHOR = datetime(2024, 3, 1, 0, 0)


class TestScheduleDiff:
    def test_only_in_a_sorted(self):
        diff = diff_schedules("0 6 * * *", "0 18 * * *", after=ANCHOR, count=3)
        assert diff.only_in_a == sorted(diff.only_in_a)

    def test_only_in_b_sorted(self):
        diff = diff_schedules("0 6 * * *", "0 18 * * *", after=ANCHOR, count=3)
        assert diff.only_in_b == sorted(diff.only_in_b)

    def test_partial_overlap(self):
        # Both fire at :00 but expr_b also fires at :30
        diff = diff_schedules("0 * * * *", "0,30 * * * *", after=ANCHOR, count=10)
        # common should be non-empty (the :00 minutes)
        assert diff.common
        # only_in_b should be non-empty (the :30 minutes)
        assert diff.only_in_b
        assert not diff.only_in_a

    def test_has_differences_false_for_same(self):
        diff = ScheduleDiff(only_in_a=[], only_in_b=[], common=[datetime(2024, 1, 1)])
        assert not diff.has_differences

    def test_has_differences_true_when_only_in_a(self):
        diff = ScheduleDiff(only_in_a=[datetime(2024, 1, 1)], only_in_b=[], common=[])
        assert diff.has_differences

    def test_summary_counts_correct(self):
        dt1, dt2, dt3 = (
            datetime(2024, 1, 1, 6, 0),
            datetime(2024, 1, 1, 7, 0),
            datetime(2024, 1, 1, 8, 0),
        )
        diff = ScheduleDiff(only_in_a=[dt1], only_in_b=[dt2], common=[dt3])
        summary = diff.summary()
        assert "1" in summary  # all counts are 1
