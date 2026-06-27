# AGENTS.md - AI Assistant Reference for wry

> For user-facing docs see README.md. For contributor guidelines see CONTRIBUTING.md.
> For version history see CHANGELOG.md. For release workflow see RELEASE_PROCESS.md.

---

## What is wry?

**wry** (Why Repeat Yourself?) is a Python library that eliminates repetitive CLI configuration by:

1. Defining configuration once in Pydantic models
2. Automatically generating Click CLI parameters
3. Supporting multiple configuration sources (CLI / ENV / JSON / DEFAULT)
4. Tracking exactly where each value came from
5. Enforcing strict precedence: **CLI > JSON > ENV > DEFAULT**

**Key innovation**: Source tracking — no other library tells you *where* each config value came from.

---

## Architecture Overview

```
wry/
├── __init__.py              # Public API exports
├── click_integration.py     # Click parameter generation (largest module)
├── auto_model.py            # AutoWryModel — zero-config model via __init_subclass__
├── multi_model.py           # Multi-model support (split_kwargs, create_models)
├── help_system.py           # Documentation system
├── comma_separated.py       # CommaSeparated list types
└── core/
    ├── model.py             # WryModel base class, from_click_context(), source tracking
    ├── sources.py           # ValueSource enum, TrackedValue, FieldWithSource
    ├── accessors.py         # Property accessors (source, minimum, maximum, etc.)
    ├── field_utils.py       # Constraint extraction from Pydantic fields
    └── env_utils.py         # Environment variable handling and type conversion
```

**Key classes**: `WryModel` (explicit annotations), `AutoWryModel` (auto-generates options for all fields)

**Key flow**: User defines Pydantic model -> `generate_click_parameters()` creates Click decorators -> `from_click_context()` builds model with source tracking

---

## Critical Gotchas

These are the most common issues that trip up both users and AI assistants.

### 1. `env_prefix` and other config must be ClassVar

```python
# WRONG - Pydantic treats as a field, generates CLI option, breaks config
class Config(AutoWryModel):
    env_prefix: str = "MYAPP_"

# CORRECT
class Config(AutoWryModel):
    wry_env_prefix: ClassVar[str] = "MYAPP_"
```

Without `ClassVar`, the attribute appears in `model_fields` and gets a CLI option generated. Use the `wry_` prefixed names (v0.6.0+). Old unprefixed names still work but emit deprecation warnings.

### 2. Source tracking requires context

```python
# NO source tracking - all sources show as CLI
@Config.generate_click_parameters()
def main(**kwargs):
    config = Config(**kwargs)  # Wrong

# FULL source tracking
@Config.generate_click_parameters()
@click.pass_context  # Required
def main(ctx: click.Context, **kwargs):
    config = Config.from_click_context(ctx, **kwargs)  # Correct
```

### 3. Boolean fields use on/off pattern by default (v0.6.0+)

```python
debug: bool = Field(default=False)
# Generates: --debug/--no-debug (not just --debug)

# Opt out to single flag:
debug: Annotated[bool, AutoOption(flag_enable_on_off=False)] = Field(default=False)
```

### 4. List fields auto-get multiple=True

```python
tags: list[str] = Field(default_factory=list)
# Usage: --tags python --tags rust (NOT --tags python,rust)

# For comma-separated: use Annotated[list[str], CommaSeparated]
# Or model-wide: wry_comma_separated_lists: ClassVar[bool] = True
```

### 5. Arguments are always optional in Click (for --config compatibility)

```python
input_file: Annotated[str, AutoArgument] = Field()
# Click sees required=False, but Pydantic still validates it's required
```

### 6. Click argument doesn't accept help parameter

wry works around this by injecting help text into the command docstring. Use `Field(description="...")` for argument help.

### 7. Click 8.4+ compatibility

Click 8.4.0 changed `ParameterSource` from a string-valued to integer-valued enum. wry v0.6.1+ handles this. If source tracking silently fails (all values show as DEFAULT), upgrade wry.

### 8. Pydantic 2.11+ deprecation

Use `cls.model_fields` or `self.__class__.model_fields`, never `self.model_fields` (deprecated).

### 9. eager_json_config must not modify param.default

The JSON config callback only sets `p.required = False` on fields found in JSON. It must NOT set `p.default = json_value` — doing so breaks Click's parameter source detection and causes CLI values to be treated as defaults. (Fixed in v0.2.2.)

### 10. Duplicate decorator detection

```python
@Config.generate_click_parameters()
@Config.generate_click_parameters()  # Error in strict mode (default)
```

---

## Correct vs Incorrect Patterns

### Pattern: Creating a config model

```python
# CORRECT - AutoWryModel for simple cases
class Config(AutoWryModel):
    wry_env_prefix: ClassVar[str] = "APP_"
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, ge=1, le=65535)

# CORRECT - WryModel for mixed arguments/options
class Config(WryModel):
    input_file: Annotated[str, AutoArgument] = Field(description="Input")
    format: Annotated[str, AutoOption] = Field(default="json")
    internal: Annotated[str, AutoExclude] = Field(default="")
```

