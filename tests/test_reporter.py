import pytest
from pathlib import Path

from src.models import RequirementInput, TestDesignOutput
from src.reporter import generate_report, write_report

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ITEMS = [
    "User logs in successfully with valid email and password credentials",
    "User is redirected to their personal dashboard after successful login",
    "Login activity is recorded in the account audit log after authentication",
]

_REQUIREMENT_TEXT = (
    "As a registered user, I want to log in with my email and password "
    "so that I can access my personal dashboard."
)


def _make_output(**overrides) -> TestDesignOutput:
    defaults = {
        "positive_scenarios": _ITEMS[:],
        "negative_scenarios": _ITEMS[:],
        "edge_cases": _ITEMS[:],
        "clarification_questions": _ITEMS[:],
        "risks": _ITEMS[:],
    }
    defaults.update(overrides)
    return TestDesignOutput(**defaults)


def _make_requirement(source_type=None) -> RequirementInput:
    return RequirementInput(raw_text=_REQUIREMENT_TEXT, source_type=source_type)


# ---------------------------------------------------------------------------
# generate_report — structure
# ---------------------------------------------------------------------------


class TestReportStructure:
    def test_returns_string(self):
        report = generate_report(_make_requirement(), _make_output())
        assert isinstance(report, str)

    def test_contains_title(self):
        report = generate_report(_make_requirement(), _make_output())
        assert "# Test Design Report" in report

    @pytest.mark.parametrize("heading", [
        "## Executive Summary",
        "## Positive Scenarios",
        "## Negative Scenarios",
        "## Edge Cases",
        "## Clarification Questions",
        "## Risks",
        "## Requirement Snapshot",
    ])
    def test_contains_all_section_headings(self, heading):
        report = generate_report(_make_requirement(), _make_output())
        assert heading in report


# ---------------------------------------------------------------------------
# generate_report — executive summary counts
# ---------------------------------------------------------------------------


class TestExecutiveSummary:
    def test_counts_match_output_field_lengths(self):
        output = _make_output(
            positive_scenarios=_ITEMS[:],
            negative_scenarios=_ITEMS[:],
            edge_cases=_ITEMS[:],
            clarification_questions=_ITEMS[:],
            risks=_ITEMS[:],
        )
        report = generate_report(_make_requirement(), output)
        assert "**Positive scenarios:** 3" in report
        assert "**Negative scenarios:** 3" in report
        assert "**Edge cases:** 3" in report
        assert "**Clarification questions:** 3" in report
        assert "**Risks:** 3" in report

    def test_source_type_shown_when_set(self):
        req = _make_requirement(source_type="user_story")
        report = generate_report(req, _make_output())
        assert "**Source type:**" in report
        assert "User Story" in report

    def test_source_type_absent_when_none(self):
        req = _make_requirement(source_type=None)
        report = generate_report(req, _make_output())
        assert "**Source type:**" not in report


# ---------------------------------------------------------------------------
# generate_report — scenario content
# ---------------------------------------------------------------------------


class TestScenarioContent:
    def test_positive_scenario_items_appear_in_report(self):
        report = generate_report(_make_requirement(), _make_output())
        for item in _ITEMS:
            assert item in report

    def test_items_are_rendered_as_bullets(self):
        report = generate_report(_make_requirement(), _make_output())
        assert f"- {_ITEMS[0]}" in report


# ---------------------------------------------------------------------------
# generate_report — requirement snapshot
# ---------------------------------------------------------------------------


class TestRequirementSnapshot:
    def test_requirement_text_appears_in_snapshot(self):
        report = generate_report(_make_requirement(), _make_output())
        assert _REQUIREMENT_TEXT in report

    def test_snapshot_uses_blockquote_syntax(self):
        report = generate_report(_make_requirement(), _make_output())
        assert "> " in report

    def test_multiline_requirement_each_line_quoted(self):
        req = RequirementInput(raw_text="Line one\nLine two\nLine three")
        report = generate_report(req, _make_output())
        assert "> Line one" in report
        assert "> Line two" in report
        assert "> Line three" in report


# ---------------------------------------------------------------------------
# write_report
# ---------------------------------------------------------------------------


class TestWriteReport:
    def test_writes_file_to_path(self, tmp_path):
        report = generate_report(_make_requirement(), _make_output())
        output_path = tmp_path / "report.md"
        write_report(report, output_path)
        assert output_path.exists()

    def test_written_content_matches_report_string(self, tmp_path):
        report = generate_report(_make_requirement(), _make_output())
        output_path = tmp_path / "report.md"
        write_report(report, output_path)
        assert output_path.read_text(encoding="utf-8") == report

    def test_creates_missing_parent_directories(self, tmp_path):
        report = generate_report(_make_requirement(), _make_output())
        output_path = tmp_path / "nested" / "deep" / "report.md"
        write_report(report, output_path)
        assert output_path.exists()
