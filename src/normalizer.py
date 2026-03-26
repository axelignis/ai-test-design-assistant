import re
from typing import Optional

from .models import RequirementInput

_SOURCE_KEYWORDS: dict[str, list[str]] = {
    "user_story": ["as a ", "i want", "so that", "in order to"],
    "acceptance_criteria": ["given ", "when ", "then ", "acceptance criteria", "must ", "shall "],
    "bug_ticket": ["steps to reproduce", "actual behavior", "expected behavior", "defect", "reproduce"],
    "feature_description": ["feature", "capability", "functionality", "allow users", "enable users"],
}


def _detect_source_type(text: str) -> Optional[str]:
    lower = text.lower()
    scores = {
        kind: sum(1 for kw in keywords if kw in lower)
        for kind, keywords in _SOURCE_KEYWORDS.items()
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else None


def normalize(raw_text: str, context: Optional[str] = None) -> RequirementInput:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return RequirementInput(
        raw_text=cleaned,
        source_type=_detect_source_type(cleaned),
        context=context,
    )
