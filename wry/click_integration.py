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
from typing import Any, TypeAlias, Union, cast, get_args, get_origin, get_type_hints

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


class WryOption:
    """Marker for auto-generated Click options with customization."""

    def __init__(
        self,
        *,
        required: bool = False,
        flag_enable_on_off: bool = True,
        flag_off_prefix: str | None = None,
        flag_off_option: str | None = None,
        comma_separated: bool = False,
    ):
        """Initialize WryOption marker.

        Args:
            required: If True, option is required even if it has a default
            flag_enable_on_off: For bool fields - True=use --option/--no-option pattern,
                False=single --option flag
            flag_off_prefix: For bool fields - Prefix for off-option
                (e.g., "disable" → --option/--disable-option)
            flag_off_option: For bool fields - Full off-option name
                (e.g., "quiet" → --verbose/--quiet)
            comma_separated: For list fields - True=comma-separated input (--tags a,b,c),
                False=multiple option (--tags a --tags b)

        Raises:
            ValueError: If both flag_off_prefix and flag_off_option are provided,
                or if they're provided when flag_enable_on_off=False
        """
        if flag_off_prefix and flag_off_option:
            raise ValueError("Provide only one of flag_off_prefix or flag_off_option, not both")
        if (flag_off_prefix or flag_off_option) and not flag_enable_on_off:
            raise ValueError("Cannot specify flag_off_prefix/flag_off_option when flag_enable_on_off=False")

        self.required = required
        self.flag_enable_on_off = flag_enable_on_off
        self.flag_off_prefix = flag_off_prefix
        self.flag_off_option = flag_off_option
        self.comma_separated = comma_separated


class WryArgument:
    """Marker for auto-generated Click arguments."""

    def __init__(self) -> None:
        """Initialize WryArgument marker."""
        pass


class WryExclude:
    """Marker to exclude field from CLI generation."""

    def __init__(self) -> None:
        """Initialize WryExclude marker."""
        pass


