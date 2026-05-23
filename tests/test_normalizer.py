"""Tests for crontab_lint.normalizer."""

import pytest

from crontab_lint.normalizer import normalize, NormalizedCron
from crontab_lint.parser import ParseError


class TestNormalizer:
    def test_plain_expression_unchanged(self):
        result = normalize("0 0 * * * /usr/bin/backup")
        assert result.normalized == "0 0 * * * /usr/bin/backup"
        assert result.was_macro is False

    def test_command_extracted(self):
        result = normalize("30 6 * * * echo hello")
        assert result.command == "echo hello"

    def test_month_name_replaced(self):
        result = normalize("0 0 1 Jan * /bin/run")
        assert "1" in result.normalized.split()[3]
        assert "jan" not in result.normalized.lower().split()[3]

    def test_month_name_case_insensitive(self):
        result = normalize("0 0 1 DEC * /bin/run")
        assert result.normalized.split()[3] == "12"

    def test_dow_name_replaced(self):
        result = normalize("0 0 * * Mon /bin/run")
        assert result.normalized.split()[4] == "1"

    def test_dow_sun_replaced(self):
        result = normalize("0 0 * * Sun /bin/run")
        assert result.normalized.split()[4] == "0"

    def test_dow_range_with_names(self):
        result = normalize("0 9 * * Mon-Fri /bin/run")
        normalized_dow = result.normalized.split()[4]
        assert normalized_dow == "1-5"

    def test_month_list_with_names(self):
        result = normalize("0 0 1 Jan,Jun,Dec * /bin/run")
        normalized_month = result.normalized.split()[3]
        assert normalized_month == "1,6,12"

    def test_macro_daily(self):
        result = normalize("@daily /bin/cleanup")
        assert result.was_macro is True
        assert result.normalized == "0 0 * * * /bin/cleanup"
        assert result.command == "/bin/cleanup"

    def test_macro_hourly(self):
        result = normalize("@hourly /bin/poll")
        assert result.normalized == "0 * * * * /bin/poll"
        assert result.was_macro is True

    def test_macro_yearly(self):
        result = normalize("@yearly /bin/annual")
        assert result.normalized == "0 0 1 1 * /bin/annual"

    def test_macro_annually_same_as_yearly(self):
        a = normalize("@yearly /bin/x")
        b = normalize("@annually /bin/x")
        assert a.normalized == b.normalized

    def test_macro_midnight_same_as_daily(self):
        a = normalize("@midnight /bin/x")
        b = normalize("@daily /bin/x")
        assert a.normalized == b.normalized

    def test_macro_weekly(self):
        result = normalize("@weekly /bin/weekly")
        assert result.normalized == "0 0 * * 0 /bin/weekly"

    def test_macro_monthly(self):
        result = normalize("@monthly /bin/monthly")
        assert result.normalized == "0 0 1 * * /bin/monthly"

    def test_original_preserved(self):
        expr = "0 12 * * Mon /bin/noon"
        result = normalize(expr)
        assert result.original == expr

    def test_invalid_expression_raises(self):
        with pytest.raises(ParseError):
            normalize("not a cron expression")

    def test_step_syntax_preserved(self):
        result = normalize("*/15 * * * * /bin/frequent")
        assert result.normalized.startswith("*/15")

    def test_repr_contains_normalized(self):
        result = normalize("0 0 * * * /bin/run")
        r = repr(result)
        assert "NormalizedCron" in r
