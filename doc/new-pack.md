# Creating a new multi-agent pack

## Goal

Use this guide when adding a new multi-agent implementation to the workspace.

The repository is intentionally pack-based. New implementations should be added as sibling folders of `incident_response/`, not mixed into the workspace root.

## Creation workflow

1. Read [README.md](../README.md), [repository.md](repository.md), [agents.md](../agents.md), and the shared rules in [../skills/workflow.md](../skills/workflow.md).
2. Choose a pack name that describes the operational domain.
3. Create a dedicated folder at the workspace root.
4. Add the baseline pack files.
5. Document the pack before adding substantial implementation details.
6. Register the pack in [agents.md](../agents.md).
7. Run the repository validation script.

## Baseline files

Create the following files for each new pack:

```text
<pack_name>/
  README.md
  pyproject.toml
  Dockerfile
  docker-compose.yml
  doc/
    agents.md
    architecture.md
    runbook.md
    security.md
```

Add the runtime entrypoint that best fits the pack, for example `app_<pack>.py`.

## Documentation expectations

- `README.md` explains what the pack does and how to start it.
- `doc/agents.md` describes the agent nodes and contracts.
- `doc/architecture.md` describes graph topology and state.
- `doc/runbook.md` explains installation, execution, and Docker usage.
- `doc/security.md` documents input controls, boundaries, and tool constraints.

## Registration step

After creating the pack, add it to [agents.md](../agents.md) with:

- Pack path
- Short purpose statement
- Key files
- Links to pack docs

## Validation step

Run:

```bash
python scripts/validate_packs.py
python scripts/validate_packs.py --check-docker
```

If Docker is not available locally, run the first command and leave Docker validation to CI.
