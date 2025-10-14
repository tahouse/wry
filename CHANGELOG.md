# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2025-10-14

### Fixed

- **Comma-separated lists with `default_factory`** 🐛
  - Fixed bug where fields with `default_factory=list` would receive `None` instead of empty list when not provided
  - Added proper handling in `click_integration.py` to call `default_factory()` for default values
  - All comma-separated list tests now pass without validation errors

### Added

- **Development guidelines** 📚
  - Created `.cursorrules` as AI assistant's quick reference guide
  - Created `CONTRIBUTING.md` as comprehensive contributor guide
  - `.cursorrules` references `CONTRIBUTING.md` for detailed explanations
  - Both tailored specifically for wry development patterns

### Changed

- **Test quality improvements** ✨
  - Fixed Pydantic shadow warnings by renaming `source` field to `source_path`/`source_file` in test cases
  - Added `@pytest.mark.filterwarnings` to suppress intentional warnings in tests
  - Tests that validate warning behavior no longer pollute test output
  - All 494 tests pass cleanly with zero warnings

- **Test quality improvements** ✨
  - Fixed Pydantic shadow warnings by renaming `source` field to `source_path`/`source_file` in test cases
  - Added `@pytest.mark.filterwarnings` to suppress intentional warnings in tests
  - Tests that validate warning behavior no longer pollute test output
  - All 494 tests pass cleanly with zero warnings

- **Documentation cross-references** 🔗
  - README.md: Added Contributing section with links to CONTRIBUTING.md, .cursorrules, AI_KNOWLEDGE_BASE.md
  - AI_KNOWLEDGE_BASE.md: Updated header with related documentation links
  - AI_KNOWLEDGE_BASE.md: Updated version to 0.5.0+ and test count to 494
  - AI_KNOWLEDGE_BASE.md: Added separate guidance sections for AI assistants and contributors
  - Creates clear documentation hierarchy and navigation

- **CHANGELOG requirements strengthened** ⚠️
  - .cursorrules: Made CHANGELOG.md update mandatory and explicit (first item)
  - CONTRIBUTING.md: Added prominent warning that CHANGELOG.md updates are required for every commit
  - CONTRIBUTING.md: Listed all CHANGELOG sections (Added/Changed/Fixed/Deprecated/Removed/Security)
  - RELEASE_PROCESS.md: Clarified [Unreleased] → versioned section workflow
  - RELEASE_PROCESS.md: Documented that commits add to [Unreleased] during development
  - RELEASE_PROCESS.md: Explained that release commit converts [Unreleased] to [X.Y.Z]

- **TODO.md integration** 📋
  - .cursorrules: Added TODO.md update as step 5 in pre-commit requirements
  - CONTRIBUTING.md: Added TODO.md checklist item (mark completed, update progress)
  - RELEASE_PROCESS.md: Check TODO.md before release, update after release
  - README.md: Added comprehensive "Documentation Index" section
  - README.md: Listed TODO.md in "For Contributors" section
  - README.md: Added "Quick Start Navigation" for users/contributors/AI assistants

### Tests

- **Additional comma-separated test** (494 total tests)
  - `test_model_wide_setting_does_not_affect_non_list_fields`
  - Validates that `comma_separated_lists: ClassVar[bool] = True` only affects list fields
  - Non-list fields (str, int, bool) work normally
  - Explicit `click.option` decorators (like `-vvv` for verbose) are not affected
  - Tests real-world use case: model-wide comma-separated + verbose counting

## [0.5.0] - 2025-10-14

### Added

