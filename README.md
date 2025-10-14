# wry - Why Repeat Yourself? CLI

[![PyPI version](https://badge.fury.io/py/wry.svg)](https://badge.fury.io/py/wry)
[![Python versions](https://img.shields.io/pypi/pyversions/wry.svg)](https://pypi.org/project/wry/)
[![License](https://img.shields.io/pypi/l/wry.svg)](https://github.com/tahouse/wry/blob/main/LICENSE)
[![CI/CD](https://github.com/tahouse/wry/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/tahouse/wry/actions/workflows/ci-cd.yml)
[![codecov](https://codecov.io/gh/tahouse/wry/branch/main/graph/badge.svg)](https://codecov.io/gh/tahouse/wry)

**wry** (Why Repeat Yourself?) is a Python library that combines the power of Pydantic models with Click CLI framework, enabling you to define your CLI arguments and options in one place using type annotations. Following the DRY (Don't Repeat Yourself) principle, it eliminates the repetition of defining arguments, types, and validation rules separately.

## Features

### Core Features

- 🎯 **Single Source of Truth**: Define your CLI structure using Pydantic models with type annotations
- 🔍 **Type Safety**: Full type checking and validation using Pydantic
- 🌍 **Multiple Input Sources**: Automatically handles CLI arguments, environment variables, and config files
- 📊 **Value Source Tracking**: Know whether each config value came from CLI, env, config file, or defaults
- 🎨 **Auto-Generated CLI**: Automatically generates Click options and arguments from your Pydantic models
- 📝 **Rich Help Text**: Auto-generated help includes type information, constraints, and defaults
- 🔧 **Validation**: Leverage Pydantic's validation system with helpful error messages
- 🌳 **Environment Variable Support**: Automatic env var discovery with customizable prefixes
- 📁 **Config File Support**: Load configuration from JSON files with proper precedence

## Installation

```bash
pip install wry
```

## Quick Start

The simplest way to use wry is with `AutoWryModel`, which automatically generates CLI options for all fields:

```python
import click
from pydantic import Field
from wry import AutoWryModel

class AppArgs(AutoWryModel):
    """Configuration for my app."""

    name: str = Field(description="Your name")
    age: int = Field(default=25, ge=0, le=120, description="Your age")
    verbose: bool = Field(default=False, description="Verbose output")

@click.command()
@AppArgs.generate_click_parameters()
def main(**kwargs: Any):
    """My simple CLI application."""
    # Create the model instance from kwargs
    config = AppArgs(**kwargs)
    click.echo(f"Hello {config.name}, you are {config.age} years old!")

if __name__ == "__main__":
    main()
```

**See comprehensive examples:**

- `examples/autowrymodel_comprehensive.py` - All AutoWryModel features including aliases
- `examples/wrymodel_comprehensive.py` - WryModel with source tracking
- `examples/multimodel_comprehensive.py` - Multi-model usage

Run it:

```bash
$ python app.py --name Alice --age 30 --verbose
Hello Alice, you are 30 years old!
Name was provided via: ValueSource.CLI

# Also supports environment variables
$ export WRY_NAME=Bob
$ python app.py --age 35
Hello Bob, you are 35 years old!
```

## Value Source Tracking

wry tracks where each configuration value came from, supporting all four sources:

- **DEFAULT**: Values from model field defaults
- **ENV**: Values from environment variables
- **JSON**: Values from configuration files (via `--config`)
- **CLI**: Values from command-line arguments

### Basic Usage (No Source Tracking)

```python
@click.command()
@AppArgs.generate_click_parameters()
def main(**kwargs: Any):
    # Simple instantiation - no source tracking
    config = AppArgs(**kwargs)
    # Works fine, but config.source.* will always show CLI
```

### Full Source Tracking (Recommended)

To enable accurate source tracking, use `@click.pass_context` and `from_click_context()`:

```python
@click.command()
@AppArgs.generate_click_parameters()
@click.pass_context
def main(ctx: click.Context, **kwargs: Any):
    # Full source tracking with context
    config = AppArgs.from_click_context(ctx, **kwargs)

    # Check individual field sources
    print(config.source.name)     # ValueSource.CLI
    print(config.source.age)      # ValueSource.ENV
    print(config.source.verbose)  # ValueSource.DEFAULT

    # Get summary of all sources
    summary = config.get_sources_summary()
    # {
    #     ValueSource.CLI: ['name'],
    #     ValueSource.ENV: ['age'],
    #     ValueSource.JSON: ['timeout'],
    #     ValueSource.DEFAULT: ['verbose']
    # }
```

### Comprehensive Example

See `examples/source_tracking_comprehensive.py` for a complete example showing all four sources working together. Run it with:

```bash
# With defaults only
python examples/source_tracking_comprehensive.py

# With environment variables
export MYAPP_TIMEOUT=120
export MYAPP_DEBUG=true
python examples/source_tracking_comprehensive.py

# Mix all sources (CLI > ENV > JSON > DEFAULT)
export MYAPP_TIMEOUT=120
python examples/source_tracking_comprehensive.py --config examples/sample_config.json --port 3000
```

**Output shows source for each field:**

```text
host         = json-server.com      [from JSON]
port         = 3000                 [from CLI]    ← CLI overrides JSON
debug        = True                 [from ENV]
timeout      = 120                  [from ENV]
log_level    = DEBUG                [from JSON]
```

## Configuration Precedence

Values are resolved in the following order (highest to lowest priority):

1. CLI arguments
2. Environment variables
3. Config file values
4. Default values

## Environment Variables

wry automatically generates environment variable names from field names:

```bash
# Set environment variables
export WRY_NAME="Alice"
export WRY_AGE=25

# These will be picked up automatically
python myapp.py --verbose
```

View supported environment variables:

```bash
python myapp.py --show-env-vars
```

## Config Files

Load configuration from JSON files:

```bash
python myapp.py --config settings.json
```

Where `settings.json` contains:

```json
{
    "name": "Bob",
    "age": 35,
    "verbose": true
}
```

## Advanced Usage

### Multi-Model Commands

Use multiple Pydantic models in a single command:

```python
from typing import Annotated
import click
from wry import WryModel, AutoOption, multi_model, create_models

class ServerConfig(WryModel):
    host: Annotated[str, AutoOption] = "localhost"
    port: Annotated[int, AutoOption] = 8080

class DatabaseArgs(WryModel):
    db_url: Annotated[str, AutoOption] = "sqlite:///app.db"
    pool_size: Annotated[int, AutoOption] = 5

@click.command()
@multi_model(ServerConfig, DatabaseConfig)
@click.pass_context
def serve(ctx: click.Context, **kwargs: Any):
    # Create model instances
    configs = create_models(ctx, kwargs, ServerConfig, DatabaseConfig)
    server = configs[ServerConfig]
    database = configs[DatabaseConfig]

    print(f"Starting server at {server.host}:{server.port}")
    print(f"Database: {database.db_url} (pool size: {database.pool_size})")
```

### AutoWryModel - Zero Configuration

Automatically generate options for all fields:

```python
import click
from wry import AutoWryModel
from pydantic import Field

class QuickConfig(AutoWryModel):
    """All fields automatically become CLI options!"""

    name: str = Field(description="Your name")
    age: int = Field(default=30, ge=0, le=120)
    email: str = Field(description="Your email")

@click.command()
@QuickConfig.generate_click_parameters()
def quickstart(config: QuickConfig):
    print(f"Hello {config.name}!")
```

### Direct Configuration Creation

Create configs without decorators:

```python
from wry import WryModel

class Config(WryModel):
    name: str = "default"
    verbose: bool = False

# Create with source tracking
config = Config.create_with_sources(
    name="Alice",  # Will be tracked as programmatic source
    verbose=True
)

# Or from Click context (in a command)
config = Config.from_click_context(ctx, **kwargs)
```

## Advanced Features

### Multi-Model Commands

Use multiple configuration models in a single command:

```python
from wry import WryModel, multi_model, create_models

class DatabaseArgs(WryModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)

class AppArgs(WryModel):
    debug: bool = Field(default=False)
    workers: int = Field(default=4)

@click.command()
@multi_model(DatabaseConfig, AppArgs)
@click.pass_context
def main(ctx: click.Context, **kwargs: Any):
    # Automatically splits kwargs between models
    configs = create_models(ctx, kwargs, DatabaseConfig, AppArgs)

    db_config = configs[DatabaseConfig]
    app_config = configs[AppArgs]

    click.echo(f"Connecting to {db_config.host}:{db_config.port}")
    click.echo(f"Running with {app_config.workers} workers")
```

### Strict Mode (Default)

By default, `generate_click_parameters` runs in strict mode to prevent common mistakes:

```python
@click.command()
@Config.generate_click_parameters()  # strict=True by default
@Config.generate_click_parameters()  # ERROR: Duplicate decorator detected!
def main(**kwargs: Any):
    pass
```

To allow multiple decorators (not recommended):

```python
@Config.generate_click_parameters(strict=False)
```

### Manual Field Control

For more control over CLI generation, use the traditional `WryModel` with annotations:

```python
from typing import Annotated
from wry import WryModel, AutoOption, AutoArgument

class Config(WryModel):
    # Environment variable prefix
    env_prefix = "MYAPP_"

    # Required positional argument
    input_file: Annotated[str, AutoArgument] = Field(
        description="Input file path"
    )

    # Optional flag with short option
    verbose: Annotated[bool, AutoOption] = Field(
        default=False,
        description="Enable verbose output"
    )

    # Option with validation
    timeout: Annotated[int, AutoOption] = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout in seconds"
    )
```

### Using Pydantic Aliases for Custom CLI Names

**New in v0.3.2+**: Pydantic field aliases automatically control the generated CLI option names and environment variable names!

This allows you to have concise Python field names while exposing descriptive CLI options:

```python
from pydantic import Field
from wry import AutoWryModel

class DatabaseConfig(AutoWryModel):
    env_prefix = "DB_"

    # Concise Python field name: db_url
    # Alias controls CLI option: --database-url
    # Environment variable: DB_DATABASE_URL
    db_url: str = Field(
        alias="database_url",
        default="sqlite:///app.db",
        description="Database connection URL"
    )

    pool_size: int = Field(
        alias="connection_pool_size",
        default=5,
        description="Maximum connection pool size"
    )
```

**How it works:**

- **Python field**: `db_url` (concise, easy to type)
- **CLI option**: `--database-url` (descriptive, user-friendly)
- **Environment variable**: `DB_DATABASE_URL` (consistent with CLI)
- **JSON config**: Accepts both `db_url` and `database_url`

**Requirements:**

- **None!** `WryModel` automatically sets `validate_by_name=True` and `validate_by_alias=True`
  - This tells Pydantic to accept both field names and aliases
  - No need to configure anything - it just works!
- Aliases automatically control option names, env var names, and help text

**Full support (v0.3.2+):**

- ✅ Aliases automatically control auto-generated option names
- ✅ Environment variables use alias names (consistent with CLI)
- ✅ Source tracking works correctly
- ✅ JSON config accepts both field names and aliases

**Why this feature exists:**

Before v0.3.2, if you wanted custom CLI option names, you had to use explicit `click.option()` decorators for every field. The alias feature eliminates this boilerplate for the common case where you just want different names.

**For advanced use cases** (short options, custom Click types):

You can still combine aliases with explicit `click.option()` decorators:

```python
class Config(AutoWryModel):
    # Explicit click.option for short option support
    verbose: Annotated[int, click.option("-v", "--verbose", count=True)] = Field(default=0)
```

See `examples/autowrymodel_comprehensive.py` for examples of explicit Click decorators.

### List Type Fields

**Automatic handling**: wry automatically detects `list[T]` and `tuple[T, ...]` type fields and generates Click options with `multiple=True`.

```python
from wry import AutoWryModel

class ProjectConfig(AutoWryModel):
    tags: list[str] = Field(
        default_factory=list,
        description="Project tags"
    )
    ports: list[int] = Field(
        default_factory=list,
        description="Ports to expose"
    )
```

**IMPORTANT - Usage**: Users must pass the option **multiple times** (not comma-separated):

```bash
# ✅ CORRECT - Repeat the option for each value:
python app.py --tags python --tags rust --tags go
# Result: tags=["python", "rust", "go"]

# ✅ Also correct - Single value:
python app.py --tags python
# Result: tags=["python"]

# ✅ Also correct - No values (uses default):
python app.py
# Result: tags=[]

# ❌ INCORRECT - Comma-separated does NOT work as expected:
python app.py --tags python,rust,go
# Result: tags=["python,rust,go"]  ← Single string with commas!
```

**Why not comma-separated?**

This is Click's standard behavior with `multiple=True`. To parse comma-separated values, you would need a custom Click type. The current behavior matches standard Unix CLI conventions (similar to `grep -e pattern1 -e pattern2` or `docker run -v vol1 -v vol2`).

**Works with all list types:**

```python
tags: list[str]         # String lists
ports: list[int]        # Integer lists (with type validation)
flags: list[bool]       # Boolean lists
items: tuple[str, ...]  # Tuples also supported
```

**JSON and Environment Variables:**

```json
{
  "tags": ["python", "rust", "go"],
  "ports": [8080, 8443]
}
```

```python
# JSON config works naturally with arrays
python app.py --config config.json

# CLI can override JSON values
python app.py --config config.json --tags typescript --tags javascript
```

**Tests**: See `tests/unit/auto_model/test_auto_model_list_fields.py` for comprehensive examples.

#### Comma-Separated Alternative (Opt-in)

If you prefer comma-separated input (like `--tags python,rust,go`) instead of repeating the option, wry provides two approaches:

**Approach 1: Per-Field Annotation (fine-grained control)**

```python
from typing import Annotated
from wry import AutoWryModel, CommaSeparated

class Config(AutoWryModel):
    # Standard behavior: --tags a --tags b --tags c
    standard_tags: list[str] = Field(default_factory=list)

    # Comma-separated: --csv-tags a,b,c
    csv_tags: Annotated[list[str], CommaSeparated] = Field(
        default_factory=list,
        description="Tags (comma-separated)"
    )
```

**Approach 2: Model-Wide Setting (all list fields)**

```python
from typing import ClassVar
from wry import AutoWryModel

class Config(AutoWryModel):
    # Enable comma-separated for ALL list fields in this model
    comma_separated_lists: ClassVar[bool] = True

    # All these now accept comma-separated input
    tags: list[str] = Field(default_factory=list)       # --tags a,b,c
    ports: list[int] = Field(default_factory=list)      # --ports 80,443
    values: list[float] = Field(default_factory=list)   # --values 1.5,2.7
```

**Usage**:

```bash
# Standard list field (multiple invocations)
python app.py --standard-tags a --standard-tags b --standard-tags c

# Comma-separated field (single invocation)
python app.py --csv-tags a,b,c

# Works with integers and floats too
python app.py --ports 8080,8443,9000

# With model-wide setting, all lists accept comma-separated
python app.py --tags a,b,c --ports 80,443 --values 1.5,2.7
```

**Which approach to use?**

- **Per-field**: Use when only some lists should be comma-separated, or when mixing both styles
- **Model-wide**: Use when all lists in a model should consistently accept comma-separated input

**Trade-offs**:

- ✅ **Pros**: More concise, familiar to users of tools like `docker run -p 80,443`
- ✅ **Pros**: Model-wide setting is less verbose than annotating every field
- ⚠️ **Cons**: Cannot repeat the option (--csv-tags a,b --csv-tags c won't work)
- ⚠️ **Cons**: Commas in values require escaping or quoting
- ⚠️ **Cons**: Less discoverable (users might not realize comma-separated is supported)

**Recommendation**: Use standard `multiple=True` (default) unless your users specifically expect comma-separated input. The model-wide `comma_separated_lists` setting is convenient when building tools with consistent comma-separated conventions (like Docker-style CLIs).

**Implementation Notes**:

- `comma_separated_lists` is a `ClassVar[bool]` (like `env_prefix`)
- NOT included in Pydantic fields (won't appear in `model_fields` or `model_dump()`)
- Per-field `CommaSeparated` annotation takes priority over model-wide setting
- Works with all list types: `list[str]`, `list[int]`, `list[float]`, `tuple[T, ...]`
- Automatically strips whitespace and filters empty items
- Validates types and enforces Pydantic constraints

**Tests**: 22 comprehensive tests covering standard and comma-separated behavior

- `tests/unit/auto_model/test_auto_model_list_fields.py` - Standard multiple=True (11 tests)
- `tests/unit/auto_model/test_comma_separated_lists.py` - Comma-separated support (11 tests)

**See also:**

- `examples/autowrymodel_comprehensive.py` - Complete AutoWryModel example with aliases
- `examples/wrymodel_comprehensive.py` - WryModel with aliases and source tracking

### Model Inheritance

**New in v0.3.3+**: Both `WryModel` and `AutoWryModel` fully support inheritance! Create base configuration classes and extend them with additional fields.

#### Basic Inheritance

```python
from wry import AutoWryModel
from pydantic import Field

class BaseConfig(AutoWryModel):
    """Common configuration shared across environments."""
    env_prefix = "APP_"
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

class ProductionConfig(BaseConfig):
    """Production-specific configuration."""
    workers: int = Field(default=4, ge=1, le=32, description="Number of workers")
    timeout: int = Field(default=30, ge=1, description="Request timeout")

# ProductionConfig has all fields: debug, log_level, workers, timeout
@click.command()
@ProductionConfig.generate_click_parameters()
@click.pass_context
def serve(ctx: click.Context, **kwargs: Any):
    config = ProductionConfig.from_click_context(ctx, **kwargs)
    click.echo(f"Starting with {config.workers} workers, debug={config.debug}")
```

#### Multiple Levels of Inheritance

```python
class Level1Config(AutoWryModel):
    field1: str = Field(default="v1", description="Level 1 field")

class Level2Config(Level1Config):
    field2: str = Field(default="v2", description="Level 2 field")

class Level3Config(Level2Config):
    field3: str = Field(default="v3", description="Level 3 field")

# Level3Config has all fields: field1, field2, field3
```

#### Inheritance with Multi-Model

```python
from wry import multi_model, create_models

class BaseServer(AutoWryModel):
    host: str = Field(default="localhost", description="Server host")

class ExtendedServer(BaseServer):
    port: int = Field(default=8080, description="Server port")

class BaseDatabase(AutoWryModel):
    db_url: str = Field(default="sqlite:///app.db", description="Database URL")

class ExtendedDatabase(BaseDatabase):
    pool_size: int = Field(default=5, description="Connection pool size")

@click.command()
@multi_model(ExtendedServer, ExtendedDatabase)
@click.pass_context
def main(ctx: click.Context, **kwargs: Any):
    configs = create_models(ctx, kwargs, ExtendedServer, ExtendedDatabase)
    server = configs[ExtendedServer]
    db = configs[ExtendedDatabase]

    # Both base and extended fields are available
    click.echo(f"Server: {server.host}:{server.port}")
    click.echo(f"Database: {db.db_url} (pool={db.pool_size})")
```

#### Mixing WryModel and AutoWryModel

```python
from typing import Annotated
from wry import WryModel, AutoWryModel, AutoOption

# Start with explicit WryModel
class BaseConfig(WryModel):
    base_field: Annotated[str, AutoOption] = Field(default="base")

# Extend with AutoWryModel for automatic options
class ChildConfig(BaseConfig, AutoWryModel):
    # This automatically becomes an option
    child_field: str = Field(default="child")
```

#### Benefits of Inheritance

1. **DRY Principle**: Define common fields once
2. **Environment-Specific Configs**: Base config + dev/staging/prod extensions
3. **Feature Flags**: Base config + feature-specific configurations
4. **Reusable Components**: Create libraries of configuration classes
5. **Full Source Tracking**: Inherited fields track their sources correctly

**Important Notes:**

- All inherited fields automatically become CLI options (for `AutoWryModel`)
- Source tracking works correctly for inherited fields
- `env_prefix` can be inherited or overridden
- Field constraints and validation are inherited
- Works with all wry features: arguments, options, exclusions, aliases

See `tests/features/test_inheritance.py` for comprehensive examples.

## Development

### Prerequisites

- Python 3.10+
- Git with SSH key configured for signing

### Setup

```bash
# Clone the repository
git clone git@github.com:tahouse/wry.git
cd wry

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run with coverage report
pytest --cov=wry --cov-report=html

# Run specific test
pytest tests/test_core.py::TestWryModel::test_basic_model_creation

# Run all checks (recommended before pushing)
./check.sh
```

### Testing Across Python Versions

wry supports Python 3.10, 3.11, and 3.12. To ensure compatibility:

```bash
# Test with all available Python versions locally
./scripts/test_all_versions.sh

# Test in CI-like environment using Docker
./scripts/test_ci_locally.sh

# Run GitHub Actions locally with act (requires act to be installed)
./scripts/test_with_act.sh
```

### Code Quality

This project uses pre-commit hooks to ensure code quality:

- **ruff**: Linting and code formatting
- **mypy**: Type checking (pinned to >=1.17.1)
- **pytest**: Tests with 90% coverage requirement
- **bandit**: Security checks
- **safety**: Dependency vulnerability scanning

Pre-commit will run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

### Version Compatibility

To ensure consistent behavior between local development and CI:

- **pydantic**: >=2.9.2 (for proper type inference)
- **mypy**: >=1.17.1 (for accurate type checking)
- **Python**: 3.10+ (we test against 3.10, 3.11, and 3.12)

Install the exact versions used in CI:

```bash
pip install -e ".[dev]" --upgrade
```

### Coverage Requirements

This project enforces 90% code coverage. To check coverage locally:

```bash
pytest --cov=wry --cov-report=term-missing --cov-fail-under=90
```

## Release Process

This project uses Git tags and GitHub Actions for releases. Only maintainers can create releases.

### Creating a Release

1. Ensure all changes are committed and pushed to `main`
2. Create and push a signed tag:

   ```bash
   git tag -s v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

3. The CI/CD pipeline will automatically:
   - Run all tests
   - Build source and wheel distributions
   - Upload to PyPI
   - Create a GitHub release
   - Sign artifacts with Sigstore

### Versioning

This project follows [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for new functionality (backwards compatible)
- PATCH version for backwards compatible bug fixes

Version numbers are managed by `setuptools-scm` and derived from git tags.

### Development Releases

Every push to `main` creates a development release on PyPI:

```bash
pip install --pre wry  # Install latest dev version
```

## Architecture

### Code Organization

The wry codebase is organized into focused modules:

**Main Package:**

- **`wry/__init__.py`**: Package exports and version handling
- **`wry/click_integration.py`**: Click-specific decorators and parameter generation
- **`wry/multi_model.py`**: Support for multiple models in single commands
- **`wry/auto_model.py`**: Zero-configuration model with automatic option generation

**Core Subpackage (`wry/core/`):**

- **`model.py`**: Core `WryModel` implementation with value tracking
- **`sources.py`**: Value source definitions and tracking
- **`accessors.py`**: Property accessors for field metadata
- **`field_utils.py`**: Field constraint extraction and utilities
- **`env_utils.py`**: Environment variable handling

### Design Principles

1. **WRY (Why Repeat Yourself?)**: Define CLI structure once using Pydantic models
2. **Type Safety**: Leverage Python's type system for validation and IDE support
3. **Explicit is Better**: Users must opt-in to features like source tracking via `@click.pass_context`
4. **Composability**: Mix and match models, decorators, and configurations
5. **Source Tracking**: Always know where configuration values came from

## Contributing

We welcome contributions! Please see **`CONTRIBUTING.md`** for comprehensive guidelines.

**Quick links**:

- 📖 **`CONTRIBUTING.md`** - Complete contributor guide (for humans)
- 🤖 **`.cursorrules`** - AI assistant quick reference
- 📚 **`AI_KNOWLEDGE_BASE.md`** - Complete technical reference
- 🚀 **`RELEASE_PROCESS.md`** - Release workflow and versioning

### Development Setup

We use standard Python virtual environments and pip for dependency management:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode with all dependencies
pip install -e ".[dev]"
```

**Note**: All dependencies are specified in `pyproject.toml`. The `[dev]` extra includes testing, linting, and development tools.

### Common Development Commands

```bash
# Install package in editable mode
pip install -e ".[dev]"

# Update dependencies
pip install -e ".[dev]" --upgrade

# Show installed packages
pip list

# Run tests
pytest

# Run with coverage
pytest --cov=wry

# Run linting
ruff check wry tests
ruff format wry tests

# Run type checking
mypy wry
```

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   ```bash
   git clone git@github.com:YOUR_USERNAME/wry.git
   cd wry
   ```

3. **Add upstream remote**:

   ```bash
   git remote add upstream git@github.com:tahouse/wry.git
   ```

4. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. **Set up development environment**:

   ```bash
   python -m venv venv       # Create virtual environment
   source venv/bin/activate  # Activate it
   pip install -e ".[dev]"   # Install with dev dependencies
   pre-commit install        # Set up git hooks
   ```

2. **Make your changes**:
   - Follow existing code style and patterns
   - Add/update tests for new functionality
   - Update documentation as needed
   - Add docstrings to all new functions/classes

3. **Test your changes**:

   ```bash
   # Run tests
   pytest

   # Check coverage (must be ≥90%)
   pytest --cov=wry --cov-report=term-missing

   # Run linting
   pre-commit run --all-files
   # Or run individual tools:
   ruff check wry tests
   mypy wry
   ```

4. **Commit your changes**:
   - Use [Conventional Commits](https://www.conventionalcommits.org/) format
   - Examples:
     - `feat: add support for YAML config files`
     - `fix: handle empty config files gracefully`
     - `docs: update examples for new API`
     - `test: add tests for edge cases`
     - `refactor: simplify value source tracking`

### Pull Request Guidelines

1. **Update your branch**:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**:
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changes you made and why
   - Include examples if applicable
   - Ensure all CI checks pass

### Code Style

- Use type hints for all function arguments and return values
- Follow PEP 8 (enforced by ruff)
- Maximum line length: 88 characters (Black's default)
- Use descriptive variable names
- Add docstrings to all public functions/classes/modules

### Testing Guidelines

- Write tests for all new functionality
- Maintain 100% code coverage
- Use pytest fixtures for common test setups
- Test both happy paths and edge cases
- Include tests for error conditions

### Documentation

- Update README.md if adding new features
- Add/update docstrings
- Include usage examples in docstrings
- Update type hints

### What We're Looking For

- **Bug fixes**: Always welcome!
- **New features**: Please open an issue first to discuss
- **Documentation**: Improvements always appreciated
- **Tests**: Additional test cases for edge conditions
- **Performance**: Optimizations with benchmarks
- **Examples**: More usage examples

### Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Check existing issues/PRs before creating new ones

## Documentation Index

wry has comprehensive documentation for different audiences:

### For Users

- 📘 **`README.md`** (this file) - Getting started, features, usage examples
- 📁 **`examples/`** - Working code examples
  - `examples/autowrymodel_comprehensive.py` - Complete AutoWryModel features
  - `examples/wrymodel_comprehensive.py` - WryModel with source tracking
  - `examples/multimodel_comprehensive.py` - Multi-model usage

### For Contributors

- 📖 **`CONTRIBUTING.md`** - Complete contributor guide with code patterns and checklists
- 🤖 **`.cursorrules`** - AI assistant quick reference (references CONTRIBUTING.md)
- 🚀 **`RELEASE_PROCESS.md`** - How to create releases and manage versions
- 📋 **`TODO.md`** - Current tasks, planned features, and work in progress

### Technical Reference

- 📚 **`AI_KNOWLEDGE_BASE.md`** - Complete technical reference for AI/LLMs (also useful for humans)
- 📝 **`CHANGELOG.md`** - Version history and all changes
- 🧪 **`tests/README.md`** - Test organization and structure
- 🔧 **`scripts/README.md`** - Development scripts and tools

### Quick Start Navigation

**I'm a user, I want to...**

- Get started → README.md "Quick Start" section
- See examples → `examples/` directory
- Understand features → README.md "Features" section
- Track config sources → README.md "Value Source Tracking" section

**I'm a contributor, I want to...**

- Set up development → CONTRIBUTING.md "Development Setup" section
- Add a feature → CONTRIBUTING.md "Adding New Features" section
- Run tests → CONTRIBUTING.md "Testing" section
- Create a release → RELEASE_PROCESS.md
- Check current tasks → TODO.md

**I'm an AI assistant, I want to...**

- Quick reference → `.cursorrules`
- Technical details → `AI_KNOWLEDGE_BASE.md`
- Code patterns → `CONTRIBUTING.md`
- Test examples → `tests/features/test_source_precedence.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Future Features

### Automatic Model Instantiation (Proof of Concept)

We're exploring a cleaner API that would automatically instantiate models and pass them to your function. See `examples/auto_instantiate_poc.py` for a working proof of concept:

```python
# Potential future syntax
@click.command()
@AppConfig.click_command()  # or @auto_instantiate(AppConfig)
def main(config: AppConfig):
    """The decorator would handle instantiation automatically."""
    click.echo(f"Hello {config.name}!")
    # Source tracking would work automatically too!
```

This would:

- Automatically handle `@click.pass_context` when needed for source tracking
- Instantiate the model and pass it with the correct parameter name
- Support multiple models in a single command
- Make the API more intuitive and similar to other libraries

If you're interested in this feature, please provide feedback!

## Acknowledgments

- Built on top of [Click](https://click.palletsprojects.com/) and [Pydantic](https://pydantic-docs.helpmanual.io/)
- Inspired by the DRY (Don't Repeat Yourself) principle
We'd also like to acknowledgme `pydanclick`, which uses a similar clean syntax (no kwargs to command functions). The code for this feature will be independently written given that `wry` supports source tracking, constraint help text creation, instantiation from config files, and several other features not supported by `pydanclick`.
