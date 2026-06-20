# Runbook

Run all commands from the `incident_response/` directory unless noted otherwise.

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.11+ |
| Docker Engine | 24+ (container mode only) |
| Docker Compose v2 | (container mode only) |
| Ollama | latest (local or container) |
| Model | `llama3.1` |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Model name |
| `LOG_LEVEL` | `INFO` | Python log level |

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
# Demo run with embedded prompt
python app_multi_agent.py --show-history

# Explicit payload
python app_multi_agent.py \
  --input "Critical audit finding: CVE-2025-1337 detected on 10.20.30.40 after patch drift analysis." \
  --thread-id incident-001 \
  --show-history

# Debug verbosity
python app_multi_agent.py --log-level DEBUG --show-history
```

## Docker — app against host Ollama

```bash
# Start host Ollama
ollama serve && ollama pull llama3.1

docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.1 \
  agia-multi-agent:latest \
  --input "CVE-2025-1337 on 10.20.30.40" \
  --thread-id docker-001 \
  --show-history
```

## Docker Compose — app + Ollama

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm agia \
  --input "CVE-2025-1337 on 10.20.30.40" \
  --thread-id compose-001 \
  --show-history
docker compose down
```

## Input format

Free-form text with operational evidence. Recommended fields:

- CVE identifier: `CVE-YYYY-NNNN`
- Affected asset IP
- Severity indicator (`critical`, `high`, `medium`, `low`)
- Brief incident or audit context

## Reading the output

### `Final State`

| Field | Meaning |
|---|---|
| `sanitized_input` | Input actually consumed by the graph |
| `triage_plan` | Structured Triage agent decision |
| `action_report` | Structured Action agent result |
| `status` | `completed` or `error` |

### `Latest Checkpoint`

- `next=()` → graph finished.
- `status=completed` → resolved successfully.
- `status=error` → safe failure or invalid input.

### `Checkpoint History`

Ordered node-transition log. A return to `triage` means a controlled re-triage was triggered.

### Ollama connectivity messages

- `Ollama triage unavailable` / `Ollama action execution unavailable` → endpoint unreachable; deterministic safe fallback active. No LLM-assisted decision was made.

## Inspecting checkpoints in Python

```python
config = {"configurable": {"thread_id": "incident-001"}, "recursion_limit": 10}
state   = graph.get_state(config)
history = list(graph.get_state_history(config))

# Examine key fields
print(state.values["triage_plan"])
print(state.values["action_report"])
print(state.values["errors"])
print(state.next)   # () when finished

# Walk messages
for msg in state.values["messages"]:
    print(type(msg).__name__, msg.content)
```
