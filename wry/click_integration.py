"""Click-specific utilities for wry CLI integration.

This module contains Click-specific functionality for auto-generating
CLI parameters from Pydantic models and handling configuration files.

Key functions:
- generate_click_parameters: Auto-generate Click options/arguments from Pydantic
- eager_json_config: Callback for JSON config file loading
- build_config_with_sources: Main helper for building config with proper precedence
"""

import inspect
import types
from collections.abc import Callable, Mapping, Sequence
from enum import Enum, auto
from typing import Any, TypeAlias, cast, get_args, get_origin, get_type_hints

import click
from annotated_types import (
    Ge,
    GroupedMetadata,
    Gt,
    Interval,
    Le,
    Len,
    Lt,
    MaxLen,
    MinLen,
    MultipleOf,
    Predicate,
    Timezone,
)
from click.decorators import FC
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from .core import extract_field_constraints


class AutoClickParameter(Enum):
    """Markers for automatic Click parameter generation."""

    OPTION = auto()
    REQUIRED_OPTION = auto()
    ARGUMENT = auto()
    EXCLUDE = auto()


ClickParameterDecorator: TypeAlias = Callable[[FC], FC]


def format_constraint_text(constraints: dict[str, Any]) -> list[str]:
    """Format constraints dictionary into human-readable text.

    Args:
        constraints: Dictionary of constraint names to values

    Returns:
        List of formatted constraint strings
    """
    texts: list[str] = []

    # Numeric bounds
    if "ge" in constraints:
        texts.append(f">= {constraints['ge']}")
    if "gt" in constraints:
        texts.append(f"> {constraints['gt']}")
    if "le" in constraints:
        texts.append(f"<= {constraints['le']}")
    if "lt" in constraints:
        texts.append(f"< {constraints['lt']}")

    # Length constraints
    if "min_length" in constraints and "max_length" in constraints:
        if constraints["min_length"] == constraints["max_length"]:
            texts.append(f"length = {constraints['min_length']}")
        else:
            texts.append(f"length {constraints['min_length']}-{constraints['max_length']}")
    elif "min_length" in constraints:
        texts.append(f"min length {constraints['min_length']}")
    elif "max_length" in constraints:
        texts.append(f"max length {constraints['max_length']}")

    # Multiple of
    if "multiple_of" in constraints:
        texts.append(f"multiple of {constraints['multiple_of']}")

    return texts


def extract_constraint_text(constraint: Any) -> str | None:
    """Extract human-readable constraint text from annotated-types constraints.

    Args:
        constraint: An annotated-types constraint object

    Returns:
        Human-readable description of the constraint, or None if not recognized
    """
    # Handle GroupedMetadata by recursively unpacking
    if isinstance(constraint, GroupedMetadata):
        sub_constraints: list[str] = []
        for item in constraint:
            sub_text = extract_constraint_text(item)
            if sub_text:
                sub_constraints.append(sub_text)
        return " AND ".join(sub_constraints) if sub_constraints else None

    # Numeric bounds
    if isinstance(constraint, Ge):
        return f">= {constraint.ge}"
    elif isinstance(constraint, Gt):
        return f"> {constraint.gt}"
    elif isinstance(constraint, Le):
        return f"<= {constraint.le}"
    elif isinstance(constraint, Lt):
        return f"< {constraint.lt}"

    # Interval (combination of bounds)
    elif isinstance(constraint, Interval):
        parts: list[Any] = []
        if constraint.gt is not None:
            parts.append(f"> {constraint.gt}")
        if constraint.ge is not None:
            parts.append(f">= {constraint.ge}")
        if constraint.lt is not None:
            parts.append(f"< {constraint.lt}")
        if constraint.le is not None:
            parts.append(f"<= {constraint.le}")
        return " AND ".join(parts) if parts else None

    # Multiple of
    elif isinstance(constraint, MultipleOf):
        return f"multiple of {constraint.multiple_of}"

    # Length constraints
    elif isinstance(constraint, Len):
        min_len = getattr(constraint, "min_length", None)
        max_len = getattr(constraint, "max_length", None)
        if min_len is not None and max_len is not None:
            if min_len == max_len:
                return f"length = {min_len}"
            return f"length {min_len}-{max_len}"
        elif min_len is not None:
            return f"length >= {min_len}"
        elif max_len is not None:
            return f"length <= {max_len}"
    elif isinstance(constraint, MinLen):
        return f"min length {constraint.min_length}"
    elif isinstance(constraint, MaxLen):
        return f"max length {constraint.max_length}"

    # Timezone constraint
    elif isinstance(constraint, Timezone):
        if constraint.tz is None:
            return "naive datetime (no timezone)"
        elif constraint.tz == ...:
            return "any timezone-aware datetime"
        else:
            return f"timezone: {constraint.tz}"

    # String predicates
    elif isinstance(constraint, Predicate):
        return _extract_predicate_description(constraint.func)

    # Handle slice objects (used for length)
    elif isinstance(constraint, slice):
        # Slice.start/stop are Union[int, None]
        constraint_slice = constraint
        start_raw = constraint_slice.start
        stop_raw = constraint_slice.stop
        start_val: int = int(start_raw) if start_raw is not None and isinstance(start_raw, int | float) else 0
        stop_val: int | None = int(stop_raw) if stop_raw is not None and isinstance(stop_raw, int | float) else None

        if stop_val is not None:
            if start_val == stop_val - 1:
                return f"length = {start_val}"
            return f"length {start_val}-{stop_val - 1}"
        else:
            return f"min length {start_val}"

    return None


