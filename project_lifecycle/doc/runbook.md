# Runbook

Run commands from the `project_lifecycle/` directory.

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.11+ |
| Ollama | latest |
| Model | `llama3.1` |
| Docker/Compose | optional |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Model used by all agents |

## Local installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Usage

### Define a new project (with scaffolding)

```bash
python app_project_lifecycle.py \
  --mode define \
  --scaffold \
  --input "Build a SaaS invoicing platform with multi-currency support and PDF export." \
  --thread-id define-001 \
  --max-rounds 2 \
  --output /tmp/project_definition.md
```

### Evaluate an ongoing project

```bash
python app_project_lifecycle.py \
  --mode evaluate \
  --input "Our Django monolith lacks tests, has hardcoded database credentials, and the API is partially documented." \
  --thread-id eval-001 \
  --output /tmp/evaluation_report.md
```

### Audit a completed project

```bash
python app_project_lifecycle.py \
  --mode audit \
  --input "The invoicing platform is live. It handles billing and payments but has no admin UI, audit log, or rate limiting." \
  --thread-id audit-001 \
  --output /tmp/audit_report.md
```

### Debug with checkpoint history

```bash
python app_project_lifecycle.py --show-history
```

## Docker usage

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1

# define mode with scaffold
docker compose run --rm project_lifecycle \
  --mode define --scaffold \
  --input "Build a SaaS invoicing platform." \
  --output /tmp/project_definition.md

# evaluate mode
docker compose run --rm project_lifecycle \
  --mode evaluate \
  --input "Our Django monolith has no tests and hardcoded credentials."

# audit mode
docker compose run --rm project_lifecycle \
  --mode audit \
  --input "The invoicing platform is live but has no admin UI."
```

## Output

All modes produce a single structured Markdown document. The document is printed to stdout and, when `--output` is specified, also written to a file.

The document contains:
- Mode and closure metadata
- Mode-specific content (requirements + tech plan + docs for `define`; evaluation for `evaluate`; audit for `audit`)
- QA review history
- Final QA review
