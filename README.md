# AI Test Design Assistant

Transforms software requirement text into structured QA test design artifacts.

Built for QA engineers and engineering teams who need to move quickly from ambiguous requirements to testable scenarios.

## What it produces

Given requirement-like input — user stories, acceptance criteria, feature descriptions, or bug tickets — the tool generates:

- Positive test scenarios
- Negative test scenarios
- Edge cases
- Clarification questions
- Risk notes

Output is structured JSON (machine-readable) and Markdown (human-readable report).

## Architecture

Three concerns, cleanly separated:

| Layer | Responsibility |
|---|---|
| Input normalization | Deterministic. Cleans input, detects source type. No AI. |
| AI generation | Single call to configured provider (Anthropic or Ollama). Returns validated JSON. |
| Output validation | Enforces output contract. Explicit errors, no silent degradation. |

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) **or** [Ollama](https://ollama.com/) running locally

## Setup

```bash
git clone <repo-url>
cd ai-test-design-assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the environment template:

```bash
cp .env.example .env
```

### Running with Anthropic

Edit `.env`:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
```

The Anthropic model defaults to `claude-sonnet-4-6`. To override:

```
ANTHROPIC_MODEL=claude-sonnet-4-6
```

### Running with Ollama (local inference)

Install Ollama from [ollama.com](https://ollama.com/), then pull a model:

```bash
ollama pull qwen2.5:7b
```

Edit `.env`:

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

Ollama defaults to `http://localhost:11434`. To override:

```
OLLAMA_BASE_URL=http://localhost:11434
```

`qwen2.5:7b` is recommended for reliable JSON output. `llama3.1:8b` is a solid alternative if you already have it.

## Usage

Run the generator against any requirement file:

```bash
python -m src.generator examples/login_feature.txt
```

Output is JSON printed to stdout:

```json
{
  "positive_scenarios": ["..."],
  "negative_scenarios": ["..."],
  "edge_cases": ["..."],
  "clarification_questions": ["..."],
  "risks": ["..."]
}
```

To generate a Markdown report, use the reporter in Python:

```python
from pathlib import Path
from src.normalizer import normalize
from src.generator import generate
from src.reporter import generate_report, write_report

requirement = normalize(Path("examples/login_feature.txt").read_text())
output = generate(requirement)
report = generate_report(requirement, output)
write_report(report, Path("report.md"))
```

## Running tests

```bash
pytest
```

Tests run without an API key. The generator is not unit-tested — it makes live API calls.

## What this covers

- Pydantic data contracts for input and output
- Deterministic input normalization and source type detection
- AI generation via Anthropic API or Ollama local inference, selected by env var
- Deterministic post-processing: cleaning, deduplication, quality validation
- Markdown report generation with write-to-disk support

## What is intentionally not built

- A CLI with flags (`--output`, `--format`, etc.)
- Batch processing
- Web interface
- HTML or PDF output
- Gherkin / BDD formatting
- CI/CD integration
