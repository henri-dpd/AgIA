# Security

## Input sanitisation pipeline

All user input is normalised **before** entering the graph. Nodes never consume `raw_input`.

| Step | What it does |
|---|---|
| `unicodedata.normalize("NFKC", …)` | Normalises Unicode to prevent homoglyph and lookalike attacks |
| `CONTROL_CHARS_RE` strip | Removes C0/C1 control characters |
| `TAG_RE` strip | Removes pseudo-role tags (`<system>`, `<assistant>`, `<tool>`, …) |
| `INJECTION_PATTERNS` redaction | Blanks classic injection phrases (`ignore previous instructions`, `reveal system prompt`, `developer mode`, `tool:`) |
| Length cap (`MAX_INPUT_LENGTH = 4 000`) | Truncates oversized payloads |

## Validated identifiers

`TriageDecision` and `RemediationRequest` run Pydantic v2 field validators on every structured exchange:

- `cve_id` — must match `CVE-\d{4}-\d{4,7}` (full match, uppercased).
- `asset_ip` — must parse as a valid IP address via `ipaddress.ip_address`.

## Tool registry and minimum privilege

- Every callable tool is registered in `ToolRegistry`. No dynamic tool resolution exists.
- Tools are sandboxed; they simulate remediation steps and do not expose `subprocess`, shell, arbitrary file access, or unconstrained network calls.
- `tool_choice="auto"` is used over the explicitly approved, small tool set.

## Protocol for adding a new tool

1. Define the tool with `@tool` and an explicit, Pydantic-validated input contract.
2. Validate all arguments before any side effect.
3. Restrict the tool to a single operational responsibility.
4. Register the tool in `ToolRegistry`.
5. Never expose shell, `subprocess`, arbitrary file paths, or unguarded network calls.
6. Document the new tool in `doc/agents.md`.

## Action agent constraints

- The Action agent returns a typed `ActionReport`; it cannot directly mutate graph state.
- The triage node translates the report into controlled state updates.
- `used_fallback=True` in an `ActionReport` indicates no LLM was involved; the result is deterministic and auditable.

## Graph-level safeguards

- `recursion_limit=10` prevents infinite retry loops at the graph level.
- `triage_attempts < MAX_TRIAGE_ATTEMPTS (2)` provides an earlier application-level guard on the `action → triage` feedback loop.
- `try/except` wraps every node; exceptions are appended to `errors` and do not crash the process.
