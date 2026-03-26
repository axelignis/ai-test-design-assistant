"""
Deterministic post-processor for TestDesignOutput.

Responsibility: clean, deduplicate, and enforce content rules on AI output.
No AI calls. No side effects. No external dependencies beyond models.

Public interface:
    post_process(output: TestDesignOutput) -> TestDesignOutput
    OutputQualityError
"""

import re
from typing import List

from .models import TestDesignOutput


class OutputQualityError(Exception):
    """Raised when AI output fails content quality rules after cleaning."""


_MIN_ITEMS = 3
_MAX_ITEMS = 10
_MIN_ITEM_CHARS = 20
_MAX_ITEM_CHARS = 300

# "1. ", "2) ", "- ", "* ", "• "
_LEADING_NUMBERING = re.compile(r"^\s*(?:\d+[.)]\s+|[-*•]\s+)")

# **bold**, *italic*, __bold__, _italic_
_MARKDOWN_EMPHASIS = re.compile(r"(\*{1,2}|_{1,2})([^*_]+)\1")

# `inline code`
_INLINE_CODE = re.compile(r"`([^`]+)`")


def _clean_item(item: str) -> str:
    item = _LEADING_NUMBERING.sub("", item)
    item = _MARKDOWN_EMPHASIS.sub(r"\2", item)
    item = _INLINE_CODE.sub(r"\1", item)
    return " ".join(item.split())


def _normalize_for_dedup(item: str) -> str:
    normalized = item.lower()
    normalized = re.sub(r"[^\w\s]", "", normalized)
    return " ".join(normalized.split())


def _process_field(items: List[str], field_name: str) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()

    for raw in items:
        item = _clean_item(raw)

        if len(item) < _MIN_ITEM_CHARS:
            continue

        if len(item) > _MAX_ITEM_CHARS:
            raise OutputQualityError(
                f"Item in '{field_name}' exceeds {_MAX_ITEM_CHARS} characters "
                f"({len(item)} chars). AI output quality check failed. "
                f"Preview: {item[:80]}..."
            )

        key = _normalize_for_dedup(item)
        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    if len(result) < _MIN_ITEMS:
        raise OutputQualityError(
            f"Field '{field_name}' has {len(result)} usable item(s) after cleaning "
            f"(minimum required: {_MIN_ITEMS}). AI output may be thin or degenerate."
        )

    if len(result) > _MAX_ITEMS:
        raise OutputQualityError(
            f"Field '{field_name}' has {len(result)} items after cleaning "
            f"(maximum allowed: {_MAX_ITEMS}). AI output may be bloated."
        )

    return result


def post_process(output: TestDesignOutput) -> TestDesignOutput:
    """
    Clean, deduplicate, and validate a TestDesignOutput.

    Steps per field:
      1. Strip leading numbering and inline markdown from each item
      2. Filter items shorter than 20 characters
      3. Raise OutputQualityError for items longer than 300 characters
      4. Remove intra-list duplicates (normalized comparison)
      5. Enforce minimum 3 and maximum 10 items per field

    Returns a new TestDesignOutput with cleaned content.
    Raises OutputQualityError if content rules cannot be satisfied.
    """
    fields = {
        "positive_scenarios": output.positive_scenarios,
        "negative_scenarios": output.negative_scenarios,
        "edge_cases": output.edge_cases,
        "clarification_questions": output.clarification_questions,
        "risks": output.risks,
    }

    cleaned = {
        field_name: _process_field(items, field_name)
        for field_name, items in fields.items()
    }

    return TestDesignOutput(**cleaned)
