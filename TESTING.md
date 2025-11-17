# ATS Match Analyzer - Testing Guide

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

This will generate:
- Terminal output showing coverage percentages
- An HTML coverage report in `htmlcov/index.html`

### Run Specific Test Files
```bash
pytest test_ats_scoring.py
pytest test_resume_optimizer.py
pytest test_app.py
```

### Run Specific Test Classes or Functions
```bash
pytest test_ats_scoring.py::TestNormalize
pytest test_ats_scoring.py::TestNormalize::test_normalize_basic
```

### Run Tests in Verbose Mode
```bash
pytest -v
```

### Run Tests and Stop on First Failure
```bash
pytest -x
```

## Test Structure

### test_ats_scoring.py
Tests for the core ATS scoring logic:
- Text normalization
- Keyword extraction
- Similarity calculations
- Skills coverage analysis
- Seniority detection and alignment
- ATS-friendliness scoring
- Posting recency factors
- Complete resume scoring

### test_resume_optimizer.py
Tests for resume optimization features:
- Header and body splitting
- Section extraction
- Text optimization
- DOCX generation
- Keyword integration

### test_app.py
Tests for the main application functions:
- PDF text extraction
- URL fetching and parsing
- Job description input handling
- LinkedIn profile extraction
- Input validation

## Code Coverage

Target coverage: 80%+

Current test coverage includes:
- Core business logic (scoring, optimization)
- Data extraction and parsing
- Error handling
- Edge cases (empty inputs, malformed data)
- Integration scenarios

## Writing New Tests

When adding new features, follow these guidelines:

1. **Test file naming**: `test_<module_name>.py`
2. **Test class naming**: `Test<FunctionOrClass>` (use classes to group related tests)
3. **Test function naming**: `test_<what_is_being_tested>`
4. **Use pytest fixtures** for common setup
5. **Mock external dependencies** (API calls, file I/O)
6. **Test edge cases** (empty, None, invalid inputs)
7. **Assert specific behaviors**, not just "doesn't crash"

### Example Test Pattern
```python
def test_function_with_valid_input():
    # Arrange
    input_data = "test data"
    expected = "expected result"

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected
```

## Continuous Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors
Make sure you're in the project root directory and have installed all dependencies.

### Mock Issues
Ensure you're patching the correct module path. Use `app.function_name` not `module.function_name`.

### Slow Tests
Use `pytest -k "not slow"` to skip slow tests, or mark slow tests with `@pytest.mark.slow`.
