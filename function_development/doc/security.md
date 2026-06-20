# Security

## Execution boundaries

The pack never executes generated code directly from memory. The Tester agent first validates raw Python source, then writes files into a temporary directory, and finally launches `pytest` as a subprocess with captured output and a fixed timeout.

## Static validation rules

The `SecurityValidator` parses both generated modules with `ast` before execution.

| Control | What it blocks |
|---|---|
| Blocked imports | `os`, `subprocess`, `socket`, `httpx`, `requests` |
| Blocked calls | `eval`, `exec`, `compile`, `__import__`, `breakpoint`, `os.system`, `os.popen`, and `subprocess.*` execution helpers |
| Syntax validation | Rejects malformed Python before any subprocess starts |

## Temporary workspace policy

- Generated files are written only to a fresh `TemporaryDirectory`.
- The workspace is deleted automatically after each validation run.
- The pack does not persist generated code unless the caller explicitly copies it from the final state output.

## Subprocess controls

- The tester executes only `python -m pytest test_subject.py -q --maxfail=1`.
- `stdout` and `stderr` are always captured and returned to state.
- A hard timeout (`30` seconds by default) prevents hung test runs.

## Graph-level safeguards

- `recursion_limit=8` prevents infinite LangGraph execution.
- `MAX_CORRECTION_ROUNDS=4` stops the self-correction loop earlier at the application level.
- Security rejections terminate the graph immediately; unsafe artifacts are never retried.
