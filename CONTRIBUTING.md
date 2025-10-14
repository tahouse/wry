# Contributing to wry

Thank you for contributing! Here's how to get started.

## Project Structure

```
wry/
├── wry/                     # Core library
│   ├── __init__.py          # Public API exports
│   ├── _version.py          # Version management
│   ├── auto_model.py        # AutoWryModel (auto-generates options)
│   ├── click_integration.py # Click parameter generation
│   ├── comma_separated.py   # Comma-separated list support
│   ├── help_system.py       # Documentation system
│   ├── multi_model.py       # Multi-model support
│   └── core/                # Core functionality
│       ├── model.py         # WryModel base class
│       ├── sources.py       # ValueSource, TrackedValue
│       ├── accessors.py     # Property accessors (source, constraints, etc.)
│       ├── field_utils.py   # Constraint extraction
│       └── env_utils.py     # Environment variable handling
│
├── examples/                # Usage examples
│   ├── autowrymodel_comprehensive.py  # Complete AutoWryModel features
│   ├── wrymodel_comprehensive.py      # WryModel with source tracking
│   └── multimodel_comprehensive.py    # Multi-model usage
│
├── tests/                   # Test suite
│   ├── features/            # End-to-end feature tests
│   │   ├── test_source_precedence.py  # All 4 sources tested
│   │   ├── test_auto_model.py
│   │   ├── test_inheritance.py
│   │   └── test_multi_model.py
│   ├── integration/         # Component integration tests
│   │   └── test_click_integration*.py
│   └── unit/                # Unit tests by module
│       ├── core/            # WryModel, sources, accessors
│       ├── click/           # Click integration (22 test files)
│       ├── model/           # Model functionality
│       ├── auto_model/      # AutoWryModel (includes list fields)
│       └── multi_model/     # Multi-model support
│
├── scripts/                 # Development tools
├── docs/                    # Documentation
├── AI_KNOWLEDGE_BASE.md     # Complete reference for AI/LLMs
├── README.md                # User documentation
└── CHANGELOG.md             # Version history
```

## Core Concepts

### wry Architecture

**wry** eliminates CLI configuration repetition by:

1. **Single Source of Truth**: Define configuration once in Pydantic models
2. **Auto-Generate CLI**: Automatically create Click parameters
3. **Source Tracking**: Track where each value came from (CLI/ENV/JSON/DEFAULT)
4. **Strict Precedence**: CLI > JSON > ENV > DEFAULT (always)

### Key Components

- **WryModel**: Base Pydantic model with source tracking
- **AutoWryModel**: Automatically makes all fields CLI options
- **Source Tracking**: `config.source.field_name` → ValueSource enum
- **Click Integration**: Generates `click.option()` and `click.argument()` from Pydantic fields
- **Multi-Model**: Combine multiple configuration models in one command

## Code Organization Principles

### 1. Separation of Concerns

- **`core/`** - Core Pydantic model logic, source tracking, utilities
- **`click_integration.py`** - Click parameter generation only
- **`auto_model.py`** - Automatic option generation
- **`multi_model.py`** - Multi-model coordination
- **`comma_separated.py`** - Custom Click ParamTypes

### 2. Key Design Principles

- **DRY**: Configuration defined once, used everywhere
- **Type Safety**: Full Pydantic validation + Click type conversion
- **Explicit > Implicit**: Opt-in to features (source tracking, comma-separated)
- **Composability**: Mix AutoWryModel with explicit Click decorators
- **Zero Surprises**: Documented precedence, comprehensive tests

### 3. Source Tracking is THE Killer Feature

Every config value tracks its origin:

- `ValueSource.CLI` - Command line
- `ValueSource.ENV` - Environment variable
- `ValueSource.JSON` - Config file
- `ValueSource.DEFAULT` - Model default

## Adding New Features

### Core Functionality

Add to `wry/` or `wry/core/`:

