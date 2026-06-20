# Repository structure

## Purpose

This repository hosts multiple local multi-agent packs in one workspace. Each pack is a self-contained implementation with its own runtime files and operational documentation.

The root layer exists to answer three questions quickly:

1. What is this repository for?
2. How is it structured?
3. How should a new pack be added without breaking the pattern?

## Separation of concerns

| Layer | Owns |
|---|---|
| Workspace root | Pack catalog, repository documentation, shared skills, validation scripts, CI |
| Pack folder | Runtime code, packaging, Docker, pack `doc/`, pack-specific contracts |

## Required root files and folders

| Path | Requirement |
|---|---|
| `README.md` | Required |
| `doc/` | Required |
| `agents.md` | Required |
| `skills/` | Required |
| `scripts/` | Recommended |
| `.github/workflows/` | Recommended when CI is enabled |

## Required pack structure

Each pack should follow this layout:

```text
pack_name/
  README.md
  pyproject.toml
  Dockerfile
  docker-compose.yml
  app_<pack>.py or equivalent runtime entrypoint
  doc/
    agents.md
    architecture.md
    runbook.md
    security.md
```

Additional files are allowed when the pack needs them, but this baseline should remain stable across packs.

## Documentation rules by layer

| Layer | Allowed content |
|---|---|
| Root `README.md` | Repository objective, layout, onboarding |
| Root `doc/` | Repository conventions, pack creation guides |
| Root `agents.md` | Pack registry and workspace-level agent metadata |
| Pack `README.md` | Pack quick start and pack overview |
| Pack `doc/` | Pack runtime contracts, architecture, security, runbook |

Do not place pack-specific operational instructions in the root `doc/` unless they are examples used to explain the structure.

## Validation model

Validation is pack-aware. The root helper script [scripts/validate_packs.py](../scripts/validate_packs.py) discovers packs, checks required files, compiles Python sources, and can optionally run `docker compose config` per pack.

CI should call the root validation script instead of assuming a single top-level application.
