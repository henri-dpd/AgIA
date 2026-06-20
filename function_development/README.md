# AgIA function development

Local multi-agent orchestration pack for autonomous Python function delivery with a `Coding + Self-Correction Loop`.

All commands in this file assume your working directory is `function_development/`.

## Quick start

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve && ollama pull llama3.1
python app_function_development.py --show-history
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
| [doc/architecture.md](doc/architecture.md) | Graph topology, state schema, and correction loop |
| [doc/agents.md](doc/agents.md) | Coder and Tester agent contracts |
| [doc/runbook.md](doc/runbook.md) | Installation, execution, and log interpretation |
| [doc/security.md](doc/security.md) | Static safeguards, execution boundaries, and blocked operations |

## Development

| Document | Description |
|---|---|
| [../agents.md](../agents.md) | Workspace pack catalog |
| [../doc/new-pack.md](../doc/new-pack.md) | Pack creation rules |
| [../skills/workflow.md](../skills/workflow.md) | Shared development flow |
