"""Tests for crontab_lint.recommender."""
import pytest

from crontab_lint.recommender import recommend, Suggestion, RecommendationReport
from crontab_lint.validator import LintResult


def _codes(report: RecommendationReport):
    return [s.code for s in report.suggestions]


class TestRecommender:
    def test_clean_expression_no_suggestions(self):
        report = recommend("0 9 * * 1 /usr/bin/backup")
        assert not report.has_suggestions

    def test_every_minute_warns_w001(self):
        report = recommend("* * * * * /bin/task")
        assert "W001" in _codes(report)

    def test_every_minute_fix_present(self):
        report = recommend("* * * * * /bin/task")
        w001 = next(s for s in report.suggestions if s.code == "W001")
        assert w001.fix is not None
        assert "hour" in w001.fix

    def test_dom_and_dow_both_set_warns_w002(self):
        report = recommend("0 12 15 * 5 /bin/task")
        assert "W002" in _codes(report)

    def test_dom_wildcard_no_w002(self):
        report = recommend("0 12 * * 5 /bin/task")
        assert "W002" not in _codes(report)

    def test_dow_wildcard_no_w002(self):
        report = recommend("0 12 15 * * /bin/task")
        assert "W002" not in _codes(report)

    def test_high_frequency_step_warns_w003(self):
        report = recommend("*/2 * * * * /bin/task")
        assert "W003" in _codes(report)

    def test_step_5_no_w003(self):
        report = recommend("*/5 * * * * /bin/task")
        assert "W003" not in _codes(report)

    def test_step_1_warns_w003(self):
        report = recommend("*/1 * * * * /bin/task")
        assert "W003" in _codes(report)

    def test_parse_error_returns_e000(self):
        report = recommend("not_a_cron")
        assert any(s.code == "E000" for s in report.suggestions)

    def test_invalid_lint_result_returns_e001(self):
        lint = LintResult(raw="* * * * *", errors=["minute out of range"])
        report = recommend("* * * * *", lint_result=lint)
        assert any(s.code == "E001" for s in report.suggestions)

    def test_invalid_lint_skips_further_checks(self):
        lint = LintResult(raw="* * * * *", errors=["bad field"])
        report = recommend("* * * * *", lint_result=lint)
        assert "W001" not in _codes(report)

    def test_has_suggestions_false_when_empty(self):
        report = RecommendationReport(raw="0 0 * * * /bin/x")
        assert not report.has_suggestions

    def test_summary_no_suggestions(self):
        report = RecommendationReport(raw="0 0 * * * /bin/x")
        assert report.summary() == "No suggestions."

    def test_summary_with_suggestions(self):
        report = recommend("* * * * * /bin/task")
        text = report.summary()
        assert "W001" in text

    def test_suggestion_repr_with_fix(self):
        s = Suggestion(code="W001", message="msg", fix="do this")
        assert "fix=" in repr(s)

    def test_multiple_issues_detected(self):
        # every minute AND dom+dow both set — should get W001 + W002
        report = recommend("* * 1 * 1 /bin/task")
        codes = _codes(report)
        assert "W001" in codes
        assert "W002" in codes
