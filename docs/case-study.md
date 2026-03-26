# Case Study: Structuring QA Thinking Before Test Execution

## The Problem

A new feature requirement lands. Now what?

A QA engineer reads the requirement, identifies testable scenarios, considers
edge cases, writes test cases. For a single well-scoped requirement this takes
20–40 minutes of focused attention. For a poorly scoped requirement — missing
acceptance criteria, ambiguous failure behavior, undefined boundary conditions —
it takes longer and the output is lower quality.

The problems are consistent and predictable:

**Requirement ambiguity is invisible until you try to test it.** A requirement
that reads clearly as a product description often contains undefined behavior:
What happens on the third failed attempt? What constitutes a valid email? What
does "session expiry" mean if the user is actively typing?

**Negative and edge cases are routinely undertested.** Under time pressure, QA
engineers focus on positive paths and obvious failures. Boundary conditions,
concurrent state, and failure recovery paths are deprioritized or skipped.

**Clarification questions are asked late.** Requirement ambiguities are often
discovered after tests are written — sometimes after code is written. The cost
of a clarification question increases the further downstream it is asked.

**Risk assessment is ad hoc.** Whether a given requirement carries security,
integrity, or UX risk depends on who reviews it and what they happen to know.

---

## What This Tool Changes

**Before:**
```
Requirement → QA engineer reads → writes scenarios from memory →
edge cases missed → ambiguities discovered during test writing or execution
```

**After:**
```
Requirement → AI Test Design Assistant →
structured artifact: positive · negative · edge cases · clarification questions · risks
→ QA engineer reviews and validates
```

The tool runs before test design begins. Its output is a structured starting
point, not a final answer. A QA engineer reviewing five positive scenarios, five
negative scenarios, and three clarification questions is in a different position
than one starting from a blank page.

---

## Local vs Cloud Models: Honest Assessment

### Ollama — qwen2.5:7b (local)

**Strengths:**
- Zero cost, no API key, no network dependency
- Viable offline and on developer machines without cloud access
- Fast response on capable hardware

**Observed weaknesses:**
- Scenarios are less grounded in the specific requirement — tend toward generic
  QA descriptions rather than requirement-specific conditions
- Clarification questions sometimes ask about things already specified in the requirement
- Risk items name broader categories rather than specific failure modes

**Verdict:** Suitable for quick exploration and offline use. Output requires
closer review before being used as a team-facing artifact.

### Anthropic Claude — claude-sonnet-4-6 (cloud)

**Strengths:**
- Scenarios are grounded in the requirement's stated conditions, not generic templates
- Clarification questions identify genuine gaps in specification
- Risk items name specific failure modes: session token entropy, audit log integrity,
  rate limiting scope
- Consistent JSON output matching the schema across runs

**Weaknesses:**
- Requires API credits and network access

**Verdict:** Recommended when output will be shared with developers or product
stakeholders.

---

## Business Value

| Outcome | Impact |
|---|---|
| Negative and edge cases surfaced automatically | Reduces coverage gaps before test writing begins |
| Clarification questions generated early | Moves ambiguity discovery upstream, before code is written |
| Risk identification at requirement stage | Flags security and integrity concerns before design is locked |
| Consistent structured output | Provides a shared starting vocabulary for QA and development |
| Provider flexibility | Works offline with Ollama; production-grade with Claude |

---

## Limitations

**AI output is a starting point, not a final artifact.** Scenarios require review
by a QA engineer who knows the domain. The tool accelerates structuring, not judgment.

**Prompt quality determines output quality.** The current prompt was tuned for
user stories and acceptance criteria. Different domains may need prompt iteration
before output quality is reliable.

**Output validation enforces format, not correctness.** The post-processor checks
that output is structurally valid — correct item counts, length bounds, no duplicates.
It does not verify that scenarios are accurate, complete, or domain-appropriate.

**This is not a test case generator.** It produces scenario descriptions, not
executable tests. Converting scenarios to Playwright, pytest, or any test framework
is a separate step outside this tool's scope.

---

## Engineering Decisions

**Validation failure is explicit, not silent.**
If the AI returns output that fails the contract — too few scenarios, items that
are too short, malformed JSON — the tool raises explicitly rather than returning
partial results. Partial results returned silently are worse than a clear error:
they reach downstream consumers and fail in unpredictable ways.

**Source type detection is best-effort and never blocks.**
`source_type` is detected by keyword scoring and passed to the AI as a hint. If
detection is wrong or ambiguous, `source_type` is `None` and the tool proceeds.
A detection failure is not a reason to abort.

**Post-processing is deterministic and independent of the prompt.**
The post-processor can be improved without touching the prompt, and the prompt
can be changed without affecting post-processing. Both concerns evolve independently.

---

## Tradeoffs Accepted

**No retry on malformed AI responses.**
Malformed JSON is surfaced as an explicit error rather than retried. A retry loop
masks the failure pattern. Characterizing the failure is necessary before the fix
can be chosen.

**No executable test generation.**
Generating Playwright or pytest code from scenario descriptions changes the output
contract, increases the surface for hallucination, and creates a direct dependency
on specific test frameworks. Scenario descriptions as output is a deliberate scope limit.

**System prompt and user template in separate files.**
The system prompt defines the reasoning rubric; the user template handles requirement
injection. Keeping them separate allows rubric iteration without touching the
injection mechanism.
