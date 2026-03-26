"""
AI generation layer.

Responsibility: take a normalized RequirementInput, call the AI, and return
a validated TestDesignOutput. Nothing else.

Entry point:
    python -m src.generator <requirement_file>
"""

import json
import os
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from .models import RequirementInput, TestDesignOutput
from .normalizer import normalize
from .postprocessor import post_process

load_dotenv()

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.txt"
_USER_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "test_design.txt"
_DEFAULT_MODEL = "claude-sonnet-4-6"


def _load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _load_user_template() -> str:
    return _USER_TEMPLATE_PATH.read_text(encoding="utf-8")


def _build_prompt(requirement: RequirementInput, template: str) -> str:
    hint_parts = []
    if requirement.source_type:
        hint_parts.append(f"Input type: {requirement.source_type.replace('_', ' ')}")
    if requirement.context:
        hint_parts.append(f"Additional context: {requirement.context}")

    hint = "\n".join(hint_parts)
    return (
        template
        .replace("{REQUIREMENT}", requirement.raw_text)
        .replace("{SOURCE_TYPE_HINT}", hint)
    )


def _clean_response(raw: str) -> str:
    # Strip markdown code fences if the model wraps its response despite instructions
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def generate(requirement: RequirementInput) -> TestDesignOutput:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set")

    model = os.environ.get("ANTHROPIC_MODEL", _DEFAULT_MODEL)
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = _load_system_prompt()
    user_message = _build_prompt(requirement, _load_user_template())

    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = _clean_response(message.content[0].text)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"AI returned invalid JSON: {exc}\n\nRaw response:\n{raw}"
        ) from exc

    output = TestDesignOutput(**data)
    return post_process(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.generator <requirement_file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    raw_text = path.read_text(encoding="utf-8")
    req = normalize(raw_text)
    output = generate(req)
    print(json.dumps(output.model_dump(), indent=2))