def _extract_predicate_description(func: Callable[[Any], bool]) -> str:
    """Extract a meaningful description from a predicate function."""
    # Check for known built-in predicates
    if func == str.islower:
        return "lowercase"
    elif func == str.isupper:
        return "uppercase"
    elif func == str.isdigit:
        return "digits only"
    elif func == str.isascii:
        return "ASCII only"
    elif func == str.isalnum:
        return "alphanumeric only"
    elif func == str.isalpha:
        return "alphabetic only"

    # Handle named functions
    if hasattr(func, "__name__") and func.__name__ != "<lambda>":
        return f"predicate: {func.__name__}"

    # Try to extract lambda source code for better descriptions
    try:
        source = inspect.getsource(func).strip()

        # Clean up the source - remove extra whitespace and lambda keyword
        if "lambda" in source:
            # Extract just the lambda expression part
            lambda_part = source.split("lambda", 1)[1]
            if ":" in lambda_part:
                lambda_expr = lambda_part.split(":", 1)[1].strip()

                # Common patterns we can make more readable
                patterns = {
                    "x.startswith(": "starts with",
                    "x.endswith(": "ends with",
                    "len(x) >=": "length >=",
                    "len(x) <=": "length <=",
                    "len(x) >": "length >",
                    "len(x) <": "length <",
                    "len(x) ==": "length =",
                    "x.count(": "contains",
                    "x in [": "must be one of",
                    "x not in [": "must not be one of",
                    "x >": "greater than",
                    "x <": "less than",
                    "x >=": "greater than or equal to",
                    "x <=": "less than or equal to",
                    "x ==": "equals",
                    "x !=": "not equals",
                }

                # Try to match common patterns
                for pattern, description in patterns.items():
                    if pattern in lambda_expr:
                        # Extract the value part
                        if pattern.endswith("("):
                            # For function calls like startswith(
                            try:
                                value_part = lambda_expr.split(pattern)[1].split(")")[0]
                                return f"{description} {value_part}"
                            except (IndexError, ValueError):
                                pass
                        elif pattern.endswith("["):
                            # For list membership like 'x in ['
                            try:
                                value_part = lambda_expr.split(pattern)[1]
                                # Find the closing bracket
                                bracket_end = value_part.find("]")
                                if bracket_end != -1:
                                    list_content = value_part[:bracket_end]
                                    return f"{description} [{list_content}]"
                            except (IndexError, ValueError):
                                pass
                        else:
                            # For operators
                            try:
                                value_part = lambda_expr.split(pattern)[1].strip()
                                # Remove trailing parentheses or other syntax
                                value_part = value_part.split(")")[0].split(",")[0].strip()
                                return f"{description} {value_part}"
                            except (IndexError, ValueError):
                                pass

                # Special case for string containment patterns
                if " in x" in lambda_expr:
                    # Extract what's being checked for containment
                    parts = lambda_expr.split(" in x")
                    if len(parts) >= 2:
                        check_value = parts[0].strip()
                        # Remove quotes if present
                        if (check_value.startswith('"') and check_value.endswith('"')) or (
                            check_value.startswith("'") and check_value.endswith("'")
                        ):
                            check_value = check_value[1:-1]
                        return f"contains '{check_value}'"

                # If no pattern matched, return the cleaned lambda expression
                if len(lambda_expr) < 50:  # Only if it's reasonably short
                    return f"must satisfy: {lambda_expr}"

    except (OSError, TypeError):
        # Can't get source (e.g., built-in functions, dynamically created)
        pass

    # Fallback to generic description
    return "custom predicate"


