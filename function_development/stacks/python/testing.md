# Python — testing

## Framework

Use **pytest** with **pytest-cov** for coverage.

## File and naming conventions

- Place tests in a `tests/` directory at the project root.
- Mirror the source structure: `src/auth/utils.py` → `tests/auth/test_utils.py`.
- Name test functions with the pattern `test_<unit>_<condition>_<expected_outcome>`.

## Test structure (Arrange – Act – Assert)

```python
def test_normalize_scores_scales_values_to_unit_range() -> None:
    # Arrange
    values = [0.0, 50.0, 100.0]

    # Act
    result = normalize_scores(values)

    # Assert
    assert result == [0.0, 0.5, 1.0]
```

## Parameterised tests

```python
import pytest

@pytest.mark.parametrize("values,expected", [
    ([0.0, 50.0, 100.0], [0.0, 0.5, 1.0]),
    ([10.0, 10.0, 20.0], [0.0, 0.0, 1.0]),
])
def test_normalize_scores_happy_path(values: list[float], expected: list[float]) -> None:
    assert normalize_scores(values) == expected
```

## Testing exceptions

```python
def test_normalize_scores_raises_for_empty_list() -> None:
    with pytest.raises(ValueError, match="empty"):
        normalize_scores([])

def test_normalize_scores_raises_when_all_equal() -> None:
    with pytest.raises(ValueError, match="equal"):
        normalize_scores([5.0, 5.0, 5.0])
```

## Mocking

```python
from unittest.mock import MagicMock, patch

def test_send_email_calls_smtp(mocker: pytest.MockerFixture) -> None:
    mock_smtp = mocker.patch("myapp.email.smtplib.SMTP")
    send_email("alice@example.com", "Hello")
    mock_smtp.return_value.__enter__.return_value.sendmail.assert_called_once()
```

## Running tests

```bash
python -m pytest -v
python -m pytest --cov=src --cov-report=term-missing
python -m pytest --tb=short -q
```
