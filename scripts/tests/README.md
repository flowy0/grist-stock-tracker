# Tests for Grist Stock Tracker Scripts

This directory contains unit tests for the Python automation scripts.

## Running Tests

### Run All Tests

```bash
uv run pytest
```

### Run with Coverage

```bash
uv run pytest --cov=. --cov-report=term-missing
```

### Run Specific Test File

```bash
uv run pytest tests/test_csv_import.py -v
```

### Run Specific Test

```bash
uv run pytest tests/test_csv_import.py::TestCSVImporter::test_transform_to_bronze -v
```

### Run Integration Tests

```bash
uv run pytest -m integration
```

## Test Structure

| File | Description |
|------|-------------|
| `test_csv_import.py` | Tests for CSV import helper (Bronze layer) |
| `test_bronze_to_silver.py` | Tests for Bronze to Silver transformation |
| `test_price_updater.py` | Tests for price updater |

## Test Coverage

Current test coverage:
- ✅ CSV parsing and transformation
- ✅ Data validation (Bronze to Silver)
- ✅ Symbol normalization
- ✅ Duplicate detection
- ✅ Price provider APIs (mocked)
- ✅ Grist API client (mocked)

## Writing New Tests

Example test structure:

```python
def test_something(self):
    """Test description."""
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

## Notes

- Integration tests are marked with `@pytest.mark.integration` and skipped by default
- Tests use `unittest.mock` to mock external API calls
- Run tests before committing changes
