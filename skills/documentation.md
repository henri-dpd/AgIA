# Documentation Rules

These rules govern how documentation is written and maintained in this repository.

## Scope and location

| Content | File |
|---|---|
| Project overview, quick start | `README.md` |
| System design, data flow, state | `doc/architecture.md` |
| Agent descriptions and contracts | `doc/agents.md` |
| Installation, execution, Docker | `doc/runbook.md` |
| Security model and controls | `doc/security.md` |
| Development workflow | `skills/workflow.md` |
| Testing rules | `skills/testing.md` |
| Documentation rules | `skills/documentation.md` (this file) |

Do not put operational content in `README.md`. Keep it as a brief entry point that links to `doc/`.

## Language

All documentation in this repository is written in **English**, regardless of the language used in issues, PRs, or verbal instructions.

## Writing style

- Use plain, direct English. Avoid filler phrases ("As you can see…", "It is worth noting…").
- Prefer tables over long bullet lists for structured data (fields, options, mappings).
- Use fenced code blocks with a language tag for all code, commands, and configuration examples.
- Use `inline code` for file names, field names, class names, and CLI options.
- Use sentence case for headings, not title case.

## Accuracy rules

- Documentation describes what the system **does**, not what was intended or planned.
- When code changes a contract, update the relevant `doc/` file in the **same commit**.
- Do not document behaviour that is not yet implemented; use a clearly labelled `## Planned` section if a future section is needed.

## Mandatory sections per document type

### `doc/agents.md` entries

Each agent entry must include:

- **Role** — one-sentence description.
- **Input consumed from state** — table of field names, types, and purposes.
- **Output written to state** — table with the same structure.
- **Routing rule** — conditions that determine the next node.
- **Protections** — security or correctness constraints the node enforces.

### `doc/architecture.md`

Must stay in sync with `StateGraph` topology. Every node, edge, and routing condition must appear in the diagram and the edges table.

### `doc/security.md`

Every sanitisation step and security constraint must be listed. When a new constraint is added in code, add a corresponding row or section here and a matching negative test (see [testing.md](testing.md)).

## Review checklist for documentation changes

Before merging a documentation PR:

- [ ] All links to other `doc/` files resolve.
- [ ] All code examples are syntactically correct and runnable.
- [ ] Tables are aligned and render correctly in GitHub Markdown preview.
- [ ] New or changed behaviour is reflected in both `doc/` and tests.
- [ ] No Spanish (or other non-English) text was introduced.
