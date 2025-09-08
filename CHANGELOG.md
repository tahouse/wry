# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/tahouse/wry/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/tahouse/wry/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/tahouse/wry/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/tahouse/wry/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/tahouse/wry/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/tahouse/wry/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/tahouse/wry/compare/v0.0.3...v0.1.0
[0.0.3]: https://github.com/tahouse/wry/releases/tag/v0.0.3
