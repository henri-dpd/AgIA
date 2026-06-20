# Testing Rules

These rules apply to all tests in this repository, whether written by humans or AI agents.

## General rules

- Every public function, class method, and agent node must have at least one unit test.
- Tests must be runnable without an active Ollama instance; use the deterministic fallback mode.
- Test files live next to the code they test or under a `tests/` directory at the project root.
- Test names must describe the scenario: `test_<unit>_<condition>_<expected_outcome>`.
- No `time.sleep` in tests unless testing actual timing behaviour; use mocks instead.

## What to test

| Layer | What |
|---|---|
| Input sanitisation | All injection patterns, control characters, oversized inputs, valid inputs |
| Pydantic models | Valid construction, invalid fields, boundary values, Validator rejection |
| Agent nodes | Happy path, error accumulation, routing decisions, fallback mode |
| Tool registry | Known tools resolve, unknown names are rejected |
| Graph routing | All routing conditions produce the correct next node |

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

## Coverage expectations

- New code merged to `main` must not reduce overall coverage.
- Every documented behaviour in `doc/` must be traceable to at least one test.
- Security constraints documented in `doc/security.md` must each have an explicit negative test (i.e., test that the constraint rejects invalid input).

## Running tests

```bash
python -m pytest              # all tests
python -m pytest -v           # verbose output
python -m pytest --tb=short   # short tracebacks
```
