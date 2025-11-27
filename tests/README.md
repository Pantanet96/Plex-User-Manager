# Tests

This directory contains the test suite for the Plex User Library Management application.

## Running Tests

### Run all tests
```bash
python -m pytest tests/
```

### Run specific test file
```bash
python -m pytest tests/test_models.py
```

### Run with coverage
```bash
python -m pytest --cov=. tests/
```

### Run tests with verbose output
```bash
python -m pytest -v tests/
```

## Test Structure

- `test_models.py` - Unit tests for database models
- `test_auth.py` - Tests for authentication and authorization
- `test_routes.py` - Tests for Flask routes (TODO)
- `test_plex_service.py` - Tests for Plex API integration (TODO)

## Writing Tests

Tests use Python's `unittest` framework. Each test class should:
- Inherit from `unittest.TestCase`
- Use `setUp()` to create test fixtures
- Use `tearDown()` to clean up after tests
- Use descriptive test method names starting with `test_`

## Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov
```

## CI/CD

Tests are automatically run on:
- Pull requests to `main` and `development` branches
- Commits to `development` branch

## Coverage Goals

- Aim for >80% code coverage
- All critical paths should be tested
- Edge cases and error handling should be covered
