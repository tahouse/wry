# wry - Comprehensive AI/LLM Knowledge Base

**Last Updated**: 2025-10-01
**Version**: 0.2.3+
**Purpose**: Complete reference for AI assistants and LLMs to understand wry without reading the entire codebase

---

## Executive Summary

**wry** (Why Repeat Yourself?) is a Python library that eliminates repetitive CLI configuration by:

1. Defining configuration once in Pydantic models
2. Automatically generating Click CLI parameters
3. Supporting multiple configuration sources (CLI/ENV/JSON/DEFAULT)
4. Tracking exactly where each value came from
5. Enforcing strict precedence: CLI > ENV > JSON > DEFAULT

**Key Innovation**: Single source of truth for configuration with comprehensive source tracking.

**Stats**: 918 lines of code, 407 tests (all passing), 92% coverage, supports Python 3.10-3.12

---

## Table of Contents

1. [Core Architecture](#core-architecture)
2. [Module Reference](#module-reference)
3. [Class Hierarchy](#class-hierarchy)
4. [Configuration Flow](#configuration-flow)
5. [Source Tracking Deep Dive](#source-tracking-deep-dive)
6. [Click Integration](#click-integration)
7. [Common Patterns](#common-patterns)
8. [Edge Cases & Gotchas](#edge-cases--gotchas)
9. [Test Coverage](#test-coverage)
10. [API Reference](#api-reference)
11. [Debugging Guide](#debugging-guide)

---

## Core Architecture

### Directory Structure

```
wry/
├── __init__.py              # Public API exports, version handling
├── click_integration.py     # Click parameter generation (361 lines)
├── auto_model.py           # AutoWryModel implementation (57 lines)
├── multi_model.py          # Multi-model support (48 lines)
├── help_system.py          # Documentation system (89 lines)
└── core/
    ├── __init__.py         # Core exports
    ├── model.py            # WryModel base class (247 lines)
    ├── sources.py          # ValueSource, TrackedValue (26 lines)
    ├── accessors.py        # Property accessors (48 lines)
    ├── field_utils.py      # Constraint extraction (52 lines)
    └── env_utils.py        # Environment handling (58 lines)

tests/
├── features/               # End-to-end feature tests
│   ├── test_source_precedence.py  # ⭐ All 4 sources tested
│   ├── test_auto_model.py
│   └── test_multi_model.py
├── integration/            # Component integration tests
│   ├── test_click_integration.py
│   ├── test_click_integration_extended.py
│   ├── test_click_edge_cases.py
│   └── test_context_handling.py
└── unit/                   # Unit tests by module
    ├── core/               # WryModel, sources, accessors
    ├── click/              # Click integration (22 test files!)
    ├── model/              # Model functionality
    ├── auto_model/         # AutoWryModel
    └── multi_model/        # Multi-model

examples/
├── simple_cli.py                          # Basic usage
├── source_tracking_comprehensive.py       # ⭐ All 4 sources demo
├── source_tracking_example.py
├── explicit_argument_help.py              # Argument help
├── multi_model_example.py                 # Multiple models
├── field_exclusion_example.py             # AutoExclude
└── sample_config.json                     # Sample config
```

---

## Module Reference

### 1. `wry/core/model.py` - WryModel Base Class (247 lines)

**Purpose**: Core Pydantic model with source tracking

**Class Attributes**:

```python
class WryModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    env_prefix: ClassVar[str] = ""  # Environment variable prefix
    _value_sources: dict[str, ValueSource] = {}  # Tracks where values came from
    _accessor_instances: dict[str, Any] = {}  # Caches property accessors
```

**Property Accessors** (lazy-initialized, cached):

```python
@property
def source(self) -> SourceAccessor:
    """config.source.field_name → ValueSource.CLI/ENV/JSON/DEFAULT"""

@property
def minimum(self) -> MinimumAccessor:
    """config.minimum.field_name → int | float | None"""

@property
def maximum(self) -> MaximumAccessor:
    """config.maximum.field_name → int | float | None"""

@property
def constraints(self) -> ConstraintsAccessor:
    """config.constraints.field_name → dict[str, Any]"""

@property
def defaults(self) -> DefaultsAccessor:
    """config.defaults.field_name → Any"""
```

**Critical Methods**:

**`__init__(**data)`**:

```python
def __init__(self, **data: Any) -> None:
    super().__init__(**data)  # Pydantic validation
    if "_value_sources" not in data:
        self._value_sources = {}
        for field_name in self.__class__.model_fields:  # ⚠️ v0.2.2 fix
            if field_name in data:
                self._value_sources[field_name] = ValueSource.CLI
            else:
                self._value_sources[field_name] = ValueSource.DEFAULT
```

**`from_click_context(ctx, strict=None, **kwargs)`** (classmethod):
THE MAIN METHOD for creating configs with accurate source tracking.

```python
# Simplified algorithm:
1. Filter kwargs to only model fields
2. Get json_data from ctx.obj['json_data'] (from eager callback)
3. Get env_values via get_env_values()
4. Build config_data with precedence:
   a. Start with defaults (from model_fields)
   b. Override with env_values
   c. Override with json_data
   d. Override with kwargs if Click says COMMANDLINE
5. Call create_with_sources(config_data)

# Key source detection (lines 521-537):
param_source = ctx.get_parameter_source(field_name)
if param_source and "COMMANDLINE" in str(param_source):
    config_data[field_name] = TrackedValue(value, ValueSource.CLI)
    continue  # Don't fall through
# Skip if ENVIRONMENT - already handled in step 4b
```

**Other Methods**:

- `create_with_sources(config_data)` - Create from TrackedValue objects
- `from_json_file(path)` - Load from JSON file
- `to_json_file(path)` - Save to JSON file
- `load_from_env()` - Create from environment variables only
- `get_env_values()` - Get env var dict
- `print_env_vars()` - Pretty-print env vars
- `get_sources_summary()` - Group fields by source
- `get_value_source(field)` - Get source for one field
- `get_field_constraints/minimum/maximum/default/range(field)` - Field metadata
- `model_dump(**kwargs)` - Serialize (excludes accessors)
- `extract_subset(target_model)` - Extract matching fields
- `extract_subset_from(source, target_model)` - Class method version

### 2. `wry/core/sources.py` - Value Source Types (26 lines, 100% coverage)

```python
class ValueSource(Enum):
    """Enum representing where a configuration value came from."""
    CLI = "cli"          # --option value
    ENV = "env"          # $ENV_VAR
    JSON = "json"        # --config file.json
    DEFAULT = "default"  # Field default value

class TrackedValue:
    """Pairs a value with its source during merging."""
    def __init__(self, value: Any, source: ValueSource):
        self.value = value
        self.source = source

    def __repr__(self) -> str:
        return f"TrackedValue({self.value!r}, {self.source.value})"

class FieldWithSource:
    """Wrapper that acts like value but exposes .source attribute."""
    _value: Any
    _source: ValueSource

    @property
    def source(self) -> ValueSource:
        return self._source

    def __str__(self) -> str:
        return str(self._value)

    def __eq__(self, other) -> bool:
        # Compares values, not sources
```

**Usage**:

```python
# During merging:
tracked = TrackedValue("api.com", ValueSource.CLI)

# After instantiation:
field = config.get_field_with_source("host")  # Returns FieldWithSource
print(field)  # "api.com"
print(field.source)  # ValueSource.CLI
```

### 3. `wry/core/accessors.py` - Property Accessors (48 lines, 100% coverage)

**Why accessors?**

- Clean API: `config.source.field` vs `config._value_sources['field']`
- Lazy initialization: Only created when accessed
- Caching: Stored in `_accessor_instances` dict
- Type safety: Each accessor returns appropriate type

**Implementation Pattern**:

```python
class SourceAccessor:
    def __init__(self, config: WryModel):
        self._config = config

    def __getattr__(self, name: str) -> ValueSource:
        if name not in self._config.__class__.model_fields:
            raise AttributeError(f"Field '{name}' not found")
        return self._config._value_sources.get(name, ValueSource.DEFAULT)

    def __dir__(self) -> list[str]:
        return list(self._config.__class__.model_fields.keys())
```

**All Accessors**:

- `SourceAccessor` → `ValueSource`
- `MinimumAccessor` → `int | float | None`
- `MaximumAccessor` → `int | float | None`
- `ConstraintsAccessor` → `dict[str, Any]`
- `DefaultsAccessor` → `Any`

### 4. `wry/core/field_utils.py` - Constraint Extraction (52 lines, 97% coverage)

**`extract_field_constraints(field_info: FieldInfo) -> dict[str, Any]`**

Extracts constraints from:

1. **Pydantic Field**: ge, le, gt, lt, min_length, max_length, pattern, etc.
2. **annotated_types metadata**: Ge, Le, MinLen, MaxLen, Interval, MultipleOf, Predicate, etc.
3. **GroupedMetadata**: Nested constraint groups

**Returns dict** with all constraints, e.g.:

```python
{"ge": 0, "le": 100, "multiple_of": 5, "default": 50}
```

**Supported Constraints**:

- Numeric: ge, gt, le, lt, multiple_of
- Length: min_length, max_length
- String: pattern (regex)
- Interval: ge, gt, le, lt (from Interval type)
- Predicate: custom validation functions

**`get_field_minimum/maximum(field_info)`**:

- Extract just min or max constraint
- Returns `int | float | None`

### 5. `wry/core/env_utils.py` - Environment Variables (58 lines, 100% coverage)

**`get_env_var_names(model_class) -> dict[str, str]`**:

```python
# For model with env_prefix="MYAPP_"
# Returns: {"host": "MYAPP_HOST", "port": "MYAPP_PORT", ...}
```

**`get_env_values(model_class) -> dict[str, Any]`**:

```python
# Reads os.environ, converts types:
{
    "port": 9000,         # "9000" → int
    "debug": True,        # "true" → bool
    "timeout": 30.5       # "30.5" → float
}
```

**Type Conversion Logic**:

```python
if field_type is bool:
    lower = env_value.lower()
    if lower in ("true", "1", "yes", "on"): return True
    if lower in ("false", "0", "no", "off"): return False
elif field_type is int:
    return int(env_value)
elif field_type is float:
    return float(env_value)
else:
    return env_value  # Let Pydantic validate
```

**`print_env_vars(model_class)`**:
Prints formatted table of env vars (triggered by `--show-env-vars`).

### 6. `wry/click_integration.py` - Click Parameter Generation (361 lines, 88% coverage)

**This is the largest and most complex module.**

**`generate_click_parameters(model_class, add_config_option=True, strict=True)`**

**Main algorithm** (lines 314-620):

```python
def generate_click_parameters(model_class, add_config_option=True, strict=True):
    arguments = []
    options = []
    argument_docs = []  # For docstring injection

    # Loop through all model fields
    for field_name, field_info in model_class.model_fields.items():
        annotation = type_hints.get(field_name)

        # Extract metadata from Annotated[type, metadata...]
        metadata = get_args(annotation)[1:] if is_annotated else []

        # Determine field type
        field_type = None
        click_parameter = None
        for item in metadata:
            if item == AutoClickParameter.OPTION:
                field_type = OPTION
            elif item == AutoClickParameter.REQUIRED_OPTION:
                field_type = REQUIRED_OPTION
            elif item == AutoClickParameter.ARGUMENT:
                field_type = ARGUMENT
            elif item == AutoClickParameter.EXCLUDE:
                break  # Skip field
            elif is_click_decorator(item):
                click_parameter = item

        if field_type == EXCLUDE:
            continue

        if field_type in [OPTION, REQUIRED_OPTION]:
            # Generate click.option()
            option_name = f"--{field_name.replace('_', '-')}"

            # Determine if required
            is_required = field_info.is_required() or field_type == REQUIRED_OPTION

            # Build Click kwargs
            click_kwargs = {"help": field_info.description or field_name.title()}

            # Set default only if exists or not required
            if field_info.default is not PydanticUndefined:
                click_kwargs["default"] = field_info.default
            elif not is_required:
                click_kwargs["default"] = None
            # ⚠️ CRITICAL: Don't set default=None for required fields!

            # Determine Click type
            base_type = extract_base_type(annotation)
            if base_type is bool:
                click_kwargs["is_flag"] = True
            elif base_type is int:
                click_kwargs["type"] = click.INT
            # ... etc

            # Extract constraints and add to help
            constraints = extract_field_constraints(field_info)
            constraints_text = format_constraint_text(constraints)
            if constraints_text:
                click_kwargs["help"] += f" (Constraints: {', '.join(constraints_text)})"

            # Check if env var is set
            env_var_name = f"{env_prefix}{field_name.upper()}"
            env_var_set = env_var_name in os.environ

            # Only require in Click if Pydantic requires AND no env var
            click_required = is_required and not env_var_set

            option = click.option(option_name, **click_kwargs,
                                 required=click_required, envvar=env_var_name)
            options.append(option)

        elif field_type == ARGUMENT:
            # Generate click.argument()
            argument_name = field_name.lower()
            # ... (similar type handling)
            arguments.append(click.argument(argument_name, **click_kwargs, required=False))

            # Track for docstring injection
            if field_info.description:
                argument_docs.append((argument_name.upper(), field_info.description))

        elif click_parameter:
            # Explicit Click decorator
            if is_argument(click_parameter):
                modified_arg, arg_info = extract_and_modify_argument_decorator(click_parameter)
                arguments.append(modified_arg)

                # Extract help for docstring injection
                help_text = arg_info.get("help") or field_info.description
                if help_text:
                    arg_name = arg_info.get("param_decls", [field_name])[0].upper()
                    argument_docs.append((arg_name, help_text))
            else:
                options.append(click_parameter)

    # Add --config and --show-env-vars if requested
    if add_config_option:
        config_and_env_options.append(config_option())
    config_and_env_options.append(show_env_vars_option())

    def decorator(func):
        # Check for duplicate decoration (strict mode)
        if strict and hasattr(func, "_wry_decorated"):
            raise ValueError("Already decorated")
        func._wry_decorated = True

        # Inject argument help into docstring
        if argument_docs:
            arg_doc_section = build_arguments_section(argument_docs)
            func.__doc__ = (func.__doc__ or "").rstrip() + arg_doc_section

        # Apply decorators (arguments first, then options)
        all_decorators = arguments + config_and_env_options + options
        for dec in reversed(all_decorators):
            func = dec(func)

        return func

    return decorator
```

**Key Functions**:

**`config_option()`** (lines 293-311):
Returns decorator for `--config/-c` option with eager callback.

**`eager_json_config(ctx, param, value)`** (lines 724-764):

```python
# CRITICAL: is_eager=True, processes before other options
# 1. Load JSON file
# 2. Store in ctx.obj['json_data']
# 3. Mark JSON fields as not required
# 4. DON'T modify param.default (v0.2.2 fix!)
```

**`extract_and_modify_argument_decorator(decorator)`** (lines 621-680):

```python
# Returns: (modified_decorator, info_dict)
# Extracts from closure: param_decls, attrs (including help)
# Filters out 'help' before passing to click.argument()
# Sets required=False for --config compatibility
```

**`format_constraint_text(constraints)`** (lines 52-290):
Converts constraint dict to human-readable list:

```python
{"ge": 0, "le": 100} → ["≥ 0", "≤ 100"]
{"min_length": 3, "max_length": 50} → ["len: 3 to 50"]
{"pattern": "^[A-Z]+$"} → ["pattern: ^[A-Z]+$"]
```

### 7. `wry/auto_model.py` - AutoWryModel (57 lines, 90% coverage)

**Purpose**: Zero-configuration model

**Magic happens in `__init_subclass__`**:

```python
@classmethod
def __init_subclass__(cls, **kwargs):
    """Called when subclass is defined."""
    super().__init_subclass__(**kwargs)

    # Prevent re-processing
    if hasattr(cls, "_autowrymodel_processed"):
        return
    cls._autowrymodel_processed = True

    # Process all annotations
    for attr_name, annotation in cls.__annotations__.copy().items():
        if attr_name.startswith("_"):
            continue  # Skip private

        # Check if already Annotated with Click metadata
        if is_annotated(annotation):
            metadata = get_args(annotation)[1:]
            if has_click_metadata(metadata):
                continue  # Preserve explicit config

            # Add AutoOption to existing annotation
            base_type = get_args(annotation)[0]
            cls.__annotations__[attr_name] = Annotated[base_type, OPTION, *metadata]
        else:
            # Not annotated, add AutoOption
            cls.__annotations__[attr_name] = Annotated[annotation, OPTION]

    # Process Field() defined without annotations
    for attr_name in dir(cls):
        if attr_name in cls.__annotations__ or attr_name.startswith("_"):
            continue
        attr_value = getattr(cls, attr_name)
        if isinstance(attr_value, FieldInfo):
            field_type = attr_value.annotation or Any
            cls.__annotations__[attr_name] = Annotated[field_type, OPTION]
```

**Result**: All fields become `--options` unless explicitly configured.

**`create_auto_model(name, fields, **kwargs)`**:
Dynamic model creation at runtime.

### 8. `wry/multi_model.py` - Multi-Model Support (48 lines, 100% coverage)

**Purpose**: Multiple Pydantic models in single command

**Functions**:

**`split_kwargs_by_model(kwargs, *model_classes)`**:

```python
# Splits kwargs based on which model owns each field
kwargs = {"host": "x", "db_url": "y", "unknown": "z"}
result = split_kwargs_by_model(kwargs, ServerConfig, DatabaseConfig)
# → {
#     ServerConfig: {"host": "x"},
#     DatabaseConfig: {"db_url": "y"}
#   }
# Warns about unknown fields
```

**`create_models(ctx, kwargs, *model_classes)`**:

```python
# Creates instances with source tracking
configs = create_models(ctx, kwargs, ServerConfig, DatabaseConfig)
server = configs[ServerConfig]
db = configs[DatabaseConfig]
```

**`@multi_model(*model_classes, strict=False)`**:

```python
# Decorator that applies generate_click_parameters for each model
@multi_model(ServerConfig, DatabaseConfig)
def serve(ctx, **kwargs):
    # All options from both models available
```

**`singleton_option(*args, **kwargs)`**:
Wrapper around `click.option` that prevents duplicate options.

### 9. `wry/help_system.py` - Documentation System (89 lines)

**Purpose**: Programmatic access to documentation

**Functions**:

- `get_help_content(help_type)` - Returns help text as string
- `print_help(help_type, pager=True)` - Prints help with optional pager
- `show_help_index()` - Shows available topics

**Help Topics**:

- `readme` - Main README.md
- `ai` - This AI knowledge base
- `sources` - Source tracking section from AI KB
- `architecture` - Architecture section from README
- `examples` - List all examples with descriptions

**Usage**:

```bash
python -m wry.help_system              # Index
python -m wry.help_system ai           # AI KB
python -m wry.help_system examples     # List examples
```

```python
from wry import print_help, get_help_content
print_help('ai')                       # With pager
content = get_help_content('readme')   # As string
```

---

## Configuration Flow (Complete Diagram)

```
USER WRITES MODEL
│
├─> class Config(AutoWryModel):
│       env_prefix: ClassVar[str] = "APP_"
│       host: str = Field(default="localhost", description="Host")
│       port: int = Field(default=8080, ge=1, le=65535)
│
↓
PYTHON EXECUTES __init_subclass__ (for AutoWryModel)
│
├─> Scans annotations
├─> Adds AutoClickParameter.OPTION to all fields
│   Result: host, port both have AutoOption
│
↓
USER DECORATES COMMAND
│
├─> @Config.generate_click_parameters()
│
│   EXECUTION AT DECORATION TIME:
│   ├─> Loop model_fields
│   ├─> For each field:
│   │   ├─> Check AutoClickParameter type
│   │   ├─> Extract Field metadata (description, default, constraints)
│   │   ├─> Build Click kwargs
│   │   ├─> Create click.option() or click.argument()
│   │   └─> Add to decorators list
│   ├─> Add --config option (if requested)
│   ├─> Add --show-env-vars option
│   └─> Return decorator function
│
↓
USER RUNS COMMAND
│
├─> $ export APP_PORT=9000
├─> $ python app.py --config prod.json --host api.com
│
↓
CLICK PROCESSES (order matters!)
│
├─> 1. EAGER CALLBACKS (is_eager=True)
│   │
│   └─> eager_json_config():
│       ├─> Load prod.json → {"port": 5432, "debug": true}
│       ├─> Store in ctx.obj['json_data']
│       └─> Mark fields in JSON as not required
│
├─> 2. PARSE COMMAND LINE
│   ├─> --host api.com → ctx.params['host']
│   └─> Click detects: ParameterSource.COMMANDLINE
│
├─> 3. CHECK ENVIRONMENT VARIABLES
│   ├─> APP_PORT=9000 read by Click (envvar parameter)
│   └─> Click detects: ParameterSource.ENVIRONMENT
│
└─> 4. CALL COMMAND FUNCTION
    └─> def main(ctx, **kwargs):
        kwargs = {"host": "api.com", "port": 9000}
│
↓
from_click_context(ctx, **kwargs) CALLED
│
├─> 1. Filter kwargs to model fields
│
├─> 2. Get json_data from ctx.obj['json_data']
│   json_data = {"port": 5432, "debug": true}
│
├─> 3. Get environment values
│   env_values = get_env_values()
│   → {"port": 9000}  # APP_PORT read from os.environ
│
├─> 4. Build config_data with precedence:
│
│   Layer 1 - DEFAULTS:
│   config_data = {
│       "host": TrackedValue("localhost", DEFAULT),
│       "port": TrackedValue(8080, DEFAULT)
│   }
│
│   Layer 2 - ENV (overrides defaults):
│   config_data["port"] = TrackedValue(9000, ENV)
│
│   Layer 3 - JSON (overrides env):
│   config_data["port"] = TrackedValue(5432, JSON)
│   config_data["debug"] = TrackedValue(true, JSON)
│
│   Layer 4 - CLI (overrides all):
│   For "host" in kwargs:
│       param_source = ctx.get_parameter_source("host")
│       if "COMMANDLINE" in str(param_source):
│           config_data["host"] = TrackedValue("api.com", CLI)
│
│   For "port" in kwargs:
│       param_source = ctx.get_parameter_source("port")
│       if "ENVIRONMENT" in str(param_source):
│           continue  # Already handled in Layer 2
│
│   FINAL config_data = {
│       "host": TrackedValue("api.com", CLI),
│       "port": TrackedValue(9000, ENV),  # ENV, not CLI or JSON!
│       "debug": TrackedValue(true, JSON)
│   }
│
├─> 5. create_with_sources(config_data):
│   ├─> Extract values: {"host": "api.com", "port": 9000, "debug": true}
│   ├─> Create instance: Config(**values)
│   ├─> Set _value_sources: {"host": CLI, "port": ENV, "debug": JSON}
│   └─> Return configured instance
│
↓
RESULT
│
config.host = "api.com"        (source: CLI)
config.port = 9000             (source: ENV) ← Not CLI or JSON!
config.debug = True            (source: JSON)
```

---

## Source Tracking Deep Dive

### The _value_sources Dictionary

Every `WryModel` instance stores sources:

```python
config._value_sources = {
    'host': ValueSource.CLI,
    'port': ValueSource.ENV,
    'debug': ValueSource.JSON,
    'timeout': ValueSource.DEFAULT
}
```

### Click's Parameter Source

Click 8.0+ provides `ctx.get_parameter_source(param_name)`:

```python
# Returns: ParameterSource.COMMANDLINE / ENVIRONMENT / DEFAULT / PROMPT
source = ctx.get_parameter_source("host")
str(source)  # "ParameterSource.COMMANDLINE"
```

**wry uses this** to distinguish:

- User typed `--port 9000` (COMMANDLINE)
- Value from `$APP_PORT` env var (ENVIRONMENT)
- Value from Click default (DEFAULT)

### Source Detection Algorithm (Lines 521-537)

```python
for field_name in cls.model_fields:
    if field_name in filtered_kwargs:
        value = filtered_kwargs[field_name]

        try:
            param_source = ctx.get_parameter_source(field_name)
            if param_source is not None:
                source_str = str(param_source)

                if "COMMANDLINE" in source_str:
                    # User explicitly provided on CLI
                    config_data[field_name] = TrackedValue(value, ValueSource.CLI)
                    continue  # CRITICAL: Skip fallback

                # ENVIRONMENT or DEFAULT already handled in earlier layers
                continue
        except (AttributeError, RuntimeError):
            # get_parameter_source not available
            pass

        # Fallback: if value differs from current, assume CLI
        if field_name not in config_data or config_data[field_name].value != value:
            config_data[field_name] = TrackedValue(value, ValueSource.CLI)
```

**Why the complexity?**

- JSON values aren't in Click's parameter source tracking
- ENV values detected by Click, but we handle them earlier
- Need to avoid double-counting ENV as CLI

### The eager_json_config Bug (Fixed in v0.2.2)

**OLD CODE (Buggy)**:

```python
def eager_json_config(ctx, param, value):
    json_data = json.load(open(value))

    # Pre-fill ctx.params (for required field satisfaction)
    for key, val in json_data.items():
        if key not in ctx.params:
            ctx.params[key] = val  # ⚠️ This was OK

    # Modify parameter defaults
    for p in ctx.command.params:
        if p.name in json_data:
            p.required = False
            p.default = json_data[p.name]  # ❌ BUG! Breaks CLI override
```

**Why it was a bug**:

1. Setting `p.default = json_data[p.name]` made Click think JSON value was the default
2. When user provides `--host api.com`, Click sees it matches "new default"
3. Click marks it as `ParameterSource.DEFAULT`, not `COMMANDLINE`
4. wry's source tracking skips it (already handled)
5. JSON value wins instead of CLI! ❌

**NEW CODE (Fixed)**:

```python
def eager_json_config(ctx, param, value):
    json_data = json.load(open(value))

    # Store JSON data for later use
    ctx.ensure_object(dict)["json_data"] = json_data

    # Mark JSON fields as not required (allows JSON to satisfy requirements)
    for p in ctx.command.params:
        if p.name in json_data:
            p.required = False  # ✅ Only this, not p.default!
```

**Result**: CLI args properly detected as COMMANDLINE, override JSON values correctly.

---

## Edge Cases & Gotchas

### 1. env_prefix Must Be ClassVar ⚠️

```python
# WRONG - Creates a field, shadows parent
class Config(AutoWryModel):
    env_prefix: str = "MYAPP_"  # ❌

# CORRECT - Class attribute, not a field
class Config(AutoWryModel):
    env_prefix: ClassVar[str] = "MYAPP_"  # ✅
```

**Why this matters**:

- Without `ClassVar`, Pydantic treats it as a field
- Field appears in `model_fields`, gets CLI option generated
- Shadows `WryModel.env_prefix` class attribute
- Env var detection breaks

**How to detect**: Warning message about shadowing parent attribute.

### 2. Source Tracking Requires Context

```python
# NO source tracking ❌
@Config.generate_click_parameters()
def main(**kwargs):
    config = Config(**kwargs)
    # config.source.* always shows CLI

# FULL source tracking ✅
@Config.generate_click_parameters()
@click.pass_context
def main(ctx, **kwargs):
    config = Config.from_click_context(ctx, **kwargs)
    # config.source.* shows actual source
```

### 3. REQUIRED_OPTION Forces Validation

```python
# Without REQUIRED_OPTION:
api_key: str = Field(default="dev-key")
# → Optional in Click (has default)

# With REQUIRED_OPTION:
api_key: Annotated[str, AutoClickParameter.REQUIRED_OPTION] = Field(default="dev-key")
# → Required in Click (even though it has default)
```

**Use case**: Fields that must be explicitly set in production.

### 4. click.Argument Doesn't Accept help Parameter

This is a Click limitation. wry solves it:

```python
# User writes:
field: Annotated[str, click.argument("field", help="Help text")] = Field()

# wry extracts help, filters it out:
modified_arg = click.argument("field")  # No help parameter
# Then injects "Help text" into docstring
```

**Since v0.2.3**: Also falls back to `Field(description="...")`.

### 5. List Fields Auto-Get multiple=True

```python
tags: list[str] = Field(default_factory=list)

# Auto-generates:
click.option("--tags", multiple=True, type=click.STRING)

# Usage:
# --tags python --tags rust --tags go
# Result: tags=["python", "rust", "go"]
```

### 6. Optional Types Handled

```python
timeout: Optional[int] = Field(default=None)

# wry extracts int from Optional[int]
# Generates: click.option("--timeout", type=click.INT, default=None)
```

### 7. Boolean Fields Become Flags

```python
debug: bool = Field(default=False)

# Auto-generates:
click.option("--debug", is_flag=True)

# Usage: --debug (sets to True)
# NOT: --debug true (doesn't work with flags)
```

### 8. Arguments Are Always Optional (For --config)

```python
# In model:
input_file: Annotated[str, AutoArgument] = Field()

# Generated:
click.argument("input_file", required=False)  # ⚠️ required=False!
```

**Why?** Allows `--config` to provide the value. Pydantic still validates it's required.

### 9. Accessing model_fields on Instance (Deprecated in Pydantic 2.11+)

```python
# DEPRECATED ❌
config.model_fields

# CORRECT ✅
Config.model_fields
# or
config.__class__.model_fields
```

**Fixed in v0.2.2** throughout wry codebase.

### 10. Duplicate Decorator Detection

```python
# Default: strict=True
@Config.generate_click_parameters()
@Config.generate_click_parameters()  # ❌ Error!

# Allow (not recommended):
@Config.generate_click_parameters(strict=False)
@Config.generate_click_parameters(strict=False)  # ⚠️ Warning
```

---

## Common Patterns

### Pattern 1: Simple AutoWryModel

```python
from wry import AutoWryModel
from pydantic import Field

class Config(AutoWryModel):
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, ge=1, le=65535)
    debug: bool = Field(default=False)

@click.command()
@Config.generate_click_parameters()
def main(**kwargs):
    config = Config(**kwargs)
    print(f"{config.host}:{config.port}")
```

**Generates**:

- `--host TEXT` (default: localhost)
- `--port INTEGER` (default: 8080, constraints: ≥ 1, ≤ 65535)
- `--debug` (flag)
- `--config FILE`
- `--show-env-vars`

### Pattern 2: Full Source Tracking

```python
from typing import ClassVar
from wry import AutoWryModel, ValueSource

class Config(AutoWryModel):
    env_prefix: ClassVar[str] = "MYAPP_"
    host: str = Field(default="localhost")
    port: int = Field(default=8080)

@click.command()
@Config.generate_click_parameters()
@click.pass_context  # ⚠️ Required
def main(ctx, **kwargs):  # ⚠️ ctx parameter required
    config = Config.from_click_context(ctx, **kwargs)  # ⚠️ Not Config(**kwargs)

    # Access sources
    print(f"Host from: {config.source.host.value}")  # "cli" or "env" or "json" or "default"

    # Get summary
    for source, fields in config.get_sources_summary().items():
        if fields:
            print(f"{source.value.upper()}: {', '.join(fields)}")
```

### Pattern 3: Mixed Arguments and Options

```python
from wry import WryModel, AutoOption, AutoArgument

class Config(WryModel):
    # Positional arguments
    input_file: Annotated[str, AutoArgument] = Field(description="Input file path")
    output_file: Annotated[str, AutoArgument] = Field(default="output.txt", description="Output path")

    # Options
    format: Annotated[str, AutoOption] = Field(default="json", description="Output format")
    verbose: Annotated[bool, AutoOption] = Field(default=False)

@click.command()
@Config.generate_click_parameters()
def main(**kwargs):
    config = Config(**kwargs)
    # Usage: python app.py input.txt output.txt --format yaml --verbose
```

### Pattern 4: Explicit Click Decorators

```python
import click
from wry import AutoWryModel

class Config(AutoWryModel):
    # Custom Click Path type
    logfile: Annotated[
        str,
        click.argument("logfile", type=click.Path(exists=True, path_type=str))
    ] = Field(description="Log file to analyze")

    # Custom Click Choice
    format: Annotated[
        str,
        click.option("--format", "-f", type=click.Choice(["json", "yaml", "xml"]))
    ] = Field(default="json", description="Output format")

    # Regular auto-generated option
    verbose: bool = Field(default=False, description="Verbose output")
```

### Pattern 5: Multi-Model

```python
from wry import WryModel, AutoOption, multi_model, create_models

class ServerConfig(WryModel):
    host: Annotated[str, AutoOption] = "localhost"
    port: Annotated[int, AutoOption] = 8080

class DatabaseConfig(WryModel):
    db_url: Annotated[str, AutoOption] = "sqlite:///app.db"
    pool_size: Annotated[int, AutoOption] = 5

@click.command()
@multi_model(ServerConfig, DatabaseConfig)
@click.pass_context
def serve(ctx, **kwargs):
    configs = create_models(ctx, kwargs, ServerConfig, DatabaseConfig)
    server = configs[ServerConfig]
    db = configs[DatabaseConfig]

    print(f"Server: {server.host}:{server.port}")
    print(f"DB: {db.db_url} (pool={db.pool_size})")
```

### Pattern 6: Field Exclusion

```python
from wry import AutoWryModel, AutoExclude

class Config(AutoWryModel):
    # Regular fields (become options)
    host: str = "localhost"
    port: int = 8080

    # Excluded from CLI (internal use)
    session_token: Annotated[str, AutoExclude] = Field(default="")
    last_updated: Annotated[datetime, AutoExclude] = Field(default_factory=datetime.now)
```

**Use cases**:

- Internal state
- Computed values
- Polymorphic validation fields
- Secrets not from CLI

---

## Test Coverage Details

### Test Statistics

- **Total Tests**: 407 (all passing)
- **Total Coverage**: 92%
- **Core Modules**: 100% coverage (sources, accessors, env_utils, multi_model)
- **Test Files**: 50+ test files
- **Lines of Test Code**: ~3000 lines

### Critical Test Files

**`tests/features/test_source_precedence.py`** ⭐ MOST IMPORTANT

```python
class TestSourcePrecedence:
    def test_complete_precedence_chain(self):
        """Tests ALL 4 sources with proper precedence."""
        # Sets env vars: TESTAPP_NAME, TESTAPP_PORT, etc.
        # Creates JSON config: {"name": "json", "port": 9090}
        # Provides CLI args: --name cli-name --port 8888
        # Verifies: CLI > JSON > ENV > DEFAULT

    def test_partial_sources(self):
        """Tests when only some sources provide values."""
        # field1: DEFAULT only
        # field2: ENV < JSON (JSON wins)
        # field3: JSON < CLI (CLI wins)
        # field4: DEFAULT < CLI (CLI wins)

    def test_type_conversion_across_sources(self):
        """Tests type conversion from all sources."""
        # ENV: "42" → int, "true" → bool, "3.14" → float
        # JSON: native types
        # CLI: Click-converted types

    def test_missing_required_field_fallback(self):
        """Tests required fields from different sources."""
        # Required from ENV
        # Required from JSON
        # Required from CLI
        # Missing required (should error)
```

**Run this test to verify precedence**:

```bash
pytest tests/features/test_source_precedence.py::TestSourcePrecedence::test_complete_precedence_chain -xvs
```

### Coverage by Module

```
wry/__init__.py              91%  (21 lines)
wry/auto_model.py            90%  (57 lines)
wry/click_integration.py     88%  (361 lines)
wry/help_system.py           NEW  (89 lines)
wry/core/model.py            94%  (247 lines)
wry/core/sources.py         100%  (26 lines)
wry/core/accessors.py       100%  (48 lines)
wry/core/field_utils.py      97%  (52 lines)
wry/core/env_utils.py       100%  (58 lines)
wry/multi_model.py          100%  (48 lines)
```

### Test Categories

1. **Source Precedence** (4 tests in test_source_precedence.py)
   - Complete chain, partial sources, type conversion, required fields

2. **Click Integration** (50+ tests)
   - Parameter generation, constraint formatting, type handling
   - Argument help injection, explicit decorators
   - Edge cases, error handling

3. **Core Functionality** (30+ tests)
   - WryModel creation, source tracking
   - Accessors, constraints, environment
   - TrackedValue, FieldWithSource

4. **AutoWryModel** (15+ tests)
   - Field processing, annotation inference
   - Edge cases, ClassVar handling

5. **Multi-Model** (10+ tests)
   - Kwargs splitting, model creation
   - Decorator application

6. **Integration** (20+ tests)
   - Click context handling
   - End-to-end scenarios

---

## API Reference

### Classes

```python
# Main Classes
class WryModel(BaseModel)
    """Base model with source tracking."""

class AutoWryModel(WryModel)
    """Auto-generates options for all fields."""

class ValueSource(Enum)
    """CLI, ENV, JSON, DEFAULT"""

class TrackedValue
    """Pairs value with source during merging."""

class FieldWithSource
    """Value wrapper exposing .source attribute."""

class AutoClickParameter(Enum)
    """OPTION, REQUIRED_OPTION, ARGUMENT, EXCLUDE"""

# Accessors (returned by @property)
class SourceAccessor
class MinimumAccessor
class MaximumAccessor
class ConstraintsAccessor
class DefaultsAccessor
```

### Functions

```python
# Click Integration
generate_click_parameters(model_class, add_config_option=True, strict=True) → decorator
config_option() → Callable
eager_json_config(ctx, param, value) → Any
build_config_with_sources(ctx, config_class, **kwargs) → instance
extract_and_modify_argument_decorator(decorator) → tuple[decorator, info_dict]
format_constraint_text(constraints) → list[str]

# Multi-Model
multi_model(*model_classes, strict=False) → decorator
create_models(ctx, kwargs, *model_classes) → dict[type, instance]
split_kwargs_by_model(kwargs, *model_classes) → dict[type, dict]
singleton_option(*args, **kwargs) → decorator

# Auto Model
create_auto_model(name, fields, **kwargs) → type[AutoWryModel]

# Field Utilities
extract_field_constraints(field_info) → dict[str, Any]
get_field_minimum(field_info) → int | float | None
get_field_maximum(field_info) → int | float | None

# Environment
get_env_var_names(model_class) → dict[str, str]
get_env_values(model_class) → dict[str, Any]
print_env_vars(model_class) → None

# Help System
get_help_content(help_type) → str
print_help(help_type, pager=True) → None
show_help_index() → None
```

### WryModel Instance API

```python
config = Config(...)

# Source Tracking
config.source.field_name                    → ValueSource
config.get_value_source("field")            → ValueSource
config.get_sources_summary()                → dict[ValueSource, list[str]]
config.get_field_with_source("field")       → FieldWithSource

# Constraints
config.constraints.field_name               → dict[str, Any]
config.minimum.field_name                   → int | float | None
config.maximum.field_name                   → int | float | None
config.defaults.field_name                  → Any
config.get_field_constraints("field")       → dict[str, Any]
config.get_field_minimum("field")           → int | float | None
config.get_field_maximum("field")           → int | float | None
config.get_field_range("field")             → tuple[min | None, max | None]
config.get_field_default("field")           → Any

# Serialization
config.model_dump(**kwargs)                 → dict (excludes accessors)
config.to_json_file(path)                   → None

# Extraction
config.extract_subset(TargetModel)          → dict[str, Any]
```

### WryModel Class API

```python
# Creation Methods
Config(**data)                              → instance (simple, basic source tracking)
Config.create_with_sources(config_data)     → instance (from TrackedValue dict)
Config.from_click_context(ctx, **kwargs)    → instance (⭐ full source tracking)
Config.from_json_file(path)                 → instance (all from JSON)
Config.load_from_env()                      → instance (all from ENV)

# Environment
Config.get_env_values()                     → dict[str, Any]
Config.print_env_vars()                     → None

# Click Integration
Config.generate_click_parameters(...)       → decorator

# Extraction
Config.extract_subset_from(source, target)  → dict[str, Any]
```

---

## Debugging Guide

### Problem: "My environment variables aren't being used!"

**Checklist**:

1. ✅ Is `env_prefix` a `ClassVar`?

   ```python
   env_prefix: ClassVar[str] = "MYAPP_"  # Not: env_prefix: str
   ```

2. ✅ Are variable names correct?

   ```bash
   # Run this to see expected names:
   python myapp.py --show-env-vars

   # Format: {PREFIX}{FIELDNAME_UPPER}
   # Field "host" with prefix "MYAPP_" → MYAPP_HOST
   ```

3. ✅ Are environment variables exported?

   ```bash
   export MYAPP_HOST=test.com
   env | grep MYAPP  # Verify it's set
   ```

4. ✅ Using `from_click_context()`?

   ```python
   # This won't show ENV source:
   config = Config(**kwargs)  # ❌

   # This will:
   config = Config.from_click_context(ctx, **kwargs)  # ✅
   ```

### Problem: "CLI arguments aren't overriding my config file!"

**This was a bug fixed in v0.2.2.**

**Check version**:

```bash
python -c "import wry; print(wry.__version__)"
# Should be ≥ 0.2.2
```

**If still failing**:

1. Are you using `from_click_context()`?
2. Check test: `pytest tests/features/test_source_precedence.py::TestSourcePrecedence::test_complete_precedence_chain -xvs`

### Problem: "Required field not enforced!"

**Fixed in v0.2.2.** Check:

1. ✅ Version ≥ 0.2.2?
2. ✅ Field is actually required?

   ```python
   # Required (no default):
   api_key: str = Field(description="API key")  # ✅

   # Not required (has default):
   api_key: str = Field(default="dev-key")  # ❌ Not required

   # Force required even with default:
   api_key: Annotated[str, AutoClickParameter.REQUIRED_OPTION] = Field(default="x")  # ✅
   ```

3. ✅ Not satisfied by env var or config file?

   ```bash
   # If MYAPP_API_KEY is set, Click won't enforce it
   unset MYAPP_API_KEY
   ```

### Problem: "Source tracking shows everything as CLI!"

**You're not using the context!**

```python
# WRONG ❌
@click.command()
@Config.generate_click_parameters()
def main(**kwargs):  # No ctx parameter
    config = Config(**kwargs)  # Direct instantiation
    # Result: All sources show as CLI

# CORRECT ✅
@click.command()
@Config.generate_click_parameters()
@click.pass_context  # Add this
def main(ctx, **kwargs):  # Add ctx parameter
    config = Config.from_click_context(ctx, **kwargs)  # Use this
    # Result: Accurate source tracking
```

### Problem: "Argument help text not showing in --help"

**Fixed in v0.2.3.**

**Solution**:

```python
# Use Field(description="..."):
input_file: Annotated[str, AutoArgument] = Field(
    description="Input file to process"  # ✅ This will appear in help
)

# Or with explicit click.argument:
logfile: Annotated[
    str,
    click.argument("logfile", type=click.Path(exists=True))
] = Field(
    description="Log file to analyze"  # ✅ Also works (v0.2.3+)
)
```

### Problem: "Getting Pydantic deprecation warning"

**Fixed in v0.2.2.**

```python
# Don't do this:
config.model_fields  # ❌ Deprecated in Pydantic 2.11+

# Do this:
Config.model_fields  # ✅
# or
config.__class__.model_fields  # ✅
```

### Problem: "Field excluded but still appears in CLI"

**Check the annotation**:

```python
# WRONG - AutoExclude not in Annotated
excluded: AutoExclude[str] = "value"  # ❌

# CORRECT
from wry import AutoExclude
excluded: Annotated[str, AutoExclude] = Field(default="value")  # ✅
```

### Debugging Commands

```bash
# Show environment variables
python myapp.py --show-env-vars

# Test source tracking interactively
python examples/source_tracking_comprehensive.py
export MYAPP_TIMEOUT=120
python examples/source_tracking_comprehensive.py --config examples/sample_config.json --port 3000

# Run specific test
pytest tests/features/test_source_precedence.py -xvs

# Check coverage
pytest --cov=wry --cov-report=term-missing

# Test all Python versions (requires them installed)
./scripts/test_all_versions.sh

# Run pre-commit checks
./check.sh
```

---

## Examples Reference

### Essential Examples

**`examples/source_tracking_comprehensive.py`** ⭐ **START HERE**

- Demonstrates ALL 4 sources (DEFAULT, ENV, JSON, CLI)
- Color-coded output showing source for each field
- Interactive - try different combinations
- Includes sample commands in docstring

**`examples/simple_cli.py`**

- Bare minimum AutoWryModel usage
- Good starting point for beginners

**`examples/source_tracking_example.py`**

- Basic source tracking demonstration
- Shows `from_click_context()` usage

### Advanced Examples

**`examples/multi_model_example.py`**

- Multiple models in one command
- Server, Database, Security configs
- Shows `multi_model()` and `create_models()`

**`examples/explicit_argument_help.py`**

- Both AutoArgument and explicit click.argument
- Field description injection
- Shows Arguments section in help

**`examples/field_exclusion_example.py`**

- Using AutoExclude
- Hiding internal fields
- Polymorphic models

**`examples/auto_model_example.py`**

- AutoWryModel features
- Zero-config approach

**`examples/intermediate_example.py`**

- Custom env_prefix
- Type validation
- Constraint access

### Proof of Concept

**`examples/auto_instantiate_poc.py`**

- Future feature exploration
- Automatic model instantiation
- Cleaner API

---

## Implementation Details

### Why object.**setattr** in Accessors?

```python
@property
def source(self) -> SourceAccessor:
    if "source" not in self._accessor_instances:
        accessor = SourceAccessor(self)
        object.__setattr__(self, "_accessor_instances",
                          {**self._accessor_instances, "source": accessor})
    # ...
```

**Reason**:

- Pydantic may have custom `__setattr__` that validates fields
- `object.__setattr__` bypasses this to directly modify instance dict
- Prevents spurious validation errors on internal attributes

### Why Arguments Before Options?

**Click requirement**: Decorators apply in reverse, arguments must be registered first.

```python
# wry handles this:
all_decorators = arguments + options
for dec in reversed(all_decorators):  # Reverse!
    func = dec(func)

# Applied as:
@option  # Last
@argument  # First
def func(): pass
```

### Why TrackedValue Class?

**Design choice**: Encapsulates value + source together during merging.

**Alternative** would be two dicts:

```python
# Alternative:
values = {"host": "api.com"}
sources = {"host": ValueSource.CLI}

# Chosen design:
config_data = {"host": TrackedValue("api.com", ValueSource.CLI)}
```

**Benefits**: Atomic updates, clearer code, type safety.

### Why model_dump() Excludes Accessors?

```python
def model_dump(self, **kwargs) -> dict[str, Any]:
    data = super().model_dump(**kwargs)
    accessor_keys = {"source", "minimum", "maximum", "constraints", "defaults"}
    return {k: v for k, v in data.items() if k not in accessor_keys}
```

**Reason**:

- Accessors are `@property` objects, not data
- They don't have meaningful serialized form
- Excluding them keeps dumps clean

### Constraint Text Formatting Logic

**Handles many constraint types** (lines 52-290):

```python
def format_constraint_text(constraints: dict[str, Any]) -> list[str]:
    text = []

    # Numeric bounds
    if "ge" in constraints and "le" in constraints:
        text.append(f"≥ {constraints['ge']}, ≤ {constraints['le']}")
    elif "ge" in constraints:
        text.append(f"≥ {constraints['ge']}")
    # ... more combinations

    # Length
    if "min_length" in constraints and "max_length" in constraints:
        text.append(f"len: {constraints['min_length']} to {constraints['max_length']}")

    # Pattern
    if "pattern" in constraints:
        text.append(f"pattern: {constraints['pattern']}")

    # Multiple of
    if "multiple_of" in constraints:
        text.append(f"multiple of {constraints['multiple_of']}")

    # Predicate
    if "predicate" in constraints:
        func = constraints["predicate"]
        text.append(f"matches predicate: {func.__name__}")

    return text
```

**Result in help**:

```
--age INTEGER  Your age (Constraints: ≥ 0, ≤ 120)  [default: 25]
--name TEXT    Your name (Constraints: len: 3 to 50)
```

---

## Version History (Critical Changes)

### v0.2.3 (2025-10-01) - Argument Help & Documentation

**Fixed**:

- Explicit `click.argument` now uses `Field(description)` for help text
- Help text extraction falls back to field_info.description
- Help parameter filtered before passing to Click

**Added**:

- AI Knowledge Base (this document)
- Integrated help system (`wry.help_system`)
- Comprehensive source tracking example
- Enhanced README source tracking section

**Tests**: 407 passing, 92% coverage

### v0.2.2 (2025-10-01) - Critical Bug Fixes ⚠️

**Fixed**:

- **Pydantic V2.11+ deprecation**: `self.model_fields` → `self.__class__.model_fields`
- **CLI precedence bug**: CLI now properly overrides JSON (eager_json_config fix)
- **REQUIRED_OPTION enforcement**: Required fields without defaults now validated

**Breaking**: `eager_json_config` no longer modifies `param.default`

**Added**: 38 new tests (365 → 403)
**Coverage**: 91% → 92%

**Impact**: Critical fixes for production use. Update recommended.

### v0.2.1 (2025-09-29) - Argument Help

**Added**:

- Automatic argument help injection into docstrings
- AutoExclude convenience alias

**Why important**: Click doesn't show argument help by default. wry fixes this.

### v0.2.0 (2025-09-29) - Field Exclusion

**Added**:

- Field exclusion with `AutoClickParameter.EXCLUDE`
- Build system improvements

### v0.1.9 (2025-09-29) - List Support

**Added**:

- Automatic `multiple=True` for `list[T]` and `tuple[T, ...]` fields
**Fixed**:
- Variadic argument bug (nargs=-1)

---

## Best Practices for AI/LLMs

### When Helping Users with wry

1. **Start with AutoWryModel** for simple cases
2. **Always recommend ClassVar for env_prefix**
3. **Always suggest source tracking** with `@click.pass_context`
4. **Point to examples/** for concrete patterns
5. **Check version** - critical fixes in v0.2.2
6. **Run interactive examples** to demonstrate

### Quick Diagnostic Questions

**User says**: "Sources are all showing as CLI"
→ **Ask**: "Are you using `@click.pass_context` and `from_click_context()`?"

**User says**: "CLI arguments not overriding config file"
→ **Ask**: "What version? This was fixed in v0.2.2."

**User says**: "Environment variables not working"
→ **Ask**: "Is `env_prefix` a ClassVar? Try `--show-env-vars` to see expected names."

**User says**: "Required field not enforced"
→ **Ask**: "Version ≥ v0.2.2? Field has no default? Check if env/config satisfying it."

**User says**: "Argument help not showing"
→ **Ask**: "Using `Field(description="...")`? Version ≥ v0.2.3?"

### Code Pattern Recognition

**Pattern**: Class attribute without ClassVar

```python
class Config(AutoWryModel):
    env_prefix = "MYAPP_"  # ⚠️ Missing ClassVar
```

**Suggest**: `env_prefix: ClassVar[str] = "MYAPP_"`

**Pattern**: Direct instantiation with context available

```python
@click.pass_context
def main(ctx, **kwargs):
    config = Config(**kwargs)  # ⚠️ Not using context
```

**Suggest**: `config = Config.from_click_context(ctx, **kwargs)`

**Pattern**: Trying to use help on click.argument

```python
field: Annotated[str, click.argument("field", help="Help")] = Field()  # ⚠️
```

**Inform**: "Click arguments don't support help parameter. Use `Field(description='Help')` instead (wry injects it into docstring)."

---

## Quick Start Templates

### Template 1: Minimal CLI

```python
import click
from pydantic import Field
from wry import AutoWryModel

class Config(AutoWryModel):
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port")

@click.command()
@Config.generate_click_parameters()
def main(**kwargs):
    config = Config(**kwargs)
    print(f"Connecting to {config.host}:{config.port}")

if __name__ == "__main__":
    main()
```

**Run**: `python app.py --host example.com --port 3000`

### Template 2: Full-Featured with Source Tracking

```python
import click
from typing import Annotated, ClassVar
from pydantic import Field
from wry import AutoWryModel, AutoArgument, AutoExclude, ValueSource

class Config(AutoWryModel):
    """Application configuration."""

    env_prefix: ClassVar[str] = "MYAPP_"

    # Positional argument
    input_file: Annotated[str, AutoArgument] = Field(
        description="Input file to process"
    )

    # Required option
    api_key: Annotated[str, AutoClickParameter.REQUIRED_OPTION] = Field(
        description="API authentication key"
    )

    # Optional fields
    output: str = Field(default="output.txt", description="Output file")
    verbose: bool = Field(default=False, description="Verbose logging")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")

    # Excluded from CLI
    _internal_state: Annotated[str, AutoExclude] = Field(default="")

@click.command()
@Config.generate_click_parameters()
@click.pass_context  # ⚠️ Required for source tracking
def main(ctx, **kwargs):  # ⚠️ ctx parameter required
    """Process files with configuration."""
    config = Config.from_click_context(ctx, **kwargs)

    # Show configuration and sources
    print(f"Processing: {config.input_file}")
    print(f"Output: {config.output}")
    print(f"Verbose: {config.verbose}")

    # Show sources
    print("\nConfiguration sources:")
    for source, fields in config.get_sources_summary().items():
        if fields:
            print(f"  {source.value.upper()}: {', '.join(fields)}")

if __name__ == "__main__":
    main()
```

**Run examples**:

```bash
# With environment variables
export MYAPP_API_KEY=secret
export MYAPP_VERBOSE=true
python app.py input.txt

# With config file
python app.py input.txt --config prod.json

# Mix all sources
export MYAPP_TIMEOUT=60
python app.py input.txt --config prod.json --output results.txt
```

### Template 3: Multi-Model Command

```python
import click
from typing import Annotated, ClassVar
from pydantic import Field
from wry import WryModel, AutoOption, multi_model, create_models

class ServerConfig(WryModel):
    """Server configuration."""
    env_prefix: ClassVar[str] = "SERVER_"

    host: Annotated[str, AutoOption] = Field(default="localhost", description="Server host")
    port: Annotated[int, AutoOption] = Field(default=8080, ge=1, le=65535)

class DatabaseConfig(WryModel):
    """Database configuration."""
    env_prefix: ClassVar[str] = "DB_"

    url: Annotated[str, AutoOption] = Field(
        default="sqlite:///app.db", description="Database URL"
    )
    pool_size: Annotated[int, AutoOption] = Field(default=5, ge=1, le=100)

@click.command()
@multi_model(ServerConfig, DatabaseConfig)
@click.pass_context
def serve(ctx, **kwargs):
    """Start server with database connection."""
    # Create both models from kwargs
    configs = create_models(ctx, kwargs, ServerConfig, DatabaseConfig)

    server = configs[ServerConfig]
    db = configs[DatabaseConfig]

    print(f"Starting server at {server.host}:{server.port}")
    print(f"Database: {db.url} (pool size: {db.pool_size})")

    # Check sources
    print(f"\nServer config from: {server.get_sources_summary()}")
    print(f"DB config from: {db.get_sources_summary()}")

if __name__ == "__main__":
    serve()
```

**Run**:

```bash
export SERVER_PORT=3000
export DB_POOL_SIZE=20
python app.py --host api.com --url postgresql://localhost/mydb
```

---

## Advanced Topics

### Custom Type Handling

```python
from click import ParamType

class EmailType(ParamType):
    """Custom Click type for email validation."""
    name = "email"

    def convert(self, value, param, ctx):
        if "@" not in value or "." not in value:
            self.fail(f"{value} is not a valid email address")
        return value.lower()

class Config(WryModel):
    # Use custom Click type
    email: Annotated[str, click.option("--email", type=EmailType())] = Field(
        description="Email address"
    )
```

### Pydantic Validators Work Normally

```python
from pydantic import field_validator, model_validator

class Config(AutoWryModel):
    email: str = Field(description="Email address")
    confirm_email: str = Field(description="Confirm email")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()

    @model_validator(mode='after')
    def validate_emails_match(self):
        if self.email != self.confirm_email:
            raise ValueError("Emails don't match")
        return self
```

**These run AFTER** Click processing, during Pydantic instantiation.

### Dynamic Model Creation

```python
from wry import create_auto_model
from pydantic import Field

# Create model at runtime
Config = create_auto_model(
    "RuntimeConfig",
    {
        "host": Field(default="localhost", description="Server host"),
        "port": (int, Field(default=8080, ge=1, le=65535)),  # Tuple form
        "debug": (bool, Field(default=False)),
    },
    env_prefix="RUNTIME_"
)

# Use like any AutoWryModel
@click.command()
@Config.generate_click_parameters()
def main(**kwargs):
    config = Config(**kwargs)
    print(f"{config.host}:{config.port}")
```

**Use cases**:

- Plugin systems
- Configuration-driven apps
- Testing/mocking

### Nested Model Flattening

wry doesn't auto-generate CLI for nested models. **Flatten instead**:

```python
# Instead of:
class DatabaseConfig(BaseModel):
    host: str
    port: int

class AppConfig(AutoWryModel):
    database: DatabaseConfig  # ❌ Won't auto-generate CLI

# Do this:
class AppConfig(AutoWryModel):
    db_host: str = Field(description="Database host")
    db_port: int = Field(description="Database port")

# Or use multi_model:
@multi_model(AppConfig, DatabaseConfig)
```

---

## Testing Strategy

### Test File Organization

```
tests/
├── features/          # End-to-end feature tests
│   ⭐ test_source_precedence.py  # THE KEY TEST FILE
│   test_auto_model.py
│   test_multi_model.py
│
├── integration/       # Component integration
│   test_click_integration.py
│   test_click_integration_extended.py
│   test_context_handling.py
│
└── unit/              # Unit tests by module
    ├── core/
    │   test_core.py  # WryModel basics
    │   test_sources.py  # ValueSource, TrackedValue
    │   test_advanced_features.py  # Constraints, env, accessors
    │   test_edge_cases.py
    │
    ├── click/  # 22 test files!
    │   test_parameter_generation.py
    │   test_constraint_formatting.py
    │   test_argument_types.py
    │   test_explicit_argument_help_injection.py
    │   test_format_constraint_text.py
    │   ... (18 more)
    │
    ├── model/
    │   test_model_click_context_handling.py
    │   test_model_environment_integration.py
    │   test_extract_subset_edge_cases.py
    │   test_model_edge_cases.py
    │
    ├── auto_model/
    │   test_auto_model_field_processing.py
    │   test_auto_model_edge_cases.py
    │
    └── multi_model/
        test_kwargs_splitting.py
```

### Coverage Requirements

- **Overall**: 90%+ (currently 92%)
- **Core modules**: Aim for 100%
- **New features**: 100% coverage expected

**Run coverage**:

```bash
pytest --cov=wry --cov-report=term-missing --cov-report=html
open htmlcov/index.html  # View detailed report
```

### What to Test When Contributing

1. **Source tracking**: All four sources, precedence
2. **Type conversion**: Every supported type (int, float, bool, str, list)
3. **Edge cases**: Optional, Union, custom types
4. **Error handling**: Invalid values, missing required, extra fields
5. **Integration**: Click context, decorators, multi-model
6. **Constraints**: All constraint types, help text generation
7. **Environment**: Variable names, type conversion, precedence

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/features/test_source_precedence.py -v

# Specific test
pytest tests/features/test_source_precedence.py::TestSourcePrecedence::test_complete_precedence_chain -xvs

# With coverage
pytest --cov=wry --cov-report=term-missing

# Fail on low coverage
pytest --cov=wry --cov-fail-under=90

# All checks (pre-commit)
./check.sh

# All Python versions
./scripts/test_all_versions.sh
```

---

## Common User Questions & Answers

**Q: Do I need to use AutoWryModel?**
A: No. Use `WryModel` with explicit `Annotated[type, AutoOption]` for more control. AutoWryModel is just convenience.

**Q: Can I use wry with existing Click commands?**
A: Yes! Just add `@Model.generate_click_parameters()` above your existing decorators.

**Q: Can I mix Pydantic validators with wry?**
A: Yes! All Pydantic features work normally. wry is a thin layer on top.

**Q: What if I have nested models?**
A: Flatten fields or use `multi_model()`. wry doesn't auto-generate CLI for nested models.

**Q: Can I use both --config and CLI args?**
A: Yes! CLI args override config file (precedence: CLI > ENV > JSON > DEFAULT).

**Q: How do I hide fields from the CLI?**
A: Use `Annotated[type, AutoExclude]` or `AutoClickParameter.EXCLUDE`.

**Q: Can I use custom Click types?**
A: Yes! Use explicit `click.option("--field", type=CustomType())` in Annotated.

**Q: Do I need to set up environment variables manually?**
A: No. wry auto-generates them based on field names and `env_prefix`.

**Q: How do I debug precedence issues?**
A: Use `config.get_sources_summary()` and run `examples/source_tracking_comprehensive.py`.

**Q: Can I load config from YAML/TOML?**
A: Not built-in. Load YAML/TOML yourself, convert to dict, use `Config(**data)`. JSON is built-in via `--config`.

**Q: Does wry work with Click groups?**
A: Yes, but apply decorators to commands, not groups.

---

## When to Use What

| Requirement | Solution | Example |
|-------------|----------|---------|
| Simple config, all options | `AutoWryModel` | All fields → `--options` |
| Need positional arguments | `AutoArgument` | `input: Annotated[str, AutoArgument]` |
| Mix arguments + options | `WryModel` with mixed annotations | See Template 2 |
| Hide fields from CLI | `AutoExclude` | `internal: Annotated[str, AutoExclude]` |
| Multiple logical configs | `multi_model()` | Server + DB + Cache configs |
| Track value sources | `@click.pass_context` + `from_click_context()` | See Template 2 |
| Custom Click types | Explicit decorator in Annotated | `click.option(type=CustomType())` |
| Load from config file | User provides `--config` | Built-in, automatic |
| Custom env var prefix | `env_prefix: ClassVar[str]` | `env_prefix: ClassVar[str] = "APP_"` |
| Force field required | `REQUIRED_OPTION` | Even with default |
| Complex validation | Pydantic validators | `@field_validator` |
| Runtime model creation | `create_auto_model()` | Plugin systems |
| List of values | `list[str]` type | Auto-gets `multiple=True` |

---

## Troubleshooting Flowchart

```
Problem: Configuration not working as expected
│
├─> Are values showing up?
│   ├─ NO → Check field names match (underscores vs hyphens)
│   │       CLI uses hyphens: --my-field
│   │       Model uses underscores: my_field
│   │
│   └─ YES → Continue
│
├─> Is source tracking accurate?
│   ├─ NO → Using @click.pass_context + from_click_context()?
│   │       Check: Not calling Config(**kwargs) directly
│   │
│   └─ YES → Continue
│
├─> Are environment variables working?
│   ├─ NO → env_prefix is ClassVar?
│   │       Run --show-env-vars to see expected names
│   │       Check: export MYAPP_FIELD=value
│   │
│   └─ YES → Continue
│
├─> Does CLI override config file?
│   ├─ NO → Version ≥ 0.2.2? (Bug fixed)
│   │       Test: pytest tests/features/test_source_precedence.py
│   │
│   └─ YES → Continue
│
├─> Are required fields enforced?
│   ├─ NO → Version ≥ 0.2.2? (Bug fixed)
│   │       Field has no default?
│   │       Not satisfied by env/config?
│   │
│   └─ YES → Continue
│
└─> Does --help show argument descriptions?
    ├─ NO → Version ≥ 0.2.3? (Feature added)
    │       Using Field(description="...")?
    │
    └─ YES → Working correctly!
```

---

## Performance Characteristics

### Startup Time

- Typical CLI startup overhead: <10ms
- Model field scanning: O(n) where n = number of fields
- Accessor creation: Lazy, only on first access
- Accessor caching: Subsequent accesses are O(1) dict lookup

### Memory Usage

- `_value_sources`: ~8 bytes per field (dict entry)
- `_accessor_instances`: Created on demand, ~40 bytes per accessor
- TrackedValue: Temporary during merging, not stored long-term

### When to Optimize

wry is designed for CLI tools where:

- Startup time matters more than runtime
- Configuration is read once at startup
- Memory footprint is negligible (<1KB for typical config)

**Don't optimize unless**: Hundreds of fields or performance-critical hot path.

---

## Design Principles

### 1. DRY (Don't Repeat Yourself)

Single source of truth: Pydantic model defines everything.

### 2. Explicit > Implicit

- Must opt-in to source tracking (`@click.pass_context`)
- AutoWryModel vs WryModel is explicit choice
- Explicit annotations override auto-generation

### 3. Type Safety

- Full Pydantic validation
- Click type conversion
- Type hints throughout (passes mypy strict)

### 4. Composability

- Mix AutoWryModel with explicit Click
- Combine multiple models
- Integrate with existing Click apps

### 5. Fail Early, Fail Clearly

- Validation errors at startup
- Clear error messages
- Strict mode detects mistakes

### 6. Zero Surprises

- Documented precedence (CLI > ENV > JSON > DEFAULT)
- Comprehensive test coverage
- Examples for every pattern

---

## Key Insights for LLMs

1. **Source tracking is wry's killer feature** - no other library does this comprehensively

2. **Precedence is strictly enforced** - CLI > ENV > JSON > DEFAULT (tested with 100% of combinations)

3. **v0.2.2 had critical fixes** - always check version when debugging

4. **Click doesn't support argument help** - wry solves by docstring injection

5. **eager_json_config is subtle** - must not modify param.default (v0.2.2 fix)

6. **env_prefix as ClassVar is non-obvious** - common mistake

7. **@click.pass_context is required** for accurate source tracking

8. **Examples are comprehensive** - point users there

9. **Test coverage is excellent** - trust the tests

10. **Help system is integrated** - `python -m wry.help_system ai`

---

## Summary

**wry** provides:

- ✅ Single source of truth (Pydantic models)
- ✅ Automatic CLI generation (Click integration)
- ✅ Multi-source configuration (CLI/ENV/JSON/DEFAULT)
- ✅ Source tracking (know where every value came from)
- ✅ Type safety (Pydantic + Click)
- ✅ Comprehensive testing (407 tests, 92% coverage)
- ✅ Excellent documentation (README + AI KB + examples)

**For AI assistants**:

- Start with `examples/source_tracking_comprehensive.py` to understand the system
- Reference this knowledge base for details
- Check version for bug fixes (v0.2.2 critical)
- Point users to examples for patterns
- Use `show_help_index()` to help users find documentation

---

**End of Knowledge Base** - Version 0.2.3+ - Last Updated: 2025-10-01

**Access this**: `python -m wry.help_system ai` or `from wry import print_help; print_help('ai')`
