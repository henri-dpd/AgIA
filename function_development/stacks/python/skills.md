# Python — skills

## Core tooling

| Tool | Purpose |
|---|---|
| `ruff` | Linting and formatting (replaces flake8, isort, black) |
| `mypy` | Static type checking |
| `pytest` | Testing framework |
| `pytest-cov` | Coverage reporting |
| `uv` | Fast package and project manager |

## Frequently used packages

| Package | Purpose |
|---|---|
| `pydantic` | Data validation and settings |
| `httpx` | Async HTTP client |
| `sqlalchemy` | ORM and query builder |
| `alembic` | Database migrations |
| `fastapi` | ASGI web framework |
| `typer` | CLI framework |
| `structlog` | Structured logging |
| `tenacity` | Retry logic |

## Pyproject.toml baseline

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.0"]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "ANN"]

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Pydantic model example

```python
from pydantic import BaseModel, ConfigDict, Field

class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
```

## Structured logging with structlog

```python
import structlog

logger = structlog.get_logger()
logger.info("user_created", user_id=str(user.id), email=user.email)
```
