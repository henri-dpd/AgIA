# Exploration and validation rules

These rules define how contributors validate multi-agent packs in this repository. Automated tests are welcome, but exploratory validation is the default when a pack does not yet provide a test suite.

## General rules

- Start with a reproducible exploration scenario before adding or changing code.
- Prefer validation paths that run without an active Ollama instance; use the deterministic fallback mode when possible.
- If automated tests exist, keep them close to the code they validate or under the pack `tests/` directory.
- When adding tests, use scenario-driven names such as `test_<unit>_<condition>_<expected_outcome>`.
- No `time.sleep` in tests unless testing actual timing behaviour; use mocks instead.

## What to explore or test

| Layer | What |
|---|---|
| Input sanitisation | All injection patterns, control characters, oversized inputs, valid inputs |
| Pydantic models | Valid construction, invalid fields, boundary values, Validator rejection |
| Agent nodes | Happy path, error accumulation, routing decisions, fallback mode |
| Tool registry | Known tools resolve, unknown names are rejected |
| Graph routing | All routing conditions produce the correct next node |

For the incident response pack, a valid exploratory run should cover at least one input that routes to `action` and one that terminates in `triage`.

## Test structure

Use the Arrange–Act–Assert pattern:

```python
def test_triage_routes_to_action_when_cve_detected():
    # Arrange
    state = build_state(sanitized_input="CVE-2025-1337 on 10.0.0.1")

    # Act
    result = triage_node(state)

    # Assert
    assert result["triage_plan"].requires_action is True
```

## Mocking LLM calls

Use `unittest.mock.patch` to replace `ChatOllama` calls. Return a predictable `AIMessage` with valid JSON so the node's parsing logic is also exercised.

```python
from unittest.mock import MagicMock, patch

with patch("app_multi_agent.ChatOllama") as mock_llm:
    mock_llm.return_value.invoke.return_value = AIMessage(content='{"requires_action": true, ...}')
    ...
```

## Validation expectations

- Every documented behaviour in a pack `doc/` directory must be covered by either an automated test or a reproducible exploration scenario.
- Security constraints documented in a pack `doc/security.md` must be exercised by at least one negative validation path.
- When a pack gains automated tests, new code must not reduce the existing coverage baseline for that pack.

## Running validation

```bash
# Repository-wide pack validation
python scripts/validate_packs.py
python scripts/validate_packs.py --check-docker

# Exploratory CLI run
python app_multi_agent.py --show-history

# Targeted CLI run with explicit input
python app_multi_agent.py --input "CVE-2025-1337 on 10.20.30.40" --thread-id validation-001 --show-history

# Optional automated tests
python -m pytest
python -m pytest -v
python -m pytest --tb=short
```
