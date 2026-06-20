# Architecture planning pack

Python multi-agent orchestration for conceptual system design, architecture planning, and technical specification generation using LangGraph and Ollama.

All commands in this file assume your working directory is `architecture_planning/`.

## Quick start

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve && ollama pull llama3.1
python architecture_planner.py --show-history
```

Docker Compose:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm architecture_planner --show-history
```

## Documentation

| Document | Description |
|---|---|
| [doc/agents.md](doc/agents.md) | Architect and QA agent contracts |
| [doc/architecture.md](doc/architecture.md) | Debate loop topology and state model |
| [doc/runbook.md](doc/runbook.md) | Installation and operation |
| [doc/security.md](doc/security.md) | Safety constraints and boundaries |
