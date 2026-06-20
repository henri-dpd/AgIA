# Agents

The project lifecycle pack contains six specialist agents connected in a LangGraph `StateGraph`. The active agent chain depends on the chosen operating mode.

---

## Requirements analyst agent (`requirements_analyst` node)

**Mode:** `define`

**Role:** Extract objectives, functional and non-functional requirements, scope, out-of-scope items, and constraints from the project description.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `project_description` | Raw project brief from the operator |
| `qa_review_doc` | Previous QA feedback for iterative refinement |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `requirements_doc` | `str` | Markdown requirements analysis |
| `messages` | `list[BaseMessage]` | Checkpoint traceability |

**Pydantic contract:** `RequirementsAnalysis` — validates objectives, functional/non-functional requirements, scope, out-of-scope, constraints.

**Protections:** Deterministic fallback when Ollama is unavailable or returns unparseable JSON.

---

## Tech planner agent (`tech_planner` node)

**Mode:** `define`

**Role:** Propose a primary technology stack, supporting tools, architecture pattern with Mermaid diagram, rationale, implementation phases with durations, and implementation risks.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `project_description` | Project brief |
| `requirements_doc` | Extracted requirements for alignment |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `tech_plan_doc` | `str` | Markdown technology proposal and implementation plan |
| `messages` | `list[BaseMessage]` | Checkpoint traceability |

**Pydantic contract:** `TechAndPlanProposal` — validates stack, tools, pattern, Mermaid diagram, rationale, phases, duration, risks.

**Protections:** Deterministic fallback proposal using FastAPI/PostgreSQL/Redis baseline.

---

## Documentation generator agent (`documentation_generator` node)

**Mode:** `define`

**Role:** Produce an initial `agents.md` outline, a skills file list, and a README structure for the planned project. When `--scaffold` is requested, also produces a suggested directory scaffolding.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `project_description` | Project brief |
| `requirements_doc` | Requirements summary for context |
| `tech_plan_doc` | Technology plan summary for context |
| `scaffold_requested` | Whether to include directory scaffolding |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `documentation_outline` | `str` | Markdown documentation and scaffolding outline |
| `messages` | `list[BaseMessage]` | Checkpoint traceability |

**Protections:** Fallback documentation template used when LLM returns empty content.

---

## Project evaluator agent (`project_evaluator` node)

**Mode:** `evaluate`

**Role:** Critically assess an in-progress project. Identifies overall status, requirements coverage, bad practices, improvement suggestions, priority actions, and risks.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `project_description` | Description of the project as it stands |
| `qa_review_doc` | Previous QA feedback for iterative refinement |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `evaluation_doc` | `str` | Markdown evaluation report |
| `messages` | `list[BaseMessage]` | Checkpoint traceability |

**Pydantic contract:** `ProjectEvaluation` — validates status, coverage, bad practices, suggestions, priority actions, risks.

**Protections:** Deterministic fallback evaluation covers common anti-patterns.

---

## Completion auditor agent (`completion_auditor` node)

**Mode:** `audit`

**Role:** Audit a finished project: determine which objectives were and were not met, identify missing features, quality gaps, documentation gaps, and produce a final production-readiness verdict with recommended next steps.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `project_description` | Description of the finished project |
| `qa_review_doc` | Previous QA feedback for iterative refinement |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `audit_doc` | `str` | Markdown completion audit report |
| `messages` | `list[BaseMessage]` | Checkpoint traceability |

**Pydantic contract:** `CompletionAudit` — validates met/unmet objectives, missing features, quality/documentation gaps, next steps, final verdict.

**Protections:** Deterministic fallback audit covers common completion gaps.

---

## QA reviewer agent (`qa_reviewer` node)

**Mode:** all

**Role:** Assess the completeness, accuracy, and actionability of the active mode's output. Approves or requests a refinement round.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `mode` | Selects which output fields to review |
| `round_number` / `max_rounds` | Loop control |
| `requirements_doc` / `tech_plan_doc` / `documentation_outline` | Reviewed in `define` mode |
| `evaluation_doc` | Reviewed in `evaluate` mode |
| `audit_doc` | Reviewed in `audit` mode |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `qa_review_doc` | `str` | Markdown QA review |
| `qa_approved` | `bool` | Approval gate |
| `round_number` | `int` | Incremented review counter |
| `review_log` | `list[dict]` | Per-round review evidence |

**Routing rule:**

- `qa_approved=True` or `round_number >= max_rounds` → `finalizer`.
- Otherwise → back to the mode's primary analysis node for refinement.

**Protections:**

- `QAReview` Pydantic contract validates approval, summary, gaps, suggestions.
- Auto-approved when `max_rounds` is reached to prevent infinite loops.
- Deterministic fallback review prevents graph failure on LLM outages.
