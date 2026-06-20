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
| `OLLAMA_MODEL` | `llama3.1` | Model used by the Coder agent |
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
```

## Docker Compose

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm agia \
  --spec "Implement def is_palindrome(text: str) -> bool that ignores spaces and case." \
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

`Final state` shows the last generated artifact, the latest validation report, the attempt count, and the terminal status.

### `Latest checkpoint`

- `next=()` means the graph has finished.
- `status=completed` means pytest passed.
- `status=failed` means the graph stopped because of a security block or because four rounds were exhausted.

### `Checkpoint history`

Each line represents one saved state. Repeated `attempt` values do not occur; every return to `coder` increments the correction round.

### Common failure signals

- `Generated function failed security validation` → the static scanner blocked unsafe code before pytest.
- `Pytest reported at least one failure` → the traceback was returned to the Coder agent for the next round.
- `Pipeline execution failed` in logs → an unexpected runtime error occurred outside the normal correction loop.
