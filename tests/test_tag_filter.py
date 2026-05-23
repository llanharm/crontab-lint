"""Tests for crontab_lint.tag_filter."""

from crontab_lint.tag_filter import tag_all, filter_by_tag, group_by_tag


_EXPRESSIONS = [
    "* * * * * /bin/every-minute",
    "0 0 * * * /bin/midnight",
    "0 9 * * 1-5 /bin/business",
    "*/5 * * * * /bin/five-min",
    "not valid at all",
]


class TestTagFilter:
    def test_tag_all_length(self):
        result = tag_all(_EXPRESSIONS)
        assert len(result) == len(_EXPRESSIONS)

    def test_tag_all_types(self):
        from crontab_lint.tagger import TaggedEntry
        for entry in tag_all(_EXPRESSIONS):
            assert isinstance(entry, TaggedEntry)

    def test_filter_by_frequent(self):
        result = filter_by_tag(_EXPRESSIONS, "frequent")
        raws = [e.raw for e in result]
        assert "* * * * * /bin/every-minute" in raws
        assert "*/5 * * * * /bin/five-min" in raws
        assert "0 0 * * * /bin/midnight" not in raws

    def test_filter_by_invalid(self):
        result = filter_by_tag(_EXPRESSIONS, "invalid")
        assert len(result) == 1
        assert result[0].raw == "not valid at all"

    def test_filter_by_midnight(self):
        result = filter_by_tag(_EXPRESSIONS, "midnight")
        assert len(result) == 1
        assert result[0].raw == "0 0 * * * /bin/midnight"

    def test_filter_no_match_returns_empty(self):
        result = filter_by_tag(_EXPRESSIONS, "nonexistent-tag")
        assert result == []

    def test_group_by_tag_contains_invalid(self):
        groups = group_by_tag(_EXPRESSIONS)
        assert "invalid" in groups

    def test_group_by_tag_every_minute(self):
        groups = group_by_tag(_EXPRESSIONS)
        raws = [e.raw for e in groups.get("business-hours", [])]
        assert "0 9 * * 1-5 /bin/business" in raws

    def test_group_by_tag_values_are_lists(self):
        groups = group_by_tag(_EXPRESSIONS)
        for v in groups.values():
            assert isinstance(v, list)

    def test_empty_input(self):
        assert tag_all([]) == []
        assert filter_by_tag([], "frequent") == []
        assert group_by_tag([]) == {}
