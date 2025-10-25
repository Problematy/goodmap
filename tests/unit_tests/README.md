# Unit Tests

This directory contains unit tests for the goodmap application.

## Structure

- **`db/`** - Database-related tests organized by functionality
- Individual test files for other components

## Running Tests

Run all unit tests:
```bash
poetry run pytest tests/unit_tests/ -v
```

Run specific test directory:
```bash
poetry run pytest tests/unit_tests/db/ -v
```

Run with coverage:
```bash
poetry run pytest tests/unit_tests/ --cov=goodmap --cov-report=html
```
