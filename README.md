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
from wry import AutoWryModel, generate_click_parameters

class AppArgs(AutoWryModel):
    """Configuration for my app."""

    name: str = Field(description="Your name")
    age: int = Field(default=25, ge=0, le=120, description="Your age")
    verbose: bool = Field(default=False, description="Verbose output")

@click.command()
@generate_click_parameters(AppArgs)
def main(**kwargs):
    """My simple CLI application."""
    config = AppArgs(**kwargs)
    click.echo(f"Hello {config.name}, you are {config.age} years old!")

if __name__ == "__main__":
    main()
```

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

wry can track where each configuration value came from. You have two options:

### Option 1: Direct Instantiation (No Source Tracking)

```python
@click.command()
@generate_click_parameters(AppArgs)
def main(**kwargs):
    # Simple instantiation - no source tracking
    config = AppArgs(**kwargs)
    # config.source.* will always show CLI regardless of actual source
```

### Option 2: With @click.pass_context (Full Source Tracking)

```python
@click.command()
@generate_click_parameters(AppArgs)
@click.pass_context
def main(ctx, **kwargs):
    # Full source tracking with context
    config = AppArgs.from_click_context(ctx, **kwargs)

    # Now sources are accurate
    print(config.source.name)     # ValueSource.CLI
    print(config.source.age)      # ValueSource.ENV
    print(config.source.verbose)  # ValueSource.DEFAULT

    # Get summary of all sources
    summary = config.get_sources_summary()
    # {
    #     ValueSource.CLI: ['name'],
    #     ValueSource.ENV: ['age'],
    #     ValueSource.DEFAULT: ['verbose']
    # }
```

**Note**: `from_click_context()` requires a Click context. If you don't need source tracking, use direct instantiation.

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
from wry import WryModel, AutoOption, generate_click_parameters, multi_model

class ServerConfig(WryModel):
    host: Annotated[str, AutoOption] = "localhost"
    port: Annotated[int, AutoOption] = 8080

class DatabaseArgs(WryModel):
    db_url: Annotated[str, AutoOption] = "sqlite:///app.db"
    pool_size: Annotated[int, AutoOption] = 5

@click.command()
@multi_model(ServerConfig, DatabaseConfig)
def serve(server: ServerConfig, database: DatabaseConfig):
    print(f"Starting server at {server.host}:{server.port}")
    print(f"Database: {database.db_url} (pool size: {database.pool_size})")
```

### AutoWryModel - Zero Configuration

Automatically generate options for all fields:

```python
import click
from wry import AutoWryModel, generate_click_parameters
from pydantic import Field

class QuickConfig(AutoWryModel):
    """All fields automatically become CLI options!"""

    name: str = Field(description="Your name")
    age: int = Field(default=30, ge=0, le=120)
    email: str = Field(description="Your email")

    # No need for Annotated[..., AutoOption]!

@click.command()
@generate_click_parameters(QuickConfig)
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
def main(ctx, **kwargs):
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
@generate_click_parameters(Config)  # strict=True by default
@generate_click_parameters(Config)  # ERROR: Duplicate decorator detected!
def main(**kwargs):
    pass
```

To allow multiple decorators (not recommended):

```python
@generate_click_parameters(Config, strict=False)
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

# Install in development mode
pip install -e ".[dev,test]"

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
pip install -e ".[dev,test]" --upgrade
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

We welcome contributions! Please follow these guidelines to ensure a smooth process.

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
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev,test]"
   pre-commit install
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

   # Check coverage (must be 100%)
   pytest --cov=wry --cov-report=term-missing

   # Run linting
   pre-commit run --all-files
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of [Click](https://click.palletsprojects.com/) and [Pydantic](https://pydantic-docs.helpmanual.io/)
- Inspired by the DRY (Don't Repeat Yourself) principle
