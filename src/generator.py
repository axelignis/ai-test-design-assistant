"""
AI generation layer.

Responsibility: take a normalized RequirementInput, call the configured LLM
provider, and return a validated TestDesignOutput. Nothing else.

Provider is selected via the LLM_PROVIDER environment variable:
    LLM_PROVIDER=anthropic  (default)
    LLM_PROVIDER=ollama

Entry point:
    python -m src.generator <requirement_file>
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from .models import RequirementInput, TestDesignOutput
from .normalizer import normalize
from .postprocessor import post_process

load_dotenv()

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.txt"
_USER_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "test_design.txt"
_DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
_DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"


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


def _call_anthropic(system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set")

    model = os.environ.get("ANTHROPIC_MODEL", _DEFAULT_ANTHROPIC_MODEL)
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


def _call_ollama(system_prompt: str, user_message: str) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["message"]["content"]


def generate(requirement: RequirementInput) -> TestDesignOutput:
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    system_prompt = _load_system_prompt()
    user_message = _build_prompt(requirement, _load_user_template())

    if provider == "anthropic":
        raw_text = _call_anthropic(system_prompt, user_message)
    elif provider == "ollama":
        raw_text = _call_ollama(system_prompt, user_message)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider!r}. Supported values: anthropic, ollama"
        )

    raw = _clean_response(raw_text)

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
