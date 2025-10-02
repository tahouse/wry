# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-10-02

### Changed

- **Reverted from Poetry to setuptools-scm**
  - Removed Poetry dependency and poetry.lock
  - Back to standard pip/venv workflow: `pip install -e ".[dev]"`
  - Simplified build system using setuptools-scm directly
  - All dependencies still in pyproject.toml [project.dependencies]
  - Development dependencies in [project.optional-dependencies]
  - Easier for contributors (standard Python tooling)
  - No lock file conflicts for library users
  - Updated README with pip-based setup instructions

### Added

- **Comprehensive AI Knowledge Base (AI_KNOWLEDGE_BASE.md)**
  - 2293-line comprehensive reference for AI assistants and LLMs
  - Complete module reference with implementation details
  - Detailed configuration flow diagrams
  - Source tracking deep dive with algorithms
  - Test coverage details (407 tests, 92% coverage)
  - Common patterns, edge cases, and gotchas
  - Quick start templates for all use cases
  - Troubleshooting flowchart and debugging guide
  - API reference with all classes, functions, and methods

- **Integrated help system (wry.help_system)**
  - Programmatic documentation access
  - Multiple topics: readme, ai, sources, architecture, examples
  - CLI usage: `python -m wry.help_system [topic]`
  - Python API: `from wry import print_help; print_help('ai')`
  - Auto-pager for long content
  - Exported functions: `get_help_content()`, `print_help()`, `show_help_index()`

- **Comprehensive source tracking example**
  - `examples/source_tracking_comprehensive.py` demonstrates all 4 sources
  - Color-coded output (GREEN=CLI, BLUE=JSON, YELLOW=ENV, DIM=DEFAULT)
  - Interactive testing with sample commands
  - Includes `examples/sample_config.json` for testing
  - Shows source summary and precedence explanation

### Changed

- **Enhanced README source tracking section**
  - Clearer explanation of all 4 sources (DEFAULT/ENV/JSON/CLI)
  - Added comprehensive example reference
  - Visual output examples showing precedence
  - Better quick start for source tracking

## [0.2.3] - 2025-10-01

### Fixed

