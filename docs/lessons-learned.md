# Lessons Learned

Engineering observations from building AI Test Design Assistant.
Written as a post-build retrospective — not prescriptive rules, but real friction
points and decisions encountered during development.

---

## 1. Output validation cannot be delegated to the prompt

**What happened:** Initial prompt iterations instructed the model to return clean
items: no leading numbering, no markdown formatting, consistent phrasing. The
model complied inconsistently — different runs returned items prefixed with `1. `,
`- `, or `*`, or containing `**bold**` text, regardless of the instruction.

**What it means:** Prompt instructions are hints, not guarantees. For structural
requirements — format, length bounds, absence of specific characters — deterministic
post-processing is more reliable than prompt instruction. The prompt should focus
on content quality; cleaning should be a code concern.

**Practical implication:** Write post-processing for any output property that must
hold reliably across runs. Reserve prompt instructions for properties about content,
not format.

---

## 2. Validation failures should be explicit errors, not silent partial results

**What happened:** An early prototype returned whatever the AI produced, even if
some fields were missing or some items were too short. Downstream consumers received
partial output and failed in unpredictable ways — the reporter produced incomplete
sections with no obvious explanation.

**What it means:** Silent partial results are harder to debug than explicit failures.
An `OutputQualityError` with a clear message — "field 'risks' has 1 usable item
after cleaning (minimum required: 3)" — is immediately actionable. Partial results
propagated silently are not.

**Practical implication:** Define an explicit output contract and enforce it at
the boundary between AI output and the rest of the system. Raise explicitly when
the contract is violated.

---

## 3. Small local LLMs have a quality ceiling that prompt iteration cannot overcome

**What happened:** `llama3.2` (3.2B) returned valid JSON consistently but produced
shorter, more generic scenarios. Items like `"Invalid email format"` (22 chars,
just above the minimum threshold) passed validation but carried less analytical
value. `qwen2.5:7b` produced noticeably more specific output: scenarios grounded
in the requirement's stated conditions, clarification questions that identified
genuine specification gaps.

**What it means:** Model capacity affects output quality independently of prompt
quality. There is a point where prompt improvement stops helping and model selection
begins. Recognizing that ceiling early prevents wasted iteration on the wrong variable.

**Practical implication:** Test your prompt against the exact model you intend to
deploy. For this task, `qwen2.5:7b` is the minimum viable local model. Results
do not transfer reliably between model sizes or families.

---

## 4. Structured output requires structured prompting

**What happened:** An earlier version of the prompt described the expected output
in prose. Replacing the prose description with an explicit JSON schema example —
field names, list format, item characteristics — reduced structural deviation
more than any additional instruction text did.

**What it means:** LLMs calibrate better on examples than on abstract instructions.
Showing the model what valid output looks like is more effective than describing
it. Instruction text redundant with an example adds tokens without adding signal.

**Practical implication:** For any structured output requirement, include a concrete
schema example in the system prompt.

---

## 5. Prompt externalization enables iteration without code churn

**What happened:** The system prompt and user prompt template were revised several
times during development. Because they live in `src/prompts/` as plain text files,
each revision required no Python changes, no test reruns, and no risk of
accidentally affecting surrounding code.

**What it means:** Prompt iteration is a separate concern from code evolution.
Embedding prompts as Python strings couples them to code — it creates noise in
diffs, makes prompt history hard to read in git log, and raises the risk of
inadvertent changes during code edits.

**Practical implication:** Prompts belong in files. They should have their own
commit history, their own review context, and their own change frequency — which
is higher than code during early development.

---

## 6. Deterministic preprocessing reduces AI reasoning load

**What happened:** Early input was passed to the model with minimal cleaning.
Trailing whitespace, inconsistent line breaks, and copy-paste formatting artifacts
(excess blank lines, leading newlines) were visible in the prompt. Adding
deterministic normalization before the AI call produced more consistent output.

**What it means:** AI models do not fail on noisy input — they adapt to it. But
adapting to input variance consumes reasoning capacity that would otherwise go
toward content quality. Clean input produces better output without any prompt change.

**Practical implication:** Normalize input before the AI sees it. This is a free
quality improvement: one deterministic function, measurable consistency gain.

---

## 7. Omissions deserve the same documentation as decisions

**What happened:** Several features were considered and explicitly rejected:
retry logic, Gherkin output, batch processing, HTML reports, a CLI framework.
Without documentation, these read as gaps. With documentation, they read as
deliberate scope decisions.

**What it means:** Engineering maturity is demonstrated as much by what is chosen
not to build as by what is built. Documented omissions look like judgment.
Undocumented omissions look like unfinished work.

**Practical implication:** For every significant feature not implemented, write
one sentence explaining the reasoning. The absence of a feature is a decision —
document it like one.
