# AI-Assisted Development Workflow

This file defines the standard development flow for this repository. All contributors — human and AI — follow these rules.

## Core principle

> **Exploration → Documentation → Implementation → Validation**

This workspace is organised as a collection of multi-agent packs. Each pack owns its own runtime files and `doc/` directory below its folder. The current implementation pack lives in `incident_response/`.

Every change starts with exploration of the target pack, then moves to documentation, implementation, and focused validation. Automated tests are optional in packs that are still exploratory; validation must still be reproducible.

---

## Step 1 — Explore first

Before changing code, inspect the target pack and confirm the real execution surface.

- Read the pack `README.md`, local `doc/` files, and the runtime entrypoint.
- Identify the narrowest owning file before editing.
- Prefer scenario exploration, CLI runs, or Docker runs over speculative changes.
- Record only implemented behaviour; do not infer missing capabilities from stale docs.

For the incident response pack, start in `incident_response/` and review `incident_response/README.md`, `incident_response/doc/`, and `incident_response/app_multi_agent.py`.

---

## Step 2 — Document

Before writing any code, update or create the relevant document in the target pack `doc/` directory.

- Define the behaviour, contract, or change in plain English.
- Include inputs, outputs, invariants, error conditions, and security constraints.
- If the change affects an agent, update the pack `doc/agents.md`.
- If the change affects the graph topology, update the pack `doc/architecture.md`.
- If the change introduces new security rules, update the pack `doc/security.md`.

**The documentation is the source of truth.** Code must match it, not the other way around.

---

## Step 3 — Implement

Write the minimum code that satisfies the documented behaviour.

- Follow existing patterns and types in the codebase.
- Do not add dependencies unless the documentation explicitly requires a new capability.
- Keep each change small and focused; prefer multiple small commits over one large one.
- Do not widen scope just to make validation easier.

---

## Step 4 — Validate

Run the narrowest reproducible validation available for the target pack and cross-check against the documentation.

```bash
# Scenario exploration
python app_multi_agent.py --show-history

# Optional automated checks when present
python -m pytest
python -m ruff check .
python -m ruff format --check .

# Type-check
python -m mypy app_multi_agent.py
```

Validation is complete when:

1. The explored behaviour matches the implementation.
2. The implementation matches every documented behaviour.
3. The chosen validation path is reproducible by another contributor.
4. No security constraint listed in the target pack `doc/security.md` is violated.

---

## AI agent rules

When an AI agent (e.g., GitHub Copilot) drives any step:

- The agent **must** explore the target pack before generating code.
- The agent **must** read the relevant pack `doc/` files before or while updating implementation.
- The agent **must** run a focused validation path and fix failures before marking a task done.
- The agent **must not** claim automated test coverage that does not exist.
- The agent **must** write all content in English, regardless of the language used in instructions.