- **Explicit `click.argument` decorators not getting help text in docstring**
  - Fixed issue where explicit `click.argument` decorators weren't using `Field(description=...)` for help text injection into command docstrings
  - `extract_and_modify_argument_decorator` now returns tuple of (decorator, info_dict) containing extracted attributes
  - Help text extraction now falls back to `field_info.description` when decorator doesn't have explicit `help` parameter
  - Help text is properly filtered out before passing to Click (since `click.Argument` doesn't accept `help` parameter)
  - Arguments defined with both `AutoArgument` and explicit `click.argument()` now display their help text in the Arguments section of `--help` output

### Added

- **Example for explicit argument help injection**
  - Added `examples/explicit_argument_help.py` demonstrating both `AutoArgument` and explicit `click.argument()` with `Field(description=...)`
  - Shows how help text is automatically injected into the command's Arguments section

## [0.2.2] - 2025-10-01

### Fixed

- **Pydantic V2.11+ deprecation warning**
  - Fixed deprecation warning: "Accessing the 'model_fields' attribute on the instance is deprecated"
  - Changed all instance-level `model_fields` access to class-level access
  - Updated `WryModel.__init__` to use `self.__class__.model_fields`
  - Updated test files to use class-level access pattern
  - Ensures compatibility with Pydantic V2.11 and future V3.0

- **CLI argument precedence bug**
  - Fixed critical bug where CLI arguments didn't override JSON config values
  - Modified `eager_json_config` to not set `param.default`, preserving Click's ability to distinguish CLI-provided values
  - CLI arguments now correctly take precedence over JSON/config file values
  - Proper precedence order is now enforced: CLI > ENV > JSON > DEFAULT
  - Source tracking accurately reflects where each value originated

- **REQUIRED_OPTION not enforcing requirements**
  - Fixed bug where fields marked with `AutoClickParameter.REQUIRED_OPTION` weren't being enforced as required
  - Required fields without explicit defaults no longer receive `default=None` in Click kwargs
  - Click now properly validates and reports missing required options

### Changed

- **Test suite improvements**
  - Added 38 new tests covering edge cases and previously uncovered code paths
  - Improved test coverage from 91% to 92%
  - Total tests increased from 365 to 403
  - All tests pass with Pydantic deprecation warnings treated as errors
  - New test files:
    - `tests/unit/model/test_extract_subset_edge_cases.py` - Extract subset edge cases
    - `tests/unit/click/test_argument_types.py` - Click argument type handling
    - `tests/unit/auto_model/test_auto_model_edge_cases.py` - AutoWryModel edge cases
    - `tests/unit/click/test_format_constraint_text.py` - Constraint formatting
    - `tests/unit/model/test_model_edge_cases.py` - WryModel edge cases

## [0.2.1] - 2025-09-29

### Added

- **Automatic argument help injection into command docstrings**
  - Click arguments (positional parameters) don't show help text by default
  - `wry` now automatically injects argument descriptions from `Field(description=...)` into the command's docstring
  - Arguments section is formatted to match Click's Options section for visual consistency
  - Uses `\b` escape sequences to prevent rewrapping and align with Options
  - Only injects descriptions for arguments that have them
  - Preserves existing command docstrings
  - Example: `arg: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Help text")`

- **New `AutoExclude` convenience alias**
  - Added `AutoExclude` as a shorthand for `AutoClickParameter.EXCLUDE`
  - Complements existing `AutoOption` and `AutoArgument` aliases
  - Makes field exclusion more concise: `field: Annotated[str, AutoExclude]`

## [0.2.0] - 2025-09-29

### Added

- **Field exclusion with `AutoClickParameter.EXCLUDE`**
  - New `EXCLUDE` enum value for `AutoClickParameter` to explicitly exclude fields from CLI
  - Works with both `AutoWryModel` and `WryModel`
  - Excluded fields maintain default values and source tracking
  - Useful for internal fields, computed values, and polymorphic validation
  - Example: `excluded_field: Annotated[str, AutoClickParameter.EXCLUDE] = "internal"`

### Changed

- **Build system migration from setuptools to Poetry** (Reverted in v0.2.4)
  - Improved dependency management with lock files
  - Better development environment isolation
  - Consistent dependencies across local and CI/CD environments
  - Maintained git tag-based versioning with `poetry-dynamic-versioning`
  - Updated CI/CD workflows to use Poetry
  - **Note**: This was reverted back to setuptools-scm in a later release for simplicity

### Fixed

- **`AutoWryModel` annotation processing**
  - Fixed issue where fields with simple type annotations weren't processed correctly
  - All fields now properly receive `AutoClickParameter.OPTION` annotation
  - Improved test isolation to prevent class name conflicts

## [0.1.9] - 2025-09-29

### Added

- **Automatic multiple option support for list types**
  - `list[str]` and `tuple[str, ...]` fields now automatically generate Click options with `multiple=True`
  - Supports both `AutoWryModel` and `WryModel` with proper type conversion
  - Handles edge cases: empty lists, single values, and multiple values
  - Works with different data types: `list[int]`, `list[str]`, etc.
  - Maintains type safety: Click tuples are correctly converted to Python lists

### Fixed

- **Variadic argument bug resolution**
  - Fixed issue where variadic Click arguments (`nargs=-1`) were incorrectly converted to strings
  - Variadic arguments now preserve their tuple type when used with `@generate_click_parameters`
  - Resolves duplicate parameter warnings and validation errors

### Testing

- **Comprehensive test coverage for multiple options**
  - Added `tests/unit/test_multiple_option_bug.py` with 6 test cases
  - Added `tests/unit/test_variadic_argument_bug.py` with 3 test cases
  - Tests cover AutoWryModel, WryModel, edge cases, type validation, and different data types
  - All tests pass with proper type checking and validation

## [0.1.8] - 2025-09-10

### Fixed

- Improved type annotations for `generate_click_parameters` decorator
  - Now uses Click's `FC` TypeVar to preserve function types through decorator chain
  - Fixes pyright `reportUntypedFunctionDecorator` warnings
  - Maintains proper type inference for decorated functions

## [0.1.7] - 2025-09-09

### Added

- `generate_click_parameters` as a classmethod on `WryModel` and `AutoWryModel`
  - Allows using `@MyModel.generate_click_parameters()` directly without imports
  - Simplifies API and reduces import requirements in downstream projects

## [0.1.6] - 2025-09-08

### Added

- GitHub releases now include commit comparison links to previous releases
- Development versions now use `.devN` format and show as pre-releases on PyPI

### Changed

- Switched setuptools-scm from `post-release` to `guess-next-dev` version scheme
- Development versions now appear as pre-releases instead of regular releases on PyPI

## [0.1.5] - 2025-09-08

### Fixed

- Restored PyPI publishing for development releases
- CI/CD now correctly publishes both postN and release versions

### Changed

- Improved CI/CD documentation

## [0.1.4] - 2025-09-08

### Fixed

- CI/CD workflow to skip fetching tags on main branch builds
- Prevents version conflicts when tags are pushed shortly after commits
- Ensures main branch builds always generate .postN development versions

## [0.1.3] - 2025-09-08

### Fixed

- Package discovery configuration to properly install `wry` package in site-packages
- ModuleNotFoundError when installing from PyPI due to incorrect package structure

## [0.1.2] - 2025-09-05

### Fixed

- GitHub release titles no longer include redundant "Release" prefix
- CI/CD workflow now extracts release notes from CHANGELOG.md automatically

### Changed

- Updated CI/CD workflow to use extract_release_notes.py script
- Improved GitHub release formatting with proper changelog integration

## [0.1.1] - 2025-09-05

### Added

- Comprehensive CHANGELOG.md following Keep a Changelog format
- Script to extract release notes from changelog for GitHub releases
- Scripts directory for better project organization

### Changed

- Moved test scripts to `scripts/` directory for cleaner repository structure
- Updated documentation to reflect new script locations

### Documentation

- Added scripts/README.md documenting utility scripts
- Improved main README with updated script paths

## [0.1.0] - 2025-09-05

### Added

- Initial release of `wry` (Why Repeat Yourself?) - a type-safe CLI framework
- Seamless Pydantic-Click integration for automatic CLI parameter generation
- `WryModel` base class for creating type-safe CLI applications
- `AutoWryModel` for automatic parameter discovery from Pydantic fields
- Multi-model CLI support for complex command structures
- Environment variable integration with automatic prefixing
- Support for Python 3.10+ union type syntax (`bool | None`)
- Comprehensive test suite with 90%+ coverage
- Local testing scripts for CI environment matching:
  - `test_all_versions.sh` - Test across Python 3.10, 3.11, 3.12
  - `test_ci_locally.sh` - Run tests in Docker container
  - `test_with_act.sh` - Run GitHub Actions locally
- Type annotations and docstrings throughout the codebase
- Pre-commit hooks for code quality enforcement
- GitHub Actions CI/CD pipeline with automated releases

### Changed

- **Breaking**: Complete package rename from `drycli` to `wry`
- **Breaking**: `DryModel` renamed to `WryModel`
- **Breaking**: `AutoDryModel` renamed to `AutoWryModel`
- Minimum test coverage requirement set to 90%
- Improved error messages and type checking

### Fixed

- Python 3.10 compatibility issues with `Annotated` type syntax
- Boolean flag handling for `Optional[bool]` fields
- Type checking errors with `mypy` across different Python versions

### Security

- Dependencies pinned to minimum versions for consistency:
  - `pydantic>=2.9.2`
  - `mypy>=1.17.1`
  - `click>=8.0`

## [0.0.3] - 2025-09-04

### Fixed

- Removed 'v' prefix from pip install command in release notes
- Fixed broken version template issue

### Changed

- Initial version as `drycli` package (before rename to `wry`)

[Unreleased]: https://github.com/tahouse/wry/compare/v0.1.9...HEAD
[0.1.9]: https://github.com/tahouse/wry/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/tahouse/wry/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/tahouse/wry/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/tahouse/wry/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/tahouse/wry/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/tahouse/wry/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/tahouse/wry/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/tahouse/wry/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/tahouse/wry/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/tahouse/wry/compare/v0.0.3...v0.1.0
[0.0.3]: https://github.com/tahouse/wry/releases/tag/v0.0.3