- **Comprehensive list field support** 🎯
  - `list[str]`, `list[int]`, `list[float]`, `tuple[T, ...]` automatically get `multiple=True`
  - Standard behavior: `--tags python --tags rust --tags go` (repeat option)
  - Users must repeat the option for multiple values (Click's standard `multiple=True`)
  - Comma-separated values NOT supported by default (documented as intentional)

- **Comma-separated list input (opt-in)** ✨
  - Two ways to enable comma-separated parsing:
    1. **Per-field annotation**: `Annotated[list[str], CommaSeparated]`
    2. **Model-wide ClassVar**: `comma_separated_lists: ClassVar[bool] = True`
  - Usage: `--tags python,rust,go` (single invocation with commas)
  - Works with all list types: `list[str]`, `list[int]`, `list[float]`
  - Custom Click ParamTypes: `CommaSeparatedStrings`, `CommaSeparatedInts`, `CommaSeparatedFloats`
  - Per-field annotation takes priority over model-wide setting
  - Automatically strips whitespace and filters empty items
  - Full Pydantic validation preserved (min_length, max_length, etc.)

- **ClassVar configuration: `comma_separated_lists`**
  - Works like `env_prefix: ClassVar[str]` - class-level configuration
  - NOT included in Pydantic model fields (won't appear in `model_fields` or `model_dump()`)
  - Can be set on model class to enable comma-separated for all list fields
  - Can be overridden in child classes
  - AutoWryModel correctly skips ClassVar fields during processing

### Fixed

- **AutoWryModel ClassVar handling** 🐛
  - Fixed bug where ClassVar annotations (like `env_prefix`, `comma_separated_lists`) would cause errors
  - AutoWryModel now properly skips ClassVar fields during automatic processing
  - Prevents `TypeError: typing.ClassVar[T] is not valid as type argument`

### Tests

- **22 new comprehensive tests** (471 → 493 total tests)
  - `tests/unit/auto_model/test_auto_model_list_fields.py` - 11 tests for standard behavior
    - Multiple types (str, int, bool, tuple)
    - Default values, constraints, source tracking
    - JSON config, environment variables, help text
  - `tests/unit/auto_model/test_comma_separated_lists.py` - 11 tests for comma-separated
    - Per-field annotations (7 tests)
    - Model-wide ClassVar (2 tests)
    - Mixed usage (2 tests)
    - Edge cases: whitespace, empty items, type validation

### Documentation

- **README.md List Type Fields section**
  - Clear explanation of standard `multiple=True` behavior
  - Documentation that comma-separated is NOT default (by design)
  - Two approaches for comma-separated (per-field and model-wide)
  - Usage examples for both approaches
  - Trade-offs and recommendations
  - Implementation notes (ClassVar, priority rules, type support)

- **AI_KNOWLEDGE_BASE.md comprehensive update**
  - Edge case #5: List Fields Auto-Get multiple=True (expanded significantly)
  - Detailed explanation of both standard and comma-separated approaches
  - How it works: detection, type selection, parsing, priority
  - Model-wide ClassVar details (similar to env_prefix pattern)
  - Complete test coverage breakdown (22 tests documented)
  - Edge cases validated
  - When to use each approach

- **Module docstrings**
  - `wry/comma_separated.py` - Complete module documentation with both approaches
  - Custom ParamType implementations with full docstrings

### Technical Details

- New module: `wry/comma_separated.py` with custom Click ParamTypes
- Modified `wry/core/model.py`: Added `comma_separated_lists: ClassVar[bool] = False`
- Modified `wry/auto_model.py`: Skip ClassVar fields (lines 62-68)
- Modified `wry/click_integration.py`: Detect and handle comma-separated (lines 431-454)
- Export `CommaSeparated` from `wry/__init__.py`

### Breaking Changes

None - all changes are opt-in or additive.

## [0.4.1] - 2025-10-07

### Fixed

- **AutoWryModel inheritance bug** 🐛
  - Fixed critical bug where child classes inheriting from `AutoWryModel` were not processing their own fields
  - Previously used `hasattr()` which checked the entire inheritance chain, causing child class fields to be skipped
  - Now uses `"_autowrymodel_processed" in cls.__dict__` to check only the current class
  - All inherited fields now correctly become CLI options in child classes
  - Multiple levels of inheritance now work correctly
  - Note: `WryModel` was not affected by this bug and has always supported inheritance correctly

### Added

- **Comprehensive inheritance test suite** (24 new tests in `tests/features/test_inheritance.py`)
  - Tests for `AutoWryModel` inheritance (10 tests - verify the bug fix)
  - Tests for `WryModel` inheritance (6 tests - verify continued functionality)
  - Tests for multi-model inheritance (5 tests - mix of both types)
  - Edge case tests (3 tests - various scenarios)
  - Coverage includes: basic inheritance, multiple levels, CLI generation, source tracking, constraints, env_prefix, mixed model types, and more

### Documentation

- **New inheritance section in README.md**
  - Basic inheritance examples
  - Multiple levels of inheritance
  - Inheritance with multi-model
  - Mixing `WryModel` and `AutoWryModel`
  - Use cases and best practices

- **New Pattern 8 in AI_KNOWLEDGE_BASE.md**
  - Comprehensive inheritance patterns and examples
  - Technical details about the bug fix
  - Use cases: environment-specific configs, feature flags, shared authentication
  - Updated test statistics (407 → 431+ tests)

### Technical Details

- Bug was in `AutoWryModel.__init_subclass__()` at line 46 of `wry/auto_model.py`
- Changed from checking inherited attributes to checking class-specific attributes
- This enables proper field processing for each class in an inheritance hierarchy
- All existing tests continue to pass (no breaking changes)

## [0.4.0] - 2025-10-04

### Added

- **Automatic Pydantic alias-based CLI option generation** 🎉
  - Aliases now automatically control generated CLI option names and environment variable names
  - Example: `db_url` field with `alias="database_url"` generates `--database-url` option and `DB_DATABASE_URL` env var
  - No configuration required - works out of the box!
  - `WryModel` now sets `validate_by_name=True` and `validate_by_alias=True` by default
  - Full source tracking support (CLI/ENV/JSON/DEFAULT) with aliases
  - JSON config files accept both field names and aliases
  - New example: `examples/field_alias_example.py` demonstrating automatic alias-based generation
  - Note: For short options (e.g., `-v`), continue using explicit `click.option()` decorators as shown in `examples/auto_model_example.py`
  - Comprehensive test suite: 20 tests covering all alias scenarios including precedence chains

### Changed

- **Pydantic v2.11+ compatibility** - replaced deprecated `populate_by_name` with `validate_by_name` and `validate_by_alias`
- `WryModel.model_config` now includes `validate_by_name=True` and `validate_by_alias=True` by default
- `generate_click_parameters()` now uses field aliases for auto-generated option names
- `get_env_var_names()` now uses field aliases for environment variable names
- Updated all documentation (README, AI_KNOWLEDGE_BASE, TODO) with alias feature details

### Fixed

- Source tracking now works correctly when using Pydantic aliases
- JSON config loading properly handles both field names and aliases
- Parameter source detection checks both alias and field name for Click compatibility
- Removed all deprecated `Field(annotation=...)` usage in tests
- All deprecation warnings eliminated for Pydantic v3 compatibility
- Click now properly validates required arguments and options, providing native Click error messages
- Fixed type display in `--show-env-vars` to correctly extract types from Annotated fields

### Technical Details

- Modified `from_click_context()` to build alias-to-field mapping and handle both field names and aliases
- Enhanced kwargs filtering to accept both field names and aliases, mapping aliases back to field names for source tracking
- Updated JSON config handling to map aliases to field names
- Improved parameter source checking with alias fallback
- Updated `generate_click_parameters()` to use aliases for option name generation
- Updated `get_env_var_names()` to use aliases for environment variable names
- Modified argument generation to properly handle `required` flag based on field defaults and environment variables
- Removed forced `required=False` override in `extract_and_modify_argument_decorator()` to preserve original Click behavior
- Improved `print_env_vars()` to correctly extract base types from Annotated fields
- Consolidated 16 example files into 3 comprehensive examples for easier discovery:
  - `examples/autowrymodel_comprehensive.py` - All AutoWryModel features
  - `examples/wrymodel_comprehensive.py` - WryModel with source tracking
  - `examples/multimodel_comprehensive.py` - Multi-model usage
- All 436 tests pass with 92%+ code coverage

## [0.3.1] - 2025-10-02

### Fixed

- CI/CD build configuration for setuptools-scm
- Version generation now works correctly with git tags

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