def config_option() -> Callable[[FC], FC]:
    """Add --config option for JSON configuration file.

    This decorator adds a --config/-c option that loads configuration
    from a JSON file. It uses an eager callback to process the file
    before other options are parsed.

    Returns:
        Decorator that adds the config option
    """
    return click.option(
        "--config",
        "-c",
        type=click.Path(exists=True, dir_okay=False, file_okay=True),
        callback=eager_json_config,
        is_eager=True,
        expose_value=False,
        help="JSON configuration file",
    )


def generate_click_parameters(
    model_class: type[BaseModel],
    add_config_option: bool = True,
    strict: bool = True,
) -> Callable[[FC], FC]:
    """Generate Click options and arguments with smart auto-generation.

    This decorator automatically generates Click CLI parameters from a Pydantic
    model's fields. It supports three modes:
    1. AUTO_CLICK_OPTION: Auto-generates a Click option from Field metadata
    2. AUTO_CLICK_ARGUMENT: Auto-generates a Click argument from Field metadata
    3. Explicit Click decorator: Uses the provided Click decorator as-is

    Args:
        model_class: Pydantic BaseModel class with Annotated fields
        add_config_option: Whether to add the --config/-c option that allows loading
            configuration from a JSON file.
        strict: If True (default), raise error when decorator is applied multiple times.
            If False, allow multiple applications with a warning.

    Returns:
        Decorator function that applies all Click parameters
    """
    arguments: list[ClickParameterDecorator[Any]] = []  # Arguments must come first
    options: list[ClickParameterDecorator[Any]] = []  # Options come after arguments
    argument_docs: list[tuple[str, str]] = []  # Track (arg_name, description) for docstring injection
    type_hints = get_type_hints(model_class, include_extras=True)

    for field_name, field_info in model_class.model_fields.items():
        annotation = type_hints.get(field_name)

        # Skip fields without annotations
        origin = get_origin(annotation)
        # Compare using string representation to handle module reload scenarios
        if origin is None or str(origin) != "<class 'typing.Annotated'>":
            continue

        # Get metadata from annotation
        metadata = get_args(annotation)[1:]

        # Check what kind of Click integration we need
        click_parameter: ClickParameterDecorator[Any] | None = None
        field_type: AutoClickParameter | None = None
        for item in metadata:
            if item == AutoClickParameter.OPTION:
                field_type = AutoClickParameter.OPTION
            elif item == AutoClickParameter.REQUIRED_OPTION:
                field_type = AutoClickParameter.REQUIRED_OPTION
            elif item == AutoClickParameter.ARGUMENT:
                field_type = AutoClickParameter.ARGUMENT
            elif item == AutoClickParameter.EXCLUDE:
                field_type = AutoClickParameter.EXCLUDE
                break  # Skip this field entirely
            elif (
                hasattr(item, "__module__")
                and "click" in str(item.__module__)
                and not isinstance(item, AutoClickParameter)
            ):
                click_parameter = item
                break

        # Skip excluded fields
        if field_type == AutoClickParameter.EXCLUDE:
            continue

        if field_type == AutoClickParameter.OPTION or field_type == AutoClickParameter.REQUIRED_OPTION:
            # Auto-generate Click option from Field info
            option_name = f"--{field_name.replace('_', '-')}"

            # Check if field is required first (needed to decide on default handling)
            is_required = field_info.is_required() or field_type == AutoClickParameter.REQUIRED_OPTION

            click_kwargs: dict[str, Any] = {
                "help": field_info.description or f"{field_name.replace('_', ' ').title()}",
                "show_default": True,
            }

            # Only set default if field has one, or if field is not required
            # For required fields without a default, we must NOT set default=None
            # or Click will think there IS a default and won't enforce the requirement
            if field_info.default is not PydanticUndefined:
                click_kwargs["default"] = field_info.default
            elif not is_required:
                # Optional field without explicit default gets None
                click_kwargs["default"] = None

            # Determine Click type from annotation
            base_type = get_args(annotation)[0]

            # Check if this is a list type that should support multiple=True
            is_list_type = False
            if hasattr(base_type, "__origin__"):
                # Handle typing.List, typing.Tuple, etc.
                if base_type.__origin__ is list or base_type.__origin__ is tuple:
                    is_list_type = True
            elif hasattr(base_type, "__args__") and base_type.__args__:
                # Handle newer Python versions with | syntax
                if get_origin(base_type) is list or get_origin(base_type) is tuple:
                    is_list_type = True

            # Add multiple=True for list types
            if is_list_type:
                click_kwargs["multiple"] = True

            # Handle Optional types - extract the actual type
            from typing import Union

            # Check for both typing.Union and types.UnionType (Python 3.10+ | syntax)
            if get_origin(base_type) is Union or (
                hasattr(types, "UnionType") and isinstance(base_type, types.UnionType)
            ):
                # Get the non-None type from Optional[X]
                args = get_args(base_type)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    base_type = non_none_types[0]

            if base_type is bool:
                click_kwargs["is_flag"] = True
                click_kwargs.pop("show_default")  # Flags don't show defaults
            elif base_type is int:
                click_kwargs["type"] = click.INT
            elif base_type is float:
                click_kwargs["type"] = click.FLOAT
            elif base_type is str:
                click_kwargs["type"] = click.STRING
            # Skip setting type for complex types - let Click use default

            # Add validation info to help text (but don't pass to Click)
            # Extract all constraints in one pass
            constraints = extract_field_constraints(field_info)
            # Remove 'default' from constraints as it's not a validation constraint
            constraints.pop("default", None)

            # Format constraints for display
            constraints_text = format_constraint_text(constraints)

            if constraints_text:
                click_kwargs["help"] += f" (Constraints: {', '.join(constraints_text)})"

            # Check if environment variable is set for this field
            # We need to check this to decide if Click should enforce required
            import os

            # Get the environment variable prefix
            env_prefix = getattr(model_class, "env_prefix", "DRYCLI_")
            env_var_name = f"{env_prefix}{field_name.upper()}"

            env_var_set = env_var_name in os.environ

            # Only mark as required in Click if:
            # 1. Field is required in Pydantic AND
            # 2. No environment variable is set
            click_required = is_required and not env_var_set

            # Add envvar support
            option = click.option(
                option_name,
                **click_kwargs,
                required=click_required,
                envvar=env_var_name,  # Tell Click about the environment variable
            )
            options.append(option)

        elif field_type == AutoClickParameter.ARGUMENT:
            # Auto-generate Click argument from Field info
            argument_name = field_name.lower()

            # Arguments don't have defaults in Click - they're positional
            click_kwargs = {}

            # Determine Click type from annotation
            base_type = get_args(annotation)[0]

            # Handle Optional types - extract the actual type
            from typing import Union

            # Check for both typing.Union and types.UnionType (Python 3.10+ | syntax)
            if get_origin(base_type) is Union or (
                hasattr(types, "UnionType") and isinstance(base_type, types.UnionType)
            ):
                # Get the non-None type from Optional[X]
                args = get_args(base_type)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    base_type = non_none_types[0]

            # Set appropriate Click type
            if base_type is int:
                click_kwargs["type"] = click.INT
            elif base_type is float:
                click_kwargs["type"] = click.FLOAT
            elif base_type is bool:
                click_kwargs["type"] = click.BOOL
            elif base_type is not str:  # Only specify type if not string (Click default)
                click_kwargs["type"] = base_type

            # Note: required=False to allow --config to replace arg
            arguments.append(click.argument(argument_name, **click_kwargs, required=False))

            # Track argument description for docstring injection
            if field_info.description:
                argument_docs.append((argument_name.upper(), field_info.description))

        elif click_parameter:
            # Determine if it's an argument or option
            if hasattr(click_parameter, "__name__") and "argument" in str(click_parameter):
                modified_arg, arg_info = extract_and_modify_argument_decorator(click_parameter)
                arguments.append(modified_arg)

                # Track argument description for docstring injection
                # Try to get help from decorator first, then from Field description
                help_text = arg_info.get("help") or field_info.description
                if help_text:
                    # Use the argument name from param_decls, uppercase it for display
                    arg_name = arg_info.get("param_decls", [field_name])[0].upper()
                    argument_docs.append((arg_name, help_text))
            else:
                # Only append if it's actually a Click decorator, not an AutoClickParameter
                if callable(click_parameter) and not isinstance(click_parameter, AutoClickParameter):
                    options.append(click_parameter)

    # We'll conditionally add these in the decorator to avoid duplicates
    config_and_env_options: list[ClickParameterDecorator[Any]] = []

    if add_config_option:
        config_and_env_options.append(config_option())

    # Add --show-env-vars option for discoverability (always)
    def _show_env_vars(ctx: click.Context, param: click.Parameter, value: bool) -> None:
        """Show supported environment variables and exit."""
        if value:
            model_class.print_env_vars()  # type: ignore
            ctx.exit(0)

    config_and_env_options.append(
        click.option(
            "--show-env-vars",
            is_flag=True,
            help="Show supported environment variables and exit",
            is_eager=True,
            callback=_show_env_vars,
            expose_value=False,
        )
    )

    def decorator(func: FC) -> FC:
        # Check for duplicate decorator application
        if hasattr(func, "_wry_models"):
            existing_models = getattr(func, "_wry_models", [])
            model_names = [m.__name__ for m in existing_models]

            if strict:
                raise ValueError(
                    f"Function '{func.__name__}' already decorated with "
                    f"generate_click_parameters for models: {model_names}. "
                    f"Use strict=False to allow multiple decorators."
                )
            else:
                import warnings

                warnings.warn(
                    f"Function '{func.__name__}' already decorated with "
                    f"generate_click_parameters for models: {model_names}. "
                    f"Adding {model_class.__name__}. This may cause duplicate options.",
                    UserWarning,
                    stacklevel=2,
                )

        # Track which models have been applied
        if not hasattr(func, "_wry_models"):
            func._wry_models = []  # type: ignore
        func._wry_models.append(model_class)  # type: ignore

        # Check if we should skip duplicate --config and --show-env-vars options
        if hasattr(func, "_has_config_option"):
            # Skip adding config and env vars options as they already exist
            final_options = options
        else:
            # Add config options only once
            final_options = options + config_and_env_options
            if config_and_env_options:
                func._has_config_option = True  # type: ignore

        # Inject argument descriptions into docstring BEFORE applying decorators
        if argument_docs:
            original_doc = func.__doc__ or ""
            # Build argument documentation section
            # Use \b to prevent Click from rewrapping, and format like Options section
            arg_doc_lines = ["\n\n\b"]
            arg_doc_lines.append("\n\b\bArguments:")
            for arg_name, description in argument_docs:
                # Match Click's Options formatting: 2 space indent, left-aligned
                arg_doc_lines.append(f"\n\b\b  {arg_name.ljust(18)} {description}")
            arg_doc_section = "".join(arg_doc_lines)

            # Append to existing docstring
            func.__doc__ = original_doc.rstrip() + arg_doc_section

        # Apply arguments first, then options (Click requirement)
        all_decorators = arguments + final_options
        for dec in reversed(all_decorators):
            func = dec(func)

        return func

    return decorator


