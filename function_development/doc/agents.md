# Agents

AgIA function development contains five LangGraph nodes organised as a planning-coding-validation pipeline with an audit gate.

## Planner agent (`planner` node)

**Role:** Analyse the function specification and the selected technology stack, produce a structured development plan with explicit acceptance criteria, and write the initial developer documentation.

**Input consumed from state:**

| Field | Type | Purpose |
|---|---|---|
| `request` | `FunctionRequest` | Raw function specification and inferred function name |
| `stack` | `str \| None` | Technology stack key used to load guidelines from `stacks/` |
| `audit_report` | `AuditReport \| None` | Auditor feedback when a plan rework is requested |
| `planner_attempts` | `int` | Current planning round |

**Output written to state:** `plan_artifact` (`PlanArtifact`)

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Short plan title |
| `context_summary` | `str` | What was understood from the specification |
| `stack_guidelines_applied` | `list[str]` | Which stack guidelines were incorporated |
| `specifications` | `str` | Detailed specification for the Coder agent |
| `acceptance_criteria` | `list[str]` | Criteria the implementation must satisfy |
| `documentation` | `str` | Docstring and usage notes for the function |

**Routing rule:** Always routes to `coder` after producing the plan.

**Protections:**

- Loads stack guidelines only from the `stacks/` directory; no external file access.
- Falls back to a passthrough plan when Ollama is unreachable.
- `planner_attempts` is bounded by `MAX_PLANNER_ROUNDS=2` to prevent infinite rework loops.

---

## Coder agent (`coder` node)

**Role:** Produce the target Python function and a matching pytest suite. When a plan is available, enriches the specification with acceptance criteria before generating code.

**Input consumed from state:**

| Field | Type | Purpose |
|---|---|---|
| `request` | `FunctionRequest` | Target function specification and inferred function name |
| `plan_artifact` | `PlanArtifact \| None` | Enriched specification and acceptance criteria from the Planner |
| `attempt` | `int` | Current correction round |
| `validation_report` | `ValidationReport \| None` | Previous pytest feedback for self-correction |
| `contract_report` | `ContractReport \| None` | Previous semantic compliance feedback for self-correction |

**Output written to state:** `artifact` (`GeneratedArtifact`)

| Field | Type | Description |
|---|---|---|
| `function_name` | `str` | Shared function symbol used by code and tests |
| `function_code` | `str` | Raw Python module for `subject.py` |
| `test_code` | `str` | Raw pytest module for `test_subject.py` |

**Routing rule:** Always routes to `tester` after generating both artifacts.

**Protections:**

- Generates implementation and tests in parallel from the same validated request.
- Combines pytest feedback and semantic compliance feedback into a single prompt.
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

- `success=True` → `validator`
- `success=False` and `attempt < MAX_CORRECTION_ROUNDS` with no `blocked_reason` → `coder`
- Security rejection or attempt budget exhausted → `END`

**Protections:**

- Runs AST-based validation before any subprocess execution.
- Writes generated files only inside a temporary directory.
- Executes `pytest` with a bounded timeout and captured output.

---

## Validator agent (`validator` node)

**Role:** Semantically verify that the generated implementation satisfies every acceptance criterion produced by the Planner agent. Provides structured compliance feedback to the Coder when criteria are unmet.

**Input consumed from state:**

| Field | Type | Purpose |
|---|---|---|
| `artifact` | `GeneratedArtifact` | Generated implementation to evaluate |
| `plan_artifact` | `PlanArtifact \| None` | Acceptance criteria to check against |

**Output written to state:** `contract_report` (`ContractReport`)

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | `True` when all acceptance criteria are met |
| `checked_criteria` | `list[str]` | Criteria that were evaluated |
| `failed_criteria` | `list[str]` | Criteria that the implementation did not satisfy |
| `feedback` | `str \| None` | Corrective guidance returned to the Coder agent |

**Routing rule:**

- `success=True` → `auditor`
- `success=False` and `attempt < MAX_CORRECTION_ROUNDS` → `coder`
- Attempt budget exhausted → `END`

**Protections:**

- Skips validation (approves automatically) when no `plan_artifact` is present.
- Falls back to approval when Ollama is unreachable.

---

## Auditor agent (`auditor` node)

**Role:** Act as a quality manager for the full pipeline. Review the plan, generated code, and contract validation result; verify best-practice compliance and scope adherence; approve the deliverable or request a plan rework.

**Input consumed from state:**

| Field | Type | Purpose |
|---|---|---|
| `plan_artifact` | `PlanArtifact \| None` | Original plan and specifications |
| `artifact` | `GeneratedArtifact` | Final generated implementation |
| `contract_report` | `ContractReport \| None` | Semantic validation result |
| `attempt` | `int` | Total correction rounds performed |

**Output written to state:** `audit_report` (`AuditReport`)

| Field | Type | Description |
|---|---|---|
| `approved` | `bool` | `True` when the deliverable meets all quality gates |
| `best_practices_violations` | `list[str]` | Stack or general best-practice issues found |
| `scope_violations` | `list[str]` | Cases where the implementation exceeds the specified scope |
| `requires_user_action` | `bool` | `True` when the auditor needs human input before proceeding |
| `user_action_description` | `str \| None` | Description of the required user action |
| `requires_plan_rework` | `bool` | `True` when the plan itself must be revised before retrying |
| `feedback` | `str \| None` | Guidance fed back to the Planner when `requires_plan_rework=True` |

**Routing rule:**

- `approved=True` → `END`
- `approved=False` and `requires_plan_rework=True` and `planner_attempts < MAX_PLANNER_ROUNDS` → `planner`
- Otherwise → `END` with `status=failed`

**Protections:**

- Auto-approves when no plan or contract report is present (passthrough mode).
- Falls back to passthrough approval when Ollama is unreachable.
- `requires_plan_rework` only routes back to `planner` within the `MAX_PLANNER_ROUNDS` budget.

---

## Registered tools

| Tool name | Description |
|---|---|
| `remediate_vulnerability` | Not used in this pack (incident response only) |

This pack has no registered action tools; the Coder generates code locally and the Tester runs it in a sandbox.
