# AgIA Workspace

AgIA is a repository for multiple local multi-agent implementations. Each implementation lives in its own pack folder, while the workspace root keeps shared guidance, repository structure, and the pack catalog.

## Repository objective

- Keep several multi-agent projects in one workspace without mixing their runtime files.
- Document the repository structure clearly enough that new pack creation can follow the same pattern every time.
- Make validation and CI operate at the pack level instead of assuming a single root application.

## Repository layout

| Path | Purpose |
|---|---|
| `README.md` | Workspace overview and onboarding entry point |
| `doc/` | Repository-level documentation about structure and pack creation |
| `agents.md` | Workspace catalog of available multi-agent packs |
| `skills/` | Shared development, documentation, and validation rules |
| `scripts/` | Repository-level helper scripts, including pack validation |
| `incident_response/` | Current incident-response multi-agent pack |
| `devsecops/` | Full-cycle DevSecOps platform multi-agent pack |

## Current packs

See [agents.md](agents.md) for the pack registry.

## Key documents

| Document | Description |
|---|---|
| [doc/repository.md](doc/repository.md) | Repository purpose, structure, and conventions |
| [doc/new-pack.md](doc/new-pack.md) | How to create a new multi-agent pack in this workspace |
| [agents.md](agents.md) | Pack catalog and root-level agent metadata |
| [skills/workflow.md](skills/workflow.md) | Shared development workflow |
| [skills/testing.md](skills/testing.md) | Shared exploration and validation rules |
| [skills/documentation.md](skills/documentation.md) | Shared documentation rules |

## Development commands

Validate the repository structure and each pack:

```bash
python scripts/validate_packs.py
python scripts/validate_packs.py --check-docker
```

Work on the incident-response pack:

```bash
cd incident_response
python app_multi_agent.py --show-history
docker compose up -d ollama
docker compose run --rm agia --show-history
```

Work on the DevSecOps platform pack:

```bash
cd devsecops
python devsecops_platform.py . --show-report
docker compose up -d ollama
docker compose run --rm devsecops /workspace --show-report
```

## Adding a new pack

Before creating a new multi-agent implementation, read [doc/new-pack.md](doc/new-pack.md). The short version is:

1. Create a dedicated pack folder at the workspace root.
2. Put runtime code, Docker files, and pack-specific `doc/` inside that folder.
3. Register the pack in [agents.md](agents.md).
4. Keep root `doc/` for repository-level guidance only.