```python
# wry/core/your_feature.py
"""Clear docstring explaining the module.

This module provides...
"""

from typing import Any

def your_function(param: str) -> dict[str, Any]:
    """One-line description.

    Args:
        param: Description of parameter

    Returns:
        Dictionary with results

    Example:
        ```python
        result = your_function("test")
        ```
    """
    # Implementation
```

### Examples

Add to `examples/`:

1. Create ONE file per use case
2. Add comprehensive module docstring
3. Include usage in docstring with command examples
4. Keep it focused and minimal
5. Update `README.md` to reference it

```python
"""Demonstration of [feature name].

This example shows how to use [feature] with wry.

Usage:
    python examples/your_example.py --option value
    python examples/your_example.py --config config.json

Key Features Demonstrated:
- Feature 1
- Feature 2
"""
```

### Tests

Add tests to the appropriate category:

**Feature Tests** (`tests/features/`) - End-to-end scenarios:

```python
# tests/features/test_your_feature.py
"""End-to-end tests for YourFeature."""

def test_complete_feature_flow():
    """Test YourFeature with real Click commands."""
    # Full integration test with CliRunner
```

**Unit Tests** (`tests/unit/`) - Isolated component tests:

```python
# tests/unit/core/test_your_feature.py
"""Unit tests for YourFeature."""

def test_your_feature_edge_case():
    """Test that YourFeature handles edge case X."""
    # Fast, focused test
```

**Integration Tests** (`tests/integration/`) - Component interaction:

```python
# tests/integration/test_your_feature_integration.py
"""Integration tests for YourFeature with Click."""

def test_your_feature_with_click():
    """Test YourFeature integration with Click commands."""
    # Tests multiple components working together
```

## Code Style

### Python Best Practices

#### Type Annotations

- **ALWAYS** add type annotations to all functions, methods, and class attributes
- Include return types for all functions (use `-> None` for void functions)
- Use proper generic types from `typing` module
- Prefer modern Python 3.10+ syntax (e.g., `list[str]` over `List[str]`)

#### Documentation

- **Type hints**: Always use (Python 3.10+ syntax preferred)
- **Docstrings**: All public functions/classes/modules (Google style)
- Add comprehensive docstrings to:
  - All modules (at the top of the file)
  - All classes (describing purpose, attributes, and usage)
  - All public functions and methods (describing parameters, return values, and exceptions)
- **No print()**: Not applicable for a library
- **Formatting**: Ruff handles formatting automatically

#### Code Quality

- **DRY Principles**: Don't Repeat Yourself - extract common logic into reusable functions/classes
- **Clean Code**: Write self-documenting code with clear variable and function names
- **No Dead Code**: Remove unused variables, functions, and commented-out code unless it serves as important documentation
- **Maintainability**: Prioritize code that is easy to understand, modify, and extend

### Linter and Type Checker Compliance

#### Fixing Issues Properly

- **ALWAYS** fix linter errors and type checker warnings properly
- **AVOID** using ignore directives like `# type: ignore`, `# noqa` as quick fixes
- **AVOID** using `cast()` unless absolutely critical for complex type scenarios
- Investigate the root cause and fix issues with proper type annotations and code structure
- If an ignore directive is truly necessary, add a detailed comment explaining why

**Example - Bad**:
```python
result = some_function()  # type: ignore  # ❌ Don't do this
```

**Example - Good**:
```python
# Fix the type annotation properly
def some_function() -> dict[str, Any]:  # ✅ Proper return type
    return {"key": "value"}

result = some_function()  # No ignore needed
```

### Working Directory

- **ALWAYS** ensure you're in the correct directory before:
  - Running commands
  - Creating files
  - Executing scripts
  - Making git operations

### Date and Time Handling

- Use actual date/time functions, not hardcoded values
- For testing, use fixtures or mocking for reproducible results
- Never assume or hardcode dates in dynamic contexts

```python
def process_config(
    input_data: dict[str, Any],
    count: int = 10
) -> dict[str, Any]:
    """Process configuration data and return results.

    Args:
        input_data: Input dictionary to process
        count: Number of items to process

    Returns:
        Dictionary with processed results

    Example:
        ```python
        result = process_config({"key": "value"}, count=5)
        ```
    """
    # Implementation
```

