# Agents

This workspace is organised as a catalog of multi-agent packs. Shared guidance stays at the root, while each pack keeps its runtime files and operational documentation inside its own folder.

## Available packs

| Pack | Purpose | Key files |
|---|---|---|
| `incident_response/` | Local incident-response orchestration with LangGraph, LangChain, and Ollama | `incident_response/README.md`, `incident_response/doc/agents.md`, `incident_response/app_multi_agent.py` |

## Workspace conventions

- The workspace root keeps repository-level guidance, not pack runtime code.
- Every multi-agent implementation must live in its own top-level pack folder.
- Every pack must keep its operational documentation inside its own `doc/` directory.
- New packs must be registered here as soon as they are scaffolded.

## Required pack baseline

Each registered pack should provide:

- `README.md`
- `pyproject.toml`
- `Dockerfile`
- `docker-compose.yml`
- A runtime entrypoint such as `app_<pack>.py`
- `doc/agents.md`
- `doc/architecture.md`
- `doc/runbook.md`
- `doc/security.md`

## Incident response pack

The current implementation lives in `incident_response/`.

- Agent contracts: [incident_response/doc/agents.md](incident_response/doc/agents.md)
- Architecture: [incident_response/doc/architecture.md](incident_response/doc/architecture.md)
- Runbook: [incident_response/doc/runbook.md](incident_response/doc/runbook.md)
- Security controls: [incident_response/doc/security.md](incident_response/doc/security.md)

When a new multi-agent pack is added, register it here and keep its pack-specific contracts inside that folder.

For the full repository structure and pack-creation guide, see [doc/repository.md](doc/repository.md) and [doc/new-pack.md](doc/new-pack.md).
