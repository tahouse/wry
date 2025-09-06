# TODO List for wry

## Current Sprint

### In Progress

- [ ] Fix remaining test errors (5 tests failing)
  - Fix test_with_dry_model - kwargs not being passed correctly
  - Fix test_from_click_context_parameter_source_error - kwargs not applied
  - Fix version import tests - version string mismatch
- [ ] Achieve 100% code coverage
  - Current coverage: ~80% (improved from 57%)
  - Need to add tests for uncovered lines in click_integration.py

### Completed ✓

- [x] Migrate core Pydantic functionality
- [x] Migrate Click integration
- [x] Create example usage files
- [x] Create comprehensive test suite
- [x] Test the migrated code
- [x] Fix linting issues from pre-commit
- [x] Update README with release process and testing info
- [x] Set up code coverage requirements (pytest.ini configured)

## Future Enhancements

### High Priority

- [ ] Add support for YAML configuration files
- [ ] Add support for TOML configuration files
- [ ] Create more comprehensive examples
  - Nested configuration structures
  - Complex validation scenarios
  - Multi-command CLI applications
- [ ] Add async support for Click commands
- [ ] Create documentation site (Sphinx/MkDocs)

### Medium Priority

- [ ] Add support for configuration file validation/schema generation
- [ ] Create VS Code extension for auto-completion
- [ ] Add support for configuration inheritance/composition
- [ ] Create migration guide from plain Click to wry
- [ ] Add benchmarks comparing performance with plain Click

### Low Priority

- [ ] Add support for custom value source types
- [ ] Create GUI for configuration editing
- [ ] Add support for remote configuration sources
- [ ] Create plugin system for extensions

## Technical Debt

- [x] Target Python 3.10 minimum (3.8 EOL'd 11 months ago, 3.9 EOL in 1 month)
  - [x] Update pyproject.toml requires-python
  - [x] Update CI matrix
  - [x] Update mypy and ruff target versions
  - [ ] Use newer Python syntax where appropriate (Union types, etc.)
- [ ] Handle Click context edge cases
  - Context not required: Works fine without @click.pass_context, but then can't use from_click_context()
  - Duplicate decorators: Click warns about duplicate parameters but still works (not recommended)
  - Multiple models: Works but creates duplicate --config/--show-env-vars options with warnings
  - Recommendations:
    - Document that @click.pass_context is optional but needed for source tracking
    - Add decorator check to warn if applied multiple times
    - Consider singleton pattern for --config and --show-env-vars options
    - Add clear error message if from_click_context() called without context
- [ ] Improve error messages for validation failures
- [ ] Add more type hints and improve mypy coverage
- [ ] Optimize import times
- [ ] Add integration tests with real CLI applications
- [ ] Add performance benchmarks

## Documentation

- [ ] Create API documentation
- [ ] Add more inline code examples
- [ ] Create video tutorials
- [ ] Write blog post about the library
- [ ] Create comparison with similar libraries (Typer, Clidantic, etc.)

## Community

- [ ] Set up GitHub Discussions
- [ ] Create Discord/Slack community
- [ ] Add contributing guidelines for first-time contributors
- [ ] Create good first issue labels
- [ ] Set up GitHub Sponsors

## Release Planning

- [ ] v0.1.0 - First stable release (after 100% coverage)
- [ ] v0.2.0 - YAML/TOML support
- [ ] v0.3.0 - Async support
- [ ] v1.0.0 - API stability guarantee

## Notes

- Keep backward compatibility in mind for all changes
- Follow semantic versioning strictly
- Ensure all new features have corresponding tests
- Update documentation for every public API change
