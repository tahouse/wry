# TODO List for wry

## Current Sprint

### In Progress

- [ ] Achieve higher code coverage
  - Current coverage: ~90%
  - Target: 95%+ for core modules

### Completed (Recent)

- [x] Click 8.4+ compatibility fix (v0.6.1)
- [x] Boolean on/off flags (`--option/--no-option`) (v0.6.0)
- [x] Callable marker API: `AutoOption()`, `AutoArgument()`, `AutoExclude()` (v0.6.0)
- [x] wry-prefixed ClassVars for configuration (v0.6.0)
- [x] Comma-separated list support (v0.5.0)
- [x] Model inheritance support (v0.4.1)
- [x] Pydantic alias-based CLI option generation (v0.4.0)
- [x] Comprehensive test suite (538 tests, all passing)
- [x] Consolidated AI docs into AGENTS.md

## Future Enhancements

### High Priority

- [ ] **Short option aliases for CLI options**
  - Allow specifying short form: `--node/-n`, `--cluster/-c`
  - Possible API: `AutoOption(short='n')` or auto-generate from first letter
  - Need conflict detection

- [ ] **Document/improve environment variable support for arguments**
  - Arguments CAN use env vars via `from_click_context()` but it's not obvious
  - Add env var info to argument docstring injection
  - Document prominently in README

- [ ] Add support for YAML configuration files
- [ ] Add support for TOML configuration files
- [ ] Add async support for Click commands
- [ ] Create documentation site (Sphinx/MkDocs)

### Medium Priority

- [ ] Add support for configuration file validation/schema generation
- [ ] Create migration guide from plain Click to wry
- [ ] Add benchmarks comparing performance with plain Click

### Low Priority

- [ ] Add support for custom value source types
- [ ] Add support for remote configuration sources
- [ ] Create plugin system for extensions

## Technical Debt

- [ ] Use newer Python 3.10+ syntax where appropriate (Union types with `|`, etc.)
- [ ] Improve error messages for validation failures
- [ ] Optimize import times

## Documentation

- [ ] Create API documentation site
- [ ] Create comparison with similar libraries (Typer, Clidantic, etc.)

## Release Planning

- [ ] v0.7.0 - Short option aliases, YAML/TOML support
- [ ] v1.0.0 - API stability guarantee, remove deprecated v0.6.0 APIs

## Notes

- Keep backward compatibility in mind for all changes
- Follow semantic versioning strictly
- Ensure all new features have corresponding tests
- Update documentation for every public API change
