# Runbook

Run all commands from the `function_development/` directory unless noted otherwise.

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.11+ |
| Docker Engine | 24+ (container mode only) |
| Docker Compose v2 | (container mode only) |
| Ollama | latest |
| Model | `llama3.1` |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Model used by all Ollama-backed agents |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Local installation

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Start Ollama and pull the model:

```bash
ollama serve
ollama pull llama3.1
```

## Running locally

```bash
# Demo run with the embedded specification
python app_function_development.py --show-history

# Pass the function specification directly
python app_function_development.py \
  --spec "Implement def clamp(value: int, lower: int, upper: int) -> int. Raise ValueError when lower > upper and return the bounded integer otherwise." \
  --thread-id function-dev-001 \
  --show-history

# Pass the specification from a file
python app_function_development.py \
  --spec-file ./examples/spec.txt \
  --thread-id function-dev-002 \
  --show-history

# Pass a technology stack for context-aware planning
python app_function_development.py \
  --spec "Implement def clamp(value: int, lower: int, upper: int) -> int." \
  --stack python \
  --thread-id function-dev-003 \
  --show-history
```

## Available `--stack` values

| Value | Technology |
|---|---|
| `python` | Python (standard library and ecosystem) |
| `typescript` | TypeScript |
| `javascript` | JavaScript (ES modules, CommonJS) |
| `csharp-dotnet` | C# / .NET |
| `react` | React |
| `nextjs` | Next.js |
| `angular` | Angular |
| `nodejs` | Node.js |
| `nestjs` | NestJS |
| `aws` | AWS cloud services |

When `--stack` is provided, the Planner agent loads best-practice guidelines from `stacks/{stack}/` before producing the development plan.

## Docker Compose

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm agia \
  --spec "Implement def is_palindrome(text: str) -> bool that ignores spaces and case." \
  --stack python \
  --thread-id function-dev-docker \
  --show-history
docker compose down
```

## What to provide in the function specification

For the most stable results, include:

- The exact Python signature (`def ...`).
- Expected return value and data types.
- Error conditions and exceptions.
- Boundary conditions and edge cases.
- Any constraints such as standard-library-only requirements.

## Reading the terminal logs

### Structured output

`Final state` shows the last generated artifact, the latest validation report, the plan artifact, the audit report, the attempt count, and the terminal status.

### `Latest checkpoint`

- `next=()` means the graph has finished.
- `status=completed` means pytest passed and the Auditor approved the deliverable.
- `status=failed` means the graph stopped because of a security block, because the attempt budget was exhausted, or because the Auditor rejected without a rework budget.
- `plan=<title>` shows the Planner's plan title.
- `audit_approved=True/False` shows the Auditor's final decision.

### `Checkpoint history`

Each line represents one saved state. `planner_attempts` increments each time the Planner runs; `attempt` increments each time the Coder runs.

### Common failure signals

- `Generated function failed security validation` → the static scanner blocked unsafe code before pytest.
- `Pytest reported at least one failure` → the traceback was returned to the Coder agent for the next round.
- `Contract validation failed` → the Validator found unmet acceptance criteria; the Coder will retry.
- `Audit failed` → the Auditor found quality issues; check `audit_report.best_practices_violations`.
- `Pipeline execution failed` in logs → an unexpected runtime error occurred outside the normal correction loop.