### Configuration Models

The correct pattern for using wry:

```python
from typing import Annotated, ClassVar
from pydantic import Field
from wry import AutoWryModel, AutoOption

class MyConfig(AutoWryModel):
    """Configuration for my CLI tool."""

    # Class-level configuration (NOT a field)
    env_prefix: ClassVar[str] = "MYAPP_"
    comma_separated_lists: ClassVar[bool] = False  # Optional

    # Fields become CLI options automatically
    host: str = Field(
        default="localhost",
        description="Server host"
    )

    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Server port"
    )

# Use in CLI:
@click.command()
@MyConfig.generate_click_parameters()
@click.pass_context
def main(ctx: click.Context, **kwargs: Any) -> None:
    """My CLI tool description."""
    config = MyConfig.from_click_context(ctx, **kwargs)

    # Access configuration
    print(f"Connecting to {config.host}:{config.port}")

    # Check source
    print(f"Host from: {config.source.host.value}")
```

**Key Points**:

- Extend `AutoWryModel` for automatic option generation
- Use `ClassVar` for class-level config (`env_prefix`, `comma_separated_lists`)
- Use `generate_click_parameters()` decorator
- Load config with `from_click_context(ctx, **kwargs)` for source tracking
- Access sources with `config.source.field_name`

### List Fields

wry has two approaches for list-type fields:

```python
class Config(AutoWryModel):
    # Standard: --tags python --tags rust --tags go
    tags: list[str] = Field(default_factory=list)

    # Comma-separated (per-field): --csv-tags python,rust,go
    csv_tags: Annotated[list[str], CommaSeparated] = Field(default_factory=list)

# Or model-wide comma-separated:
class CommaSepConfig(AutoWryModel):
    comma_separated_lists: ClassVar[bool] = True  # All lists use comma-separated

    tags: list[str] = Field(default_factory=list)  # Now: --tags python,rust,go
```

## Testing

### Running Tests

```bash
# All tests (recommended before committing)
pytest

# With coverage
pytest --cov=wry --cov-report=term-missing

# Specific category
pytest tests/features/ -v
pytest tests/unit/core/ -v

# Specific test file
pytest tests/features/test_source_precedence.py -v

# Specific test function
pytest tests/features/test_source_precedence.py::TestSourcePrecedence::test_complete_precedence_chain -v

# Fast tests only (skip slow tests if any marked)
pytest -m "not slow"
```

### Test Organization

Place tests logically:

- `tests/features/` - End-to-end feature tests (most important!)
- `tests/integration/` - Component interaction tests
- `tests/unit/` - Isolated component tests organized by module
  - `tests/unit/core/` - WryModel, sources, accessors
  - `tests/unit/click/` - Click integration (22+ test files)
  - `tests/unit/model/` - Model functionality
  - `tests/unit/auto_model/` - AutoWryModel features

**Key Test Files**:

- `tests/features/test_source_precedence.py` ⭐ - Tests all 4 sources (CLI/ENV/JSON/DEFAULT)
- `tests/features/test_inheritance.py` - Model inheritance
- `tests/unit/auto_model/test_auto_model_list_fields.py` - List field behavior
- `tests/unit/auto_model/test_comma_separated_lists.py` - Comma-separated support

### Test Coverage Requirements

- **NEVER** ignore, skip, or disable test cases just to make test suites pass
- If a test fails, fix the underlying issue or update the test if requirements changed
- Add tests for all new functionality
- Update tests when changing existing behavior
- Ensure all tests **PASS** before considering work complete
- Name test files and functions clearly: `test_<function>_<scenario>_<expected_result>`

### Writing Good Tests

```python
def test_feature_with_clear_name():
    """Test that feature X behaves correctly when Y.

    This test validates...
    """
    # Arrange
    config_class = create_test_config()

    # Act
    result = test_with_cli_runner(config_class, ["--option", "value"])

    # Assert
    assert result.exit_code == 0
    assert "expected output" in result.output
```

