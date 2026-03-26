# ai-test-design-assistant

## Purpose

Transform software requirement input into structured QA test design artifacts.

This tool is for QA engineers and engineering teams who need to move quickly
from ambiguous requirements to testable scenarios. It is not a chatbot, a
test case spammer, or a general AI demo.

## What This Tool Produces

Given requirement-like input (user stories, acceptance criteria, feature
descriptions, bug tickets), the tool generates:

- Positive test scenarios
- Negative test scenarios
- Edge cases
- Clarification questions
- Risk notes

## Architecture: Three Concerns

1. **Input normalization** — deterministic, no AI. Cleans and prepares input.
2. **AI generation** — single responsibility. Takes normalized input, returns structured response.
3. **Output validation** — enforces the output contract. Explicit failures, no silent degradation.

AI is augmentation, not replacement. QA judgment is encoded in the prompt.

## Output Contract

All five output fields are required. If the AI response does not conform to
the schema, the tool raises explicitly rather than returning partial results.

## Stack

- Python 3.11+
- Pydantic — input and output data contracts
- Anthropic SDK — AI client (client is injected, not hardcoded globally)
- External prompt files — prompts live in `src/prompts/`, not embedded in code
- JSON — primary machine-readable output format

## Engineering Rules

- No `utils.py`. Every module has a clear responsibility.
- Prompts are files, not strings in code. They evolve independently.
- `source_type` is optional and never blocks execution.
- Validation failures are explicit errors, never silent partial results.
- No abstraction without an immediate use case.
- Prefer simple over clever. Prefer clear over fancy.
