"""Tests for the crontab parser and validator modules."""

import pytest
from crontab_lint.parser import parse, ParseError
from crontab_lint.validator import validate


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestParser:
    def test_basic_expression(self):
        p = parse("0 12 * * 1")
        assert len(p.fields) == 5
        assert p.fields[0].raw == "0"
        assert p.fields[1].raw == "12"

    def test_command_extracted(self):
        p = parse("*/5 * * * * /usr/bin/backup.sh")
        assert p.command == "/usr/bin/backup.sh"

    def test_too_few_fields_raises(self):
        with pytest.raises(ParseError):
            parse("0 12 * *")

    def test_month_alias_resolved(self):
        p = parse("0 0 1 jan *")
        assert p.fields[3].raw == "1"

    def test_weekday_alias_resolved(self):
        p = parse("0 0 * * mon")
        assert p.fields[4].raw == "1"

    def test_no_command_is_none(self):
        p = parse("0 0 * * *")
        assert p.command is None


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

class TestValidator:
    def test_valid_expression(self):
        result = validate(parse("0 12 * * 1"))
        assert result.is_valid
        assert result.errors == []

    def test_out_of_range_minute(self):
        result = validate(parse("60 12 * * *"))
        assert not result.is_valid
        assert any("minute" in e for e in result.errors)

    def test_out_of_range_hour(self):
        result = validate(parse("0 25 * * *"))
        assert not result.is_valid
        assert any("hour" in e for e in result.errors)

    def test_invalid_step_zero(self):
        result = validate(parse("*/0 * * * *"))
        assert not result.is_valid

    def test_invalid_range_inverted(self):
        result = validate(parse("0 0 15-5 * *"))
        assert not result.is_valid
        assert any("greater than" in e for e in result.errors)

    def test_step_exceeds_range_warning(self):
        # step of 100 on minutes (range 60) should flag an error
        result = validate(parse("*/100 * * * *"))
        assert not result.is_valid

    def test_wildcard_always_valid(self):
        result = validate(parse("* * * * *"))
        assert result.is_valid

    def test_list_values_valid(self):
        result = validate(parse("0,15,30,45 * * * *"))
        assert result.is_valid

    def test_list_with_out_of_range(self):
        result = validate(parse("0,99 * * * *"))
        assert not result.is_valid
