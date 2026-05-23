"""Filter a list of crontab lines by tag."""

from __future__ import annotations

from typing import List

from .tagger import TaggedEntry, tag


def tag_all(expressions: List[str]) -> List[TaggedEntry]:
    """Return a TaggedEntry for every expression in *expressions*."""
    return [tag(expr) for expr in expressions]


def filter_by_tag(expressions: List[str], required_tag: str) -> List[TaggedEntry]:
    """Return entries whose tag list contains *required_tag*."""
    return [
        entry
        for entry in tag_all(expressions)
        if required_tag in entry.tags
    ]


def group_by_tag(expressions: List[str]) -> dict[str, List[TaggedEntry]]:
    """Group entries by their first (primary) tag.

    Entries with no tags (should not occur for valid input) are placed under
    the key ``"untagged"``.
    """
    groups: dict[str, List[TaggedEntry]] = {}
    for entry in tag_all(expressions):
        primary = entry.tags[0] if entry.tags else "untagged"
        groups.setdefault(primary, []).append(entry)
    return groups