# DEPRECATED v0.6.0: Old enum-based API
# TODO: Remove in v1.0.0
class AutoClickParameter(Enum):
    """Deprecated: Use AutoOption(), AutoArgument(), AutoExclude() instead.

    This enum is deprecated and will be removed in the next major version.
    Use the new callable API instead:
    - AutoClickParameter.OPTION → AutoOption()
    - AutoClickParameter.REQUIRED_OPTION → AutoOption(required=True)
    - AutoClickParameter.ARGUMENT → AutoArgument()
    - AutoClickParameter.EXCLUDE → AutoExclude()

    Note: Deprecation warnings are emitted when enum values are used in annotations.
    """

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

        # Handle Optional/Union wrapping Annotated types
        # e.g., Annotated[list[str], CommaSeparated] | None
        origin = get_origin(annotation)
        if origin is not None and (
            origin is Union or (hasattr(types, "UnionType") and isinstance(annotation, types.UnionType))
        ):
            # Unwrap Optional/Union to get the inner type
            args = get_args(annotation)
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                annotation = non_none_types[0]
                origin = get_origin(annotation)

        # Skip fields without annotations
        # Compare using string representation to handle module reload scenarios
        if origin is None or str(origin) != "<class 'typing.Annotated'>":
            continue

        # Get metadata from annotation
        metadata = get_args(annotation)[1:]

        # Also check for metadata inside Optional/Union types
        # e.g., Annotated[Optional[Annotated[list[str], CommaSeparated]], AutoOption]
        base_type_for_metadata = get_args(annotation)[0]
        if get_origin(base_type_for_metadata) is Union or (
            hasattr(types, "UnionType") and isinstance(base_type_for_metadata, types.UnionType)
        ):
            # Unwrap Optional to check for inner Annotated
            inner_args = get_args(base_type_for_metadata)
            inner_non_none = [arg for arg in inner_args if arg is not type(None)]
            if inner_non_none and get_origin(inner_non_none[0]) is not None:
                inner_origin = get_origin(inner_non_none[0])
                if str(inner_origin) == "<class 'typing.Annotated'>":
                    # Extract metadata from inner Annotated
                    inner_metadata = get_args(inner_non_none[0])[1:]
                    # Combine with outer metadata
                    metadata = tuple(metadata) + tuple(inner_metadata)

        # Check what kind of Click integration we need
        click_parameter: ClickParameterDecorator[Any] | None = None
        wry_marker: WryOption | WryArgument | WryExclude | None = None
        use_comma_separated: bool = False

        for item in metadata:
            # NEW: Check for Wry marker instances (check first - has comma_separated param)
            if isinstance(item, WryOption | WryArgument | WryExclude):
                wry_marker = item
                # Check for comma_separated in WryOption
                if isinstance(item, WryOption) and item.comma_separated:
                    use_comma_separated = True
                # Don't break yet - might have other markers
            # DEPRECATED v0.6.0: Check for CommaSeparated marker (standalone)
            # TODO: Remove in v1.0.0
            elif item.__class__.__name__ == "CommaSeparated" or (
                hasattr(item, "__class__")
                and item.__class__.__name__ == "type"
                and hasattr(item, "__name__")
                and item.__name__ == "CommaSeparated"
            ):
                import warnings

                warnings.warn(
                    "Using standalone CommaSeparated marker is deprecated. "
                    "Use AutoOption(comma_separated=True) instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                use_comma_separated = True
                # Don't break - continue checking for other markers
            # DEPRECATED v0.6.0: Check for Wry marker classes without calling them
            # TODO: Remove in v1.0.0 - require users to call the class
            elif item in (WryOption, WryArgument, WryExclude):
                # Instantiate the class
                if item is WryOption:
                    wry_marker = WryOption()
                elif item is WryArgument:
                    wry_marker = WryArgument()
                elif item is WryExclude:
                    wry_marker = WryExclude()
                # Don't break yet - might have CommaSeparated too
            # DEPRECATED v0.6.0: Check for deprecated enum values (backwards compat)
            # TODO: Remove in v1.0.0
            elif item in (
                AutoClickParameter.OPTION,
                AutoClickParameter.REQUIRED_OPTION,
                AutoClickParameter.ARGUMENT,
                AutoClickParameter.EXCLUDE,
            ):
                import warnings

                warnings.warn(
                    f"Using AutoClickParameter.{item.name} is deprecated. "
                    f"Use Auto{item.name.title().replace('_', '')}() instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                # Convert old enum to new marker
                if item == AutoClickParameter.OPTION:
                    wry_marker = WryOption()
                elif item == AutoClickParameter.REQUIRED_OPTION:
                    wry_marker = WryOption(required=True)
                elif item == AutoClickParameter.ARGUMENT:
                    wry_marker = WryArgument()
                elif item == AutoClickParameter.EXCLUDE:
                    wry_marker = WryExclude()
                # Don't break yet - might have CommaSeparated too
            # Check for explicit click decorator
            elif hasattr(item, "__module__") and "click" in str(item.__module__):
                click_parameter = item
                break  # Break here - explicit decorators take full control

        # Skip excluded fields
        if isinstance(wry_marker, WryExclude):
            continue

        # Handle options (but not if there's an explicit click decorator)
        if (isinstance(wry_marker, WryOption) or wry_marker is None) and click_parameter is None:
            # Auto-generate Click option from Field info
            # Use alias if available, otherwise use field name
            name_for_option = field_info.alias if field_info.alias else field_name
            option_name = f"--{name_for_option.replace('_', '-')}"

            # Determine if required
            is_required = field_info.is_required()
            if isinstance(wry_marker, WryOption) and wry_marker.required:
                is_required = True

            click_kwargs: dict[str, Any] = {
                "help": field_info.description or f"{field_name.replace('_', ' ').title()}",
                "show_default": True,
            }

            # Only set default if field has one, or if field is not required
            # For required fields without a default, we must NOT set default=None
            # or Click will think there IS a default and won't enforce the requirement
            if field_info.default is not PydanticUndefined:
                click_kwargs["default"] = field_info.default
            elif field_info.default_factory is not None:
                # Field has default_factory (e.g., default_factory=list)
                # Call it to get the default value for Click
                factory = cast(Callable[[], Any], field_info.default_factory)
                click_kwargs["default"] = factory()
            elif not is_required:
                # Optional field without explicit default gets None
                click_kwargs["default"] = None

            # Determine Click type from annotation
            base_type = get_args(annotation)[0]

            # Handle Optional types FIRST - extract the actual type
            # Check for both typing.Union and types.UnionType (Python 3.10+ | syntax)
            if get_origin(base_type) is Union or (
                hasattr(types, "UnionType") and isinstance(base_type, types.UnionType)
            ):
                # Get the non-None type from Optional[X] or Union[X, None]
                args = get_args(base_type)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    base_type = non_none_types[0]

            # If after unwrapping Optional, we have an Annotated type, unwrap that too
            # e.g., Optional[Annotated[list[str], CommaSeparated]] -> list[str]
            if get_origin(base_type) is not None and str(get_origin(base_type)) == "<class 'typing.Annotated'>":
                base_type = get_args(base_type)[0]

            # Check if this is a list type that should support multiple=True
            # (Now base_type has been unwrapped from Optional and Annotated if needed)
            is_list_type = False
            list_element_type = None
            if hasattr(base_type, "__origin__"):
                # Handle typing.List, typing.Tuple, etc.
                if base_type.__origin__ is list or base_type.__origin__ is tuple:
                    is_list_type = True
                    # Get the element type for comma-separated handling
                    if hasattr(base_type, "__args__") and base_type.__args__:
                        list_element_type = base_type.__args__[0]
            elif hasattr(base_type, "__args__") and base_type.__args__:
                # Handle newer Python versions with | syntax
                if get_origin(base_type) is list or get_origin(base_type) is tuple:
                    is_list_type = True
                    list_element_type = get_args(base_type)[0]

            # Handle list types - either multiple=True or comma-separated
            if is_list_type:
                # Check if comma-separated is enabled:
                # 1. Per-field via AutoOption(comma_separated=True) (NEW v0.6.0)
                # 2. Per-field via CommaSeparated annotation (DEPRECATED - backwards compat)
                # 3. Model-wide via wry_comma_separated_lists class variable
                per_field_comma_sep = isinstance(wry_marker, WryOption) and wry_marker.comma_separated
                use_comma_sep = (
                    per_field_comma_sep
                    or use_comma_separated
                    or getattr(model_class, "wry_comma_separated_lists", False)
                )

                if use_comma_sep:
                    # Use comma-separated input instead of multiple=True
                    from .comma_separated import (
                        CommaSeparatedFloats,
                        CommaSeparatedInts,
                        CommaSeparatedStrings,
                    )

                    # Select appropriate comma-separated type based on element type
                    if list_element_type is int:
                        click_kwargs["type"] = CommaSeparatedInts()
                    elif list_element_type is float:
                        click_kwargs["type"] = CommaSeparatedFloats()
                    else:  # Default to strings (includes str and other types)
                        click_kwargs["type"] = CommaSeparatedStrings()
                    # Don't set multiple=True for comma-separated
                else:
                    # Standard behavior: multiple=True
                    click_kwargs["multiple"] = True

            # NEW: Boolean handling with on/off support
            if base_type is bool:
                # Determine on/off behavior (default=True for all bools)
                use_on_off = True

                if isinstance(wry_marker, WryOption) and not wry_marker.flag_enable_on_off:
                    use_on_off = False

                if not use_on_off:
                    # Single flag (explicit opt-out)
                    click_kwargs["is_flag"] = True
                    click_kwargs.pop("show_default")
                else:
                    # On/off pattern (new default)
                    off_option_name = None

                    # Check for per-field customization
                    if isinstance(wry_marker, WryOption):
                        if wry_marker.flag_off_option:
                            off_option_name = f"--{wry_marker.flag_off_option}"
                        elif wry_marker.flag_off_prefix:
                            off_option_name = f"--{wry_marker.flag_off_prefix}-{name_for_option.replace('_', '-')}"

                    if not off_option_name:
                        # Use model-wide prefix (wry_boolean_off_prefix)
                        from .core.model import _DEFAULT_BOOLEAN_OFF_PREFIX

                        off_prefix = getattr(model_class, "wry_boolean_off_prefix", _DEFAULT_BOOLEAN_OFF_PREFIX)
                        off_option_name = f"--{off_prefix}-{name_for_option.replace('_', '-')}"

                    # Collision detection
                    collision_field = off_option_name.removeprefix("--").replace("-", "_")
                    if collision_field in model_class.model_fields:
                        import warnings

                        warnings.warn(
                            f"Boolean field '{field_name}' off-option '{off_option_name}' collides with "
                            f"existing field '{collision_field}'. Falling back to single flag. "
                            f"Use AutoOption(flag_off_option='other-name') to customize.",
                            UserWarning,
                            stacklevel=2,
                        )
                        click_kwargs["is_flag"] = True
                        click_kwargs.pop("show_default")
                    else:
                        # Use on/off pattern
                        option_name = f"{option_name}/{off_option_name}"
                        # Don't pop show_default - Click handles it for on/off flags

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
            env_prefix = getattr(model_class, "wry_env_prefix", "DRYCLI_")
            # Use alias for env var name if available, otherwise use field name
            name_for_env = field_info.alias if field_info.alias else field_name
            env_var_name = f"{env_prefix}{name_for_env.upper()}"

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

        # Handle arguments
        elif isinstance(wry_marker, WryArgument):
            # Auto-generate Click argument from Field info
            argument_name = field_name.lower()

            # Arguments don't have defaults in Click - they're positional
            click_kwargs = {}

            # Determine Click type from annotation
            base_type = get_args(annotation)[0]

            # Handle Optional types - extract the actual type
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

            # Check if field has a default or if env var is set
            import os

            env_prefix = getattr(model_class, "wry_env_prefix", "")
            name_for_env = field_info.alias if field_info.alias else field_name
            env_var_name = f"{env_prefix}{name_for_env.upper()}"
            env_var_set = env_var_name in os.environ

            # Mark as not required if field has default or env var is set
            is_required_arg = field_info.is_required() and not env_var_set

            arguments.append(click.argument(argument_name, **click_kwargs, required=is_required_arg))

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
    attrs: dict[str, Any] = {}  # Don't override required - let Click handle it

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
                    # Don't override required - preserve original setting

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