**Test Requirements**:

- Clear test name describing what's being tested
- Docstring explaining why the test exists
- Use `CliRunner` for Click command tests
- Test all four sources when testing source tracking
- Test edge cases (empty lists, None values, missing required fields)

## Pre-Commit Checklist

**IMPORTANT**: Before making ANY commit, complete this checklist:

### 1. Documentation Updates

**⚠️ ALWAYS UPDATE CHANGELOG.md - This is required for every commit!**

- [ ] **CHANGELOG.md**: **ALWAYS** add entry under `[Unreleased]` with appropriate section:
  - `Added` - New features, new files, new capabilities
  - `Changed` - Changes to existing functionality, documentation updates
  - `Fixed` - Bug fixes
  - `Deprecated` - Features that will be removed
  - `Removed` - Removed features
  - `Security` - Security fixes
- [ ] **README.md**: Update if user-facing features, usage, or API changed
- [ ] **AI_KNOWLEDGE_BASE.md**: Update if architecture, implementation details, or patterns changed
- [ ] **Module docstrings**: Update docstrings in modified modules
- [ ] **Examples**: Add or update examples if demonstrating new features

**Documentation Management**:
- **Do not create excessive markdown files** unless explicitly needed
- If markdown files exist, add content to the appropriate existing file
- If unsure which file is appropriate, consider whether the content belongs in README.md, AI_KNOWLEDGE_BASE.md, or CHANGELOG.md
- Before creating a new markdown file, ask: Is this really necessary?

### 2. Code Quality

- [ ] **Type annotations**: All new functions have type hints (Python 3.10+ syntax)
- [ ] **Docstrings**: All public functions/classes/modules have comprehensive docstrings (Google style)
- [ ] **No dead code**: Remove unused imports, variables, commented code
- [ ] **DRY principle**: No duplicate code - extract common logic
- [ ] **ClassVar for class config**: Use `ClassVar` for `env_prefix`, `comma_separated_lists`

### 3. Tests

- [ ] **New tests**: Added tests for new functionality
- [ ] **Updated tests**: Modified tests for changed behavior
- [ ] **Tests pass**: Run `pytest` - ALL tests must pass
- [ ] **Source tracking**: If adding config features, test all 4 sources (CLI/ENV/JSON/DEFAULT)
- [ ] **Edge cases**: Test error cases, empty values, None, constraints

### 4. Pre-Commit Validation

```bash
# Run all tests with coverage
pytest --cov=wry --cov-report=term-missing

# Check for linter issues (pre-commit will auto-fix many)
ruff check wry/ tests/

# Check types
mypy wry/
```

**Note**: Git commits automatically run pre-commit hooks (ruff, mypy, pytest). All must pass.

### 5. Update TODO.md (if applicable)

- [ ] **TODO.md**: Update if working on tracked tasks
  - Mark completed tasks as done (✅)
  - Remove completed items or move to archive
  - Update progress notes on ongoing work
  - Add new tasks if discovered during development

### 6. wry-Specific Checks

- [ ] **Source tracking works**: If touching config/model code, verify source tracking
- [ ] **Precedence correct**: CLI > JSON > ENV > DEFAULT (verify if changing)
- [ ] **ClassVar not in fields**: Ensure `env_prefix`, `comma_separated_lists` use `ClassVar`
- [ ] **Examples still work**: Run examples if you changed core functionality
- [ ] **Help text clear**: Generated --help output is helpful

### 6. Commit Message

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring (no behavior change)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `build`: Build system changes

**Example**:

```
feat: add comma-separated list support

- Add CommaSeparated marker for per-field annotation
- Add comma_separated_lists ClassVar for model-wide setting
- Per-field annotation takes priority over model-wide
- Full Pydantic validation preserved

Closes #42
```

## Git Best Practices

### File Operations

- **Strongly prefer** using Git commands for file operations:
  - Use `git rm` instead of `rm` when deleting tracked files
  - Use `git mv` instead of `mv` when moving/renaming tracked files
