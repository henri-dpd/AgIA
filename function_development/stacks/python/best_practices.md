# Python — best practices

## Language version and type hints

- Target **Python 3.11+**; use `from __future__ import annotations` for forward-reference compatibility.
- Annotate every public function signature; use `mypy --strict` or `pyright` in CI.
- Prefer built-in generics (`list[int]`, `dict[str, Any]`) over `typing.List` / `typing.Dict` (Python 3.9+).
- Use `TypeAlias` (Python 3.10+) or `type` statement (Python 3.12+) for named type aliases.

## Data modelling

- Use **Pydantic v2** for data validation, serialisation, and settings; use `model_config = ConfigDict(extra="forbid")` to reject unexpected fields.
- Use **dataclasses** (`@dataclass(frozen=True)`) for simple value objects that do not need validation.
- Use **`NamedTuple`** for lightweight immutable records that benefit from positional access.

## Functions

- Keep functions short and focused; a function that is hard to name is probably doing too much.
- Raise **specific exceptions** (`ValueError`, `TypeError`, custom subclasses of `Exception`); never raise `Exception` directly.
- Use `*` to force keyword-only arguments for functions with many parameters.
- Use `Final` from `typing` for constants that must not be reassigned.

## Imports

- Sort imports with `isort` or `ruff`; group: standard library, third-party, local.
- Avoid star imports (`from module import *`); they hide the origin of names.
- Use absolute imports inside packages; relative imports only in tightly coupled submodules.

## Error handling

- Catch the narrowest exception type possible.
- Always preserve the original exception with `raise ... from exc` when re-raising.
- Do not use bare `except:` (without a type); it catches `SystemExit` and `KeyboardInterrupt`.

## Async (asyncio)

- Mark all I/O-bound coroutines with `async def`; never block the event loop with synchronous I/O.
- Use `asyncio.TaskGroup` (Python 3.11+) for concurrent tasks; it handles cancellation safely.
- Use `anyio` or `trio` for library code that must be event-loop-agnostic.

## Naming conventions

| Entity | Convention | Example |
|---|---|---|
| Function / variable | `snake_case` | `get_user_by_id` |
| Class | `PascalCase` | `UserRepository` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |
| Private attribute | `_snake_case` | `_connection` |
| Module | `snake_case` | `user_service.py` |
| Package | `snake_case` | `auth/` |
| Type alias | `PascalCase` | `UserId = str` |

## Anti-patterns

- Do not use mutable default arguments (`def f(items=[]):`); use `None` as default and initialise inside the function.
- Do not use bare `except:` without a type.
- Do not use `global` or `nonlocal` for shared state; use class attributes or inject dependencies.
- Do not shadow built-in names (`list`, `id`, `type`, `input`).
- Do not `import *`; it makes the namespace unpredictable.