def extract_and_modify_argument_decorator(
    click_decorator: ClickParameterDecorator[Any],
) -> tuple[ClickParameterDecorator[Any], dict[str, Any]]:
    """Extract and modify a click.argument decorator to set required=False.

    Returns:
        Tuple of (modified_decorator, info_dict) where info_dict contains:
            - param_decls: list of parameter declaration strings
            - help: help text if available
            - other attributes from the original decorator
    """
    # Default values - use a safe fallback
    param_decls: list[str] = ["argument"]
    attrs: dict[str, Any] = {"required": False}

    # Try to extract from closure, but don't rely on it
    try:
        if hasattr(click_decorator, "__closure__") and click_decorator.__closure__:
            for cell in click_decorator.__closure__:
                contents = cell.cell_contents

                # Handle string sequences (parameter names)
                if isinstance(contents, tuple | list):
                    seq: Sequence[Any] = cast(Sequence[Any], contents)
                    string_items: list[str] = []
                    for item in seq:
                        if isinstance(item, str):
                            string_items.append(item)
                    if string_items:
                        param_decls = string_items

                # Handle attribute dictionaries
                elif isinstance(contents, dict):
                    # Only update with string keys to be safe
                    dict_contents: Mapping[Any, Any] = cast(Mapping[Any, Any], contents)
                    for k, v in dict_contents.items():
                        if isinstance(k, str):
                            attrs[k] = v
                    attrs["required"] = False  # Always override to make optional

                # Handle Click parameter classes
                elif isinstance(contents, type):
                    try:
                        if issubclass(contents, click.Argument):
                            attrs["cls"] = contents
                    except (TypeError, AttributeError):
                        pass
    except Exception:
        # If closure inspection fails, just use defaults
        pass

    # Create info dict with extracted information (including help if present)
    info = {"param_decls": param_decls, **attrs}

    # Remove 'help' from attrs before creating Click argument
    # (click.Argument doesn't accept 'help' parameter)
    argument_attrs = {k: v for k, v in attrs.items() if k != "help"}

    # Create new argument with modified attrs
    return click.argument(*param_decls, **argument_attrs), info