- This ensures Git properly tracks file history instead of treating operations as delete+add
- Always pass `--yes` or appropriate non-interactive flags to avoid user prompts

**Example**:
```bash
# Bad - Git sees this as delete + add
rm old_file.py
touch new_file.py

# Good - Git tracks the rename
git mv old_file.py new_file.py
```

### Safety Rules

- **NEVER** use `git push --force` to main/master without explicit approval
- **NEVER** use `git reset --hard` without understanding the consequences
- **NEVER** commit directly to main - always use feature branches
- Always review changes before committing (`git diff --staged`)

### Commit Workflow

1. Make changes
2. Review: `git diff`
3. Stage: `git add <files>` (or `git add -A` for all)
4. Review staged: `git diff --staged`
5. Commit: `git commit` (pre-commit hooks run automatically)
6. If hooks fail, fix issues and commit again
7. Push: `git push`

## Pull Request Process

1. **Branch**: Create feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Complete checklist**: Follow Pre-Commit Checklist above
3. **Commit**: Make your commit with conventional commit message
4. **Test**: Pre-commit hook will run checks automatically
5. **Push**: Push to remote
   ```bash
   git push -u origin feature/your-feature-name
   ```
6. **PR**: Submit with clear description referencing checklist items

## Critical Rules

### ⚠️ NEVER Skip Pre-Commit Hooks

**NEVER** use `git commit --no-verify` or `--no-gpg-sign` to bypass pre-commit hooks unless explicitly authorized.

Pre-commit hooks:

- Catch bugs before they reach the repository
- Enforce code quality standards
- Run tests to prevent broken code
- Ensure consistent formatting

If pre-commit hooks are failing:

1. **Fix the underlying issue** - don't bypass the check
2. **Ask for help** - if you don't understand the error
3. **Update the hook** - if the check itself is broken
4. **Get approval** - if you truly need to bypass (rare emergency only)

### wry Development Principles

1. **Source tracking is sacred**: Never break the CLI > JSON > ENV > DEFAULT precedence
2. **DRY everywhere**: Configuration defined once, used everywhere
3. **Examples are crucial**: Users learn from examples - keep them clear and comprehensive
4. **Test all 4 sources**: When adding config features, test CLI/ENV/JSON/DEFAULT
5. **ClassVar correctness**: `env_prefix` and `comma_separated_lists` must be ClassVar
6. **Explicit decorators work**: Users can always use explicit `click.option()` - preserve this
7. **No surprises**: Behavior should match documentation exactly

## Guidelines

### DO

✅ Keep examples simple and focused
✅ Test all four configuration sources (CLI/ENV/JSON/DEFAULT)
✅ Use `ClassVar` for class-level config
✅ Write comprehensive docstrings
✅ Add tests for edge cases
✅ Use `from_click_context()` for source tracking
✅ Update both README.md and AI_KNOWLEDGE_BASE.md

### DON'T

❌ Break source precedence (CLI > JSON > ENV > DEFAULT)
❌ Make `env_prefix` or `comma_separated_lists` regular fields
❌ Skip testing source tracking
❌ Bypass pre-commit hooks
❌ Create duplicate functionality
❌ Make breaking changes without major version bump
❌ Ignore linter/type checker errors

## Release Process

For information about creating releases, see **`RELEASE_PROCESS.md`**.

**Key points**:
- During development: Add all changes to `[Unreleased]` in CHANGELOG.md
- When releasing: Convert `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`
- Tag the release commit: `git tag -s vX.Y.Z`
- See RELEASE_PROCESS.md for complete step-by-step instructions

## Questions?

- Check `examples/` for usage patterns
- Check `AI_KNOWLEDGE_BASE.md` for complete technical reference
- Check `README.md` for user documentation
- Check `RELEASE_PROCESS.md` for release workflow
- Check `TODO.md` for current tasks and planned features
- Check `tests/features/test_source_precedence.py` for source tracking examples
- Open an issue for questions or clarifications
