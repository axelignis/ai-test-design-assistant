# Architecture

## Design Philosophy

Three independent layers with unidirectional data flow. Each layer communicates
through typed contracts defined in `src/models.py`. No layer knows about layers
beyond its immediate neighbor.

The hard constraint: **the normalizer and post-processor have zero AI dependency
and must work offline.** A normalizer that calls an LLM is not a normalizer — it
is a coupled system that fails for two unrelated reasons and cannot be tested
in isolation.

---

## Pipeline

```
Raw requirement text  →  Normalizer  →  AI Generation  →  Post-Processor  →  Reporter
(string / file)          (Python)        (Python)           (Python)           (Python)
```

### Layer Responsibilities

| Layer | Input | Output | Dependency |
|---|---|---|---|
| Normalizer | Raw text string | `RequirementInput` | stdlib only |
| AI Generation | `RequirementInput` | raw JSON string | LLM provider |
| Post-Processor | `TestDesignOutput` (raw) | `TestDesignOutput` (clean) | stdlib only |
| Reporter | `RequirementInput` + `TestDesignOutput` | Markdown string | stdlib only |

---

## Data Contracts

Both contracts live in `src/models.py`. This file is the only shared dependency
across layers — if it changes, every layer is affected.

**RequirementInput** — produced by the normalizer, consumed by AI generation:

```python
class RequirementInput(BaseModel):
    raw_text: str
    source_type: Optional[Literal["user_story", "acceptance_criteria",
                                   "feature_description", "bug_ticket"]] = None
    context: Optional[str] = None
```

**TestDesignOutput** — produced by AI generation, cleaned by the post-processor,
consumed by the reporter:

```python
class TestDesignOutput(BaseModel):
    positive_scenarios: List[str]
    negative_scenarios: List[str]
    edge_cases: List[str]
    clarification_questions: List[str]
    risks: List[str]
```

---

## Deterministic vs AI Responsibilities

**Deterministic (no AI, testable in isolation):**

- Input cleaning — whitespace normalization, excess blank line collapse
- Source type detection — keyword scoring across four input categories
- Output cleaning — strips leading numbering and inline markdown per item
- Deduplication — normalized comparison (case-insensitive, punctuation-stripped) per field
- Item length validation — 20–300 character bounds per item
- Field count validation — 3–10 items per field, explicit error on violation
- Report formatting — Markdown structure, section headings, blockquote snapshot

**AI (single call per run):**

- Scenario generation — positive, negative, edge cases
- Question generation — clarification questions
- Risk identification — specific failure modes and specification gaps

Everything before and after the AI call is deterministic and independently testable.
The test suite runs to completion without an API key.

---

## Why Post-Processing Exists

AI models do not consistently produce clean output even when explicitly instructed.
Common deviations observed across runs:

- **Leading numbering:** `"1. User logs in..."` instead of `"User logs in..."`
- **Inline markdown:** `"User **must** provide..."` in what should be plain text
- **Short filler items:** items that pass JSON parsing but carry no analytical value
- **Near-duplicates:** minor phrasing variants of the same scenario
- **Markdown fences:** the model wraps its JSON in ` ```json ``` ` despite instructions

The post-processor handles all of these deterministically. Prompt improvements and
cleaning logic can change independently — they are separate concerns.

---

## Key Design Decisions

### Prompt externalization

System and user prompt templates live in `src/prompts/`, not in Python source.
The system prompt (`system.txt`) defines the reasoning rubric and output rules.
The user template (`test_design.txt`) handles requirement injection. Both were
revised several times during development without touching any Python code.

### Provider as a routing function, not a framework

`generate()` routes to `_call_anthropic()` or `_call_ollama()` based on
`LLM_PROVIDER`. No abstract base class, no registry, no framework. Two functions
and an if/else. Adding a provider means one function and one branch. No other
files change.

### Ollama uses stdlib urllib

The Ollama path uses only `urllib.request` from stdlib. When `LLM_PROVIDER=ollama`,
the `anthropic` package is never imported. No extra dependency is declared or loaded.

### generate_report() and write_report() are separate

`generate_report()` returns a string. `write_report()` takes that string and
persists it. The formatting logic is testable without filesystem side effects.
The write destination can change without touching formatting.

---

## What Was Not Built

**No CLI framework (argparse, click, typer):**
A single `sys.argv[1]` path argument is sufficient at this scope. Frameworks add
dependency weight and documentation overhead for marginal ergonomic gain.

**No retry logic on AI calls:**
Malformed JSON surfaces as a `json.JSONDecodeError`. A retry loop masks the failure
mode. The right fix is prompt hardening or model selection — chosen after observing
the failure, not before.

**No HTML or PDF output:**
Markdown renders natively in GitHub, Notion, Confluence, and most internal tooling.
It requires no build step and no viewer dependency.

**No batch processing:**
The current design processes one requirement at a time. Both `generate()` and
`generate_report()` are callable in a loop — batch support belongs in a future
entry point, not in the current layer design.