def build_config_with_sources(
    ctx: click.Context | type[BaseModel] | None = None,
    config_class: type[BaseModel] | None = None,
    **kwargs: Any,
) -> Any:
    """Build a configuration instance with proper source tracking.

    This is a convenience wrapper that delegates to the config class's
    from_click_context method if available, providing backward compatibility.

    Args:
        ctx: Click context. If None, will try to get current context.
        config_class: The Pydantic model class to instantiate
        **kwargs: All CLI arguments passed to the command

    Returns:
        Instance of config_class with proper source tracking

    Example:
        ```python
        @click.command()
        @generate_click_parameters(MyConfig)
        def my_command(**kwargs: Any) -> None:
            # Context retrieved automatically
            config = build_config_with_sources(config_class=MyConfig, **kwargs)

            # Or with explicit context (backward compatible)
            ctx = click.get_current_context()
            config = build_config_with_sources(ctx, MyConfig, **kwargs)
        ```
    """
    # Handle positional arguments for backward compatibility
    actual_config_class: type[BaseModel]
    actual_ctx: click.Context | None

    if config_class is not None:
        # Normal case: config_class provided
        actual_config_class = config_class
        actual_ctx = ctx if isinstance(ctx, click.Context | type(None)) else None
    elif ctx is not None and not isinstance(ctx, click.Context):
        # Called as build_config_with_sources(MyConfig, **kwargs)
        # ctx is actually the config class in this case
        # actual_config_class = cast(type[BaseModel], ctx)
        actual_config_class = ctx
        actual_ctx = None
    else:
        # No valid config class provided
        raise ValueError("config_class must be provided")

    # Check if the config class has the new method
    if hasattr(actual_config_class, "from_click_context"):
        # Use getattr to satisfy type checker
        from_click_context = actual_config_class.from_click_context
        return from_click_context(actual_ctx, **kwargs)
    else:
        # Fallback for regular Pydantic models without WryModel
        # Just create with the kwargs, no source tracking
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return actual_config_class(**clean_kwargs)


def eager_json_config(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    """Eager callback that pre-populates required parameters from JSON.

    This callback is designed to be used with Click's is_eager=True flag,
    allowing it to process before other parameters. It loads a JSON config
    file and pre-fills any missing required parameters, preventing Click
    from throwing MissingParameter errors.

    Args:
        ctx: Click context
        param: Click parameter (the config file option)
        value: Path to JSON config file

    Returns:
        The original value (config file path)

    Raises:
        click.BadParameter: If the config file cannot be loaded
    """
    import json

    if not value or ctx.resilient_parsing:
        return value

    try:
        with open(value) as f:
            json_data = json.load(f)

        # Store JSON data for later merging in from_click_context
        ctx.ensure_object(dict)["json_data"] = json_data

        # Mark parameters from JSON as not required
        # This allows JSON to satisfy required arguments without modifying defaults
        if hasattr(ctx, "command") and ctx.command:
            for p in ctx.command.params:
                if (isinstance(p, click.Argument) or isinstance(p, click.Option)) and p.name in json_data:
                    p.required = False

        return value

    except Exception as e:
        raise click.BadParameter(f"Config file error: {e}") from e
