# Agents

AgIA contains two agent nodes connected in a `StateGraph`. Both agents share a typed state and communicate only through structured Pydantic models.

## Triage agent (`triage` node)

**Role:** Analyse sanitised input and decide whether an action is warranted.

**Input consumed from state:**

| Field | Purpose |
|---|---|
| `sanitized_input` | Normalised incident report |
| `errors` | Previous node errors (informs retry reasoning) |
| `messages` | Conversation history |

**Output written to state:** `triage_plan` (`TriageDecision`)

| Field | Type | Description |
|---|---|---|
| `cve_id` | `str \| None` | Validated CVE identifier |
| `asset_ip` | `str \| None` | Validated affected asset IP |
| `severity` | enum | `critical`, `high`, `medium`, `low`, `unknown` |
| `strategy` | `str` | Recommended remediation strategy (10–500 chars) |
| `rationale` | `str` | Reasoning behind the decision (10–1 000 chars) |
| `requires_action` | `bool` | Whether the Action agent should execute |
| `confidence` | `float` | Decision confidence score [0.0, 1.0] |
| `escalation_reason` | `str \| None` | Human-readable reason when escalating |

**Routing rule:**

- `requires_action=True` → `action` node
- `requires_action=False` → `END`

**Protections:**

- Only reads `sanitized_input`; raw input is never visible to the agent.
- Produces a fully validated Pydantic model; free-form strings are length-capped.

---

## Action agent (`action` node)

**Role:** Execute a remediation action using allowed tools, or produce a safe deterministic result when the LLM is unavailable.

**Input consumed from state:** `triage_plan` (`TriageDecision`)

**Output written to state:** `action_report` (`ActionReport`)

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | Whether the action succeeded |
| `executed_tool` | `str \| None` | Name of the tool that was called |
| `sandboxed` | `bool` | Always `True`; actions are never live |
| `used_fallback` | `bool` | `True` when Ollama was unreachable |
| `summary` | `str` | Human-readable result summary |
| `output` | `str` | Detailed tool output |
| `commands` | `list[str]` | Commands that would have been run |

**Routing rule:**

- Success or retries exhausted → `END`
- Safe failure with `triage_attempts < MAX_TRIAGE_ATTEMPTS` → back to `triage`

**Protections:**

- Tool calls are resolved only from `ToolRegistry`; no dynamic dispatch.
- The node does not mutate state directly; it returns an `ActionReport`.
- `used_fallback=True` signals an auditable, deterministic path with no LLM involvement.

---

## Registered tools

| Tool name | Description |
|---|---|
| `simulate_patch_application` | Simulates applying a patch for the given CVE on an asset |
| `simulate_network_isolation` | Simulates isolating an asset from the network |
| `simulate_log_collection` | Simulates collecting forensic logs from an asset |

To add a new tool, follow the protocol in [doc/security.md](doc/security.md#protocol-for-adding-a-new-tool).
