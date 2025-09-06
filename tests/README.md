# Test Organization

This directory contains all tests for the wry package, organized by test type and functionality.

## Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── core/          # Tests for core functionality (WryModel, accessors, etc.)
│   ├── click/         # Tests for Click integration
│   ├── model/         # Tests for model-specific functionality
│   ├── auto_model/    # Tests for AutoWryModel
│   └── multi_model/   # Tests for multi-model commands
├── integration/       # Integration tests for component interactions
└── features/          # Feature tests for end-to-end functionality
```

## Test Categories

### Unit Tests (`unit/`)

- **core/**: Tests for the core module including WryModel, accessors, field utilities, environment utilities, and sources
- **click/**: Tests for Click integration including parameter generation, constraint formatting, and predicate handling
- **model/**: Tests for model functionality like data extraction, environment integration, and Click context handling
- **auto_model/**: Tests for AutoWryModel field processing and annotation inference
- **multi_model/**: Tests for multi-model command functionality

### Integration Tests (`integration/`)

- Tests that verify correct interaction between multiple components
- Click integration with Pydantic models
- Context handling across different scenarios

### Feature Tests (`features/`)

- End-to-end tests for major features
- AutoWryModel usage patterns
- Multi-model command scenarios
- Source precedence and tracking

## Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/core
pytest tests/integration
pytest tests/features

# Run with coverage
pytest --cov=wry --cov-report=term-missing

# Run specific test file
pytest tests/unit/model/test_data_extraction.py
```

## Test Naming Conventions

- Test files should be named `test_<functionality>.py`
- Test classes should describe the component being tested
- Test methods should describe the specific behavior being tested
- Avoid generic names like "test_coverage" or "test_edge_cases" in filenames
