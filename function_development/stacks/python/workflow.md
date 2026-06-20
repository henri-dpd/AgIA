# Python — workflow

## Step 1 — Set up the environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## Step 2 — Understand the requirement

- Identify all inputs, return types, and exception conditions.
- Map domain concepts to Python types or Pydantic models.
- Clarify whether the function is sync or async.

## Step 3 — Implement

- Write the function with full type hints.
- Raise specific exceptions as documented.
- Run `mypy` after each non-trivial change.

## Step 4 — Lint and format

```bash
ruff check --fix src/
ruff format src/
mypy src/ --strict
```

## Step 5 — Test

```bash
python -m pytest tests/ -v --tb=short
python -m pytest --cov=src --cov-report=term-missing
```

## Step 6 — Review checklist

- [ ] All public functions have complete type annotations.
- [ ] `mypy --strict` passes with no errors.
- [ ] `ruff check` passes with no warnings.
- [ ] No mutable default arguments.
- [ ] Tests cover the happy path, edge cases, and each documented exception.
- [ ] No bare `except:` clauses.