### Pattern: Using aliases for CLI names

```python
class Config(AutoWryModel):
    # Python: config.db_url | CLI: --database-url | Env: APP_DATABASE_URL
    db_url: str = Field(alias="database_url", default="sqlite:///app.db")
```

No extra configuration needed — `validate_by_name=True` and `validate_by_alias=True` are set by WryModel.

### Pattern: Multi-model commands

```python
@click.command()
@multi_model(ServerConfig, DatabaseConfig)
@click.pass_context
def serve(ctx, **kwargs):
    configs = create_models(ctx, kwargs, ServerConfig, DatabaseConfig)
```

---

## Development Rules

### Pre-Commit Requirements

Before any commit, ensure:

1. **CHANGELOG.md**: Add entry under `[Unreleased]` for ANY change
2. **Tests**: Add/update tests, ensure all pass (`pytest`)
3. **Code quality**: Type annotations, docstrings, no dead code
4. **Linting**: `ruff check`, `ruff format`, `mypy` must pass
5. **TODO.md**: Mark completed tasks if applicable
6. **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

The pre-commit hook runs all checks automatically. **Never use `--no-verify`.**

### Code Style

- Type annotations on all functions (use `-> None` for void)
- Google-style docstrings on public API
- Fix linter errors properly — avoid `# type: ignore`, `# noqa`, `cast()` unless truly necessary
- Use `git rm` / `git mv` for tracked files (preserves history)

### Testing

- **Never skip/disable tests** to make suites pass — fix the issue
- Test all four sources: CLI, ENV, JSON, DEFAULT
- Test source tracking for new features
- Use `CliRunner` for Click command tests
- Coverage requirement: 90%+
- Test organization: `tests/unit/`, `tests/integration/`, `tests/features/`

### wry-Specific Rules

- All `WryModel`/`AutoWryModel` config attributes must use `ClassVar`
- Source tracking is a core feature — ensure it works for new features
- List fields auto-get `multiple=True` unless comma-separated is enabled
- Update README.md for user-facing changes, AGENTS.md for architecture/API changes
- See CONTRIBUTING.md for comprehensive guidelines

---

## Debugging Quick Reference

| User says | Check |
|-----------|-------|
| "Sources all show as CLI" | Using `@click.pass_context` + `from_click_context()`? |
| "CLI doesn't override config file" | Version >= 0.2.2? (bug fixed) |
| "Env vars not working" | `env_prefix` is `ClassVar`? Try `--show-env-vars` |
| "Required field not enforced" | Version >= 0.2.2? Has no default? Not satisfied by env/config? |
| "Argument help not showing" | Using `Field(description="...")`? Version >= 0.2.3? |
| "Field excluded but still in CLI" | Using `Annotated[str, AutoExclude]`? (not `AutoExclude[str]`) |
| "Source tracking shows DEFAULT for everything" | Click 8.4+ issue — upgrade wry to 0.6.1+ |

### Key Test Files

- `tests/features/test_source_precedence.py` — Tests all 4 sources with proper precedence
- `tests/features/test_inheritance.py` — Model inheritance scenarios
- `tests/features/test_auto_model.py` — AutoWryModel features

### Useful Commands

```bash
pytest                                          # All tests
pytest tests/features/test_source_precedence.py -xvs  # Key precedence test
pytest --cov=wry --cov-report=term-missing      # Coverage
python -m wry.help_system ai                    # This file via help system
./check.sh                                      # Pre-commit checks
```

---

## Key Files for Common Tasks

| Task | Files to modify |
|------|----------------|
| Add new field type support | `click_integration.py`, `env_utils.py`, tests |
| Add new source type | `sources.py`, `model.py` (from_click_context) |
| Change CLI generation | `click_integration.py`, `auto_model.py` |
| Fix source tracking | `model.py` (lines ~586-624) |
| Add new accessor | `accessors.py`, `model.py` (add @property) |
| Add new constraint | `field_utils.py`, `click_integration.py` (format_constraint_text) |

---

## Configuration Precedence (how it works internally)

`from_click_context()` builds config in 4 layers:

1. **DEFAULT** — Pydantic field defaults
2. **ENV** — `get_env_values()` reads `os.environ` with `env_prefix`
3. **JSON** — `ctx.obj['json_data']` from eager `--config` callback
4. **CLI** — `ctx.get_parameter_source()` checks for `COMMANDLINE`

Each layer overrides the previous. The result is a dict of `TrackedValue(value, source)` objects passed to `create_with_sources()`.

**Critical detail**: Click's `get_parameter_source()` returns an enum. wry uses `.name` (not `str()`) to check for `"COMMANDLINE"` — this is what Click 8.4+ compatibility depends on.
