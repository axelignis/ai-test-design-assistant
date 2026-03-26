import pytest
from pydantic import ValidationError

from src.models import RequirementInput, TestDesignOutput


class TestRequirementInput:
    def test_valid_minimal(self):
        req = RequirementInput(raw_text="User can log in with email and password")
        assert req.raw_text == "User can log in with email and password"
        assert req.source_type is None
        assert req.context is None

    def test_strips_surrounding_whitespace(self):
        req = RequirementInput(raw_text="  some requirement  ")
        assert req.raw_text == "some requirement"

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            RequirementInput(raw_text="")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            RequirementInput(raw_text="   \n\t  ")

    def test_valid_source_types(self):
        for source_type in ("user_story", "acceptance_criteria", "feature_description", "bug_ticket"):
            req = RequirementInput(raw_text="Some requirement", source_type=source_type)
            assert req.source_type == source_type

    def test_invalid_source_type_raises(self):
        with pytest.raises(ValidationError):
            RequirementInput(raw_text="Some requirement", source_type="test_case")

    def test_context_is_optional(self):
        req = RequirementInput(raw_text="Some requirement", context="Applies to mobile only")
        assert req.context == "Applies to mobile only"


class TestTestDesignOutput:
    def _valid_output(self) -> dict:
        return {
            "positive_scenarios": ["Valid login with correct credentials"],
            "negative_scenarios": ["Login fails with wrong password"],
            "edge_cases": ["Login with email containing + addressing"],
            "clarification_questions": ["What happens to an active session when the account is locked?"],
            "risks": ["Lockout mechanism could be triggered by a third party"],
        }

    def test_valid_output(self):
        output = TestDesignOutput(**self._valid_output())
        assert len(output.positive_scenarios) == 1
        assert len(output.risks) == 1

    def test_all_fields_required(self):
        data = self._valid_output()
        for field in data:
            subset = {k: v for k, v in data.items() if k != field}
            with pytest.raises(ValidationError):
                TestDesignOutput(**subset)

    def test_model_dump_returns_all_fields(self):
        output = TestDesignOutput(**self._valid_output())
        dumped = output.model_dump()
        expected_keys = {
            "positive_scenarios", "negative_scenarios", "edge_cases",
            "clarification_questions", "risks",
        }
        assert set(dumped.keys()) == expected_keys
