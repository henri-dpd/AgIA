# Project lifecycle pack

Python multi-agent orchestration for the full software project lifecycle: initial definition, in-progress evaluation, and completed-project audit. Built with LangGraph and Ollama.

All commands in this file assume your working directory is `project_lifecycle/`.

## Modes

| Mode | Purpose |
|---|---|
| `define` | New project: elicits requirements, proposes technologies, creates an implementation plan, generates documentation outlines and optional scaffolding |
| `evaluate` | Ongoing project: identifies bad practices, measures requirements coverage, and proposes prioritised improvements |
| `audit` | Finished project: verifies whether objectives and requirements were met, finds quality and documentation gaps, recommends next steps |

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve && ollama pull llama3.1
python app_project_lifecycle.py --show-history
```

Define a new project with scaffolding:

```bash
python app_project_lifecycle.py \
  --mode define \
  --scaffold \
  --input "Build a SaaS invoicing platform with multi-currency support." \
  --output /tmp/project_definition.md
```

Evaluate an ongoing project:

```bash
python app_project_lifecycle.py \
  --mode evaluate \
  --input "Our monolith lacks tests and has hardcoded config; the API is partially documented." \
  --output /tmp/evaluation_report.md
```

Audit a completed project:

```bash
python app_project_lifecycle.py \
  --mode audit \
  --input "The invoicing platform is live. It handles billing and payments but has no admin UI or audit log." \
  --output /tmp/audit_report.md
```

Docker Compose:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm project_lifecycle \
  --mode define --scaffold \
  --input "Build a SaaS invoicing platform with multi-currency support."
```

## CLI reference

| Flag | Default | Description |
|---|---|---|
| `--input` | Built-in example | Project description or context |
| `--mode` | `define` | `define`, `evaluate`, or `audit` |
| `--scaffold` | off | Add project directory scaffolding to `define` output |
| `--thread-id` | `lifecycle-001` | LangGraph checkpoint identifier |
| `--max-rounds` | `2` | QA review round cap (1–3) |
| `--output` | — | Write final Markdown document to this file |
| `--show-history` | off | Print checkpoint metadata for debugging |

## Documentation

| Document | Description |
|---|---|
| [doc/agents.md](doc/agents.md) | Agent node contracts and routing rules |
| [doc/architecture.md](doc/architecture.md) | Graph topology and state model |
| [doc/runbook.md](doc/runbook.md) | Installation and operation |
| [doc/security.md](doc/security.md) | Safety constraints and boundaries |
