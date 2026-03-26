from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator


class RequirementInput(BaseModel):
    raw_text: str
    source_type: Optional[
        Literal[
            "user_story",
            "acceptance_criteria",
            "feature_description",
            "bug_ticket",
        ]
    ] = None
    context: Optional[str] = None

    @field_validator("raw_text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("raw_text must not be empty or whitespace-only")
        return v.strip()


class TestDesignOutput(BaseModel):
    positive_scenarios: List[str]
    negative_scenarios: List[str]
    edge_cases: List[str]
    clarification_questions: List[str]
    risks: List[str]
