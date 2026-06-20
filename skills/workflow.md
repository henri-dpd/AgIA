# AI-Assisted Development Workflow

This file defines the standard development flow for this repository. All contributors — human and AI — follow these rules.

## Core principle

> **Documentation → Tests → Implementation → Validation**

Every change starts with a written specification, moves to tests that encode that spec, and only then proceeds to implementation. Validation confirms the implementation satisfies both the tests and the documentation.

---

## Step 1 — Document first

Before writing any code, update or create the relevant document in `doc/`.

- Define the behaviour, contract, or change in plain English.
- Include inputs, outputs, invariants, error conditions, and security constraints.
- If the change affects an agent, update `doc/agents.md`.
- If the change affects the graph topology, update `doc/architecture.md`.
- If the change introduces new security rules, update `doc/security.md`.

**The documentation is the source of truth.** Code must match it, not the other way around.

---

## Step 2 — Write tests

Translate every documented behaviour into tests before touching implementation code.

- Cover the happy path, edge cases, and all documented error conditions.
- Test at the unit level where possible; use integration tests only for cross-component behaviour.
- Tests must be deterministic and runnable without Ollama (use the fallback mode).
- A failing test suite at this stage is expected and correct — the implementation does not exist yet.

See [testing.md](testing.md) for concrete rules.

---

## Step 3 — Implement

Write the minimum code that makes the tests pass.

- Follow existing patterns and types in the codebase.
- Do not add dependencies unless the documentation explicitly requires a new capability.
- Keep each change small and focused; prefer multiple small commits over one large one.
- Never silence tests or lower coverage thresholds to make the build green.

---

## Step 4 — Validate

Run the full validation suite and cross-check against the documentation.

```bash
# Run tests
python -m pytest

# Lint
python -m ruff check .
python -m ruff format --check .

# Type-check
python -m mypy app_multi_agent.py
```

Validation is complete when:

1. All tests pass.
2. The implementation matches every documented behaviour.
3. No documented behaviour is untested.
4. No security constraint listed in `doc/security.md` is violated.

---

## AI agent rules

When an AI agent (e.g., GitHub Copilot) drives any step:

- The agent **must** read the relevant `doc/` files before generating code.
- The agent **must** write or update tests before (or in the same commit as) implementation code.
- The agent **must** run the validation suite and fix failures before marking a task done.
- The agent **must not** modify test assertions to pass; it must fix the implementation.
- The agent **must** write all content in English, regardless of the language used in instructions.
