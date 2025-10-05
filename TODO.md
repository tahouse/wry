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

- [ ] **Short option aliases for CLI options**
  - Allow specifying short form: `--node/-n`, `--cluster/-c`
  - Challenge: Avoiding conflicts between short options
  - Possible API ideas:
    - Field metadata: `Field(..., short='n')`
    - Annotation: `Annotated[str, AutoOption(short='n')]`
    - Auto-generate from first letter (with conflict detection)
    - Allow custom mapping: `short_options = {"node": "n", "cluster": "c"}`
  - Need to handle conflicts gracefully (warn or error)
  - Should work with AutoWryModel and WryModel

- [ ] **Boolean flag negation (--no-flag / --skip-flag)**
  - Auto-generate negative form for boolean flags
  - Examples: `--debug/--no-debug`, `--verbose/--quiet`, `--enable/--disable`
  - Possible API ideas:
    - Auto from field name: `enable_feature` → `--enable-feature/--no-enable-feature`
    - Custom negative: `Field(..., negative='--quiet')` for `verbose` field
    - Pattern-based: `use_cache` → `--use-cache/--no-cache` or `--cache/--no-cache`
    - Click supports this: `click.option('--flag/--no-flag')`
  - Should respect user's choice (some bools shouldn't have negation)
  - May need new marker: `AutoFlag(negative=True)` vs `AutoFlag(negative=False)`

- [ ] **Document/improve environment variable support for arguments**
  - Current behavior: Arguments CAN use env vars via wry's layer system
    - `from_click_context()` applies env vars to ALL fields (including arguments)
    - Env var naming: `{prefix}{field_name.upper()}` (e.g., `MYAPP_INPUT_FILE`)
    - Already shows in `--show-env-vars` output
  - Issue: Not obvious to users that this works
    - Click's `click.argument()` doesn't support `envvar=` parameter natively
    - Help text doesn't indicate env var can be used
    - Only works when using `from_click_context()`, not plain `Config(**kwargs)`
  - Possible improvements:
    - Add env var info to argument docstring injection (like "Can also be set via MYAPP_INPUT_FILE")
    - Document this behavior prominently in README and examples
    - Consider adding note to `--help` output for arguments
    - Maybe add a section in help text: "Arguments can also be provided via environment variables"
  - Related: Ensure tests cover argument + env var interaction

- [x] **Custom CLI option names (beyond underscore-to-hyphen conversion)**
  - **✅ FULLY IMPLEMENTED (v0.3.2+): Automatic alias-based option generation!**
    - ✅ Aliases automatically control auto-generated CLI option names
    - ✅ Aliases automatically control environment variable names
    - ✅ `from_click_context()` recognizes aliases in kwargs
    - ✅ JSON config works with both field names and aliases
    - ✅ Source tracking works correctly with aliases
    - ✅ Comprehensive test coverage (tests/unit/click/test_field_alias_with_click_options.py)
    - ✅ Examples: `examples/autowrymodel_comprehensive.py` and `examples/wrymodel_comprehensive.py`
    - ✅ Documented in README under "Advanced Usage"

    **Simple pattern (auto-generated options):**
    ```python
    class Config(AutoWryModel):
        model_config = ConfigDict(populate_by_name=True)

        # Concise Python field: db_url
        # Alias controls CLI: --database-url
        # Env var: DB_DATABASE_URL
        db_url: str = Field(alias="database_url", default="sqlite:///app.db")
    ```

    **Advanced pattern (explicit click.option for short options):**
    ```python
    class Config(AutoWryModel):
        model_config = ConfigDict(populate_by_name=True)

        database_connection_string: Annotated[
            str,
            click.option("--db-url", "-d")
        ] = Field(alias='db_url', default="sqlite:///app.db")
    ```

  - Future enhancements:
    - Make `generate_click_parameters()` auto-use alias for option name
    - Add `cli_name` parameter to Field: `Field(..., cli_name="db-url")`
    - Add to AutoOption: `Annotated[str, AutoOption(name="db-url", short="d")]`
    - Auto-generate short options: `AutoOption(short=True)` → first letter if no conflict
    - Handle env var naming (use alias or field name?)
    - JSON config files (use alias or field name?)
  - Related to short option aliases feature above

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
