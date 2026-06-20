# AgIA

AI agents for local multi-agent orchestration with LangGraph, LangChain, and Ollama.

All commands in this file assume your working directory is `incident_response/`.

For workspace structure and new pack creation rules, start at [../README.md](../README.md) and [../doc/new-pack.md](../doc/new-pack.md).

## Quick start

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve && ollama pull llama3.1
python app_multi_agent.py --show-history
```

Docker Compose:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm agia --show-history
```

## Documentation

| Document | Description |
|---|---|
| [doc/architecture.md](doc/architecture.md) | Graph topology, state schema, node contracts |
| [doc/agents.md](doc/agents.md) | Triage and Action agent specifications |
| [doc/runbook.md](doc/runbook.md) | Installation, execution, Docker, log interpretation |
| [doc/security.md](doc/security.md) | Input sanitisation, tool registry, security controls |

## Development

| Document | Description |
|---|---|
| [../agents.md](../agents.md) | Workspace pack catalog |
| [../skills/workflow.md](../skills/workflow.md) | AI-assisted development flow: explore → document → implement → validate |
| [../skills/testing.md](../skills/testing.md) | Exploration and validation rules |
| [../skills/documentation.md](../skills/documentation.md) | Documentation standards |
