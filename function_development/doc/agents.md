# Agents

AgIA function development contains two LangGraph nodes that collaborate on Python function delivery and self-correction.

## Coder agent (`coder` node)

**Role:** Produce the target Python function and a matching pytest suite from the shared function specification.

**Input consumed from state:**

| Field | Type | Purpose |
|---|---|---|
| `request` | `FunctionRequest` | Target function specification and inferred function name |
| `attempt` | `int` | Current correction round |
| `validation_report` | `ValidationReport \| None` | Previous pytest feedback reused for self-correction |

**Output written to state:** `artifact` (`GeneratedArtifact`)

| Field | Type | Description |
|---|---|---|
| `function_name` | `str` | Shared function symbol used by code and tests |
| `function_code` | `str` | Raw Python module for `subject.py` |
| `test_code` | `str` | Raw pytest module for `test_subject.py` |

**Routing rule:** Always routes to `tester` after generating both artifacts.

**Protections:**

- Generates implementation and tests in parallel from the same validated request.
- Reuses only explicit pytest feedback from state; it does not read external files.
- Prompts prohibit shell, network, and dynamic-code execution APIs.

---

## Tester agent (`tester` node)

**Role:** Reject unsafe generated code, execute pytest in an isolated temporary directory, and decide whether another correction round is required.

**Input consumed from state:**

| Field | Type | Purpose |
|---|---|---|
| `artifact` | `GeneratedArtifact` | Generated implementation and tests |
| `attempt` | `int` | Current correction round |

**Output written to state:** `validation_report` (`ValidationReport`)

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | `True` when pytest exits with status 0 |
| `exit_code` | `int \| None` | Subprocess exit code when pytest runs |
| `stdout` | `str` | Captured pytest STDOUT |
| `stderr` | `str` | Captured pytest STDERR |
| `feedback` | `str \| None` | Failure summary returned to the Coder agent |
| `blocked_reason` | `str \| None` | Security rejection reason when execution is denied |

**Routing rule:**

- `success=True` → `END`
- `success=False` and `attempt < 4` with no `blocked_reason` → `coder`
- Security rejection or attempt budget exhausted → `END`

**Protections:**

- Runs AST-based validation before any subprocess execution.
- Writes generated files only inside a temporary directory.
- Executes `pytest` with a bounded timeout and captured output.
