# Agents

The architecture planning pack contains two debating agents connected in a LangGraph `StateGraph`.

## Infrastructure architect agent (`architect` node)

**Role:** Produce an end-to-end distributed architecture proposal from business requirements.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `business_requirement` | Business problem to solve |
| `qa_review` | Previous QA objections for the next revision |
| `round_number` | Current debate iteration |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `architect_proposal` | `str` | Markdown architecture proposal |
| `messages` | `list[BaseMessage]` | Proposal message for checkpoint traceability |

**Routing rule:** Always routes to `qa` after writing a proposal.

**Protections:**

- Fallback proposal exists when Ollama is unavailable.
- Proposal generation is scoped to architecture concerns only.

---

## Requirements and QA agent (`qa` node)

**Role:** Critically audit the architect proposal and decide whether the debate can stop.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `architect_proposal` | Candidate architecture from the architect agent |
| `business_requirement` | Original requirement for consistency checks |
| `round_number` / `max_rounds` | Debate control values |

**Output written to state:**

| Field | Type | Description |
|---|---|---|
| `qa_review` | `str` | Markdown audit result |
| `qa_approved` | `bool` | Consensus flag |
| `round_number` | `int` | Incremented review counter |
| `review_log` | `list[dict]` | Per-round debate evidence |

**Routing rule:**

- `qa_approved=True` → `finalize`.
- `qa_approved=False` and `round_number < max_rounds` → back to `architect`.
- `round_number >= max_rounds` → `finalize`.

**Protections:**

- Structured audit contract (`QAAudit`) validates approval, risks, and data model fields.
- Deterministic fallback audit prevents graph failure on LLM outages.
