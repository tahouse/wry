"""Environment variable handling utilities."""

import os
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic._internal._fields import PydanticUndefined

if TYPE_CHECKING:
    from .model import WryModel

T = TypeVar("T", bound="WryModel")


def get_env_var_names(model_class: type[T]) -> dict[str, str]:
    """Get mapping of field names to their environment variable names.

    Args:
        model_class: WryModel class

    Returns:
        Dictionary mapping field names to environment variable names
    """
    prefix = getattr(model_class, "env_prefix", "")
    env_vars = {}

    for field_name in model_class.model_fields:
        env_name = f"{prefix}{field_name.upper()}"
        env_vars[field_name] = env_name

    return env_vars


def print_env_vars(model_class: type[T]) -> None:
    """Print all supported environment variables with their types and descriptions.

    Args:
        model_class: WryModel class
    """
    print(f"\nEnvironment variables for {model_class.__name__}:")
    print("=" * 70)

    env_vars = get_env_var_names(model_class)
    type_hints = model_class.__annotations__

    for field_name, env_name in env_vars.items():
        field_info = model_class.model_fields[field_name]
        field_type = type_hints.get(field_name, Any)

        # Format type for display
        type_str = getattr(field_type, "__name__", str(field_type))

        # Check if field is required
        required = field_info.default is PydanticUndefined and field_info.default_factory is None

        # Build the output line
        line_parts = [f"  {env_name}"]

        # Add type info
        if field_type is bool:
            line_parts.append("(bool: true/false, 1/0, yes/no, on/off)")
        else:
            line_parts.append(f"({type_str})")

        # Add required/optional indicator
        if required:
            line_parts.append("(required)")

        # Add default value if present
        if not required and field_info.default is not PydanticUndefined:
            line_parts.append(f"(default={field_info.default!r})")

        # Add description
        if field_info.description:
            line_parts.append(f": {field_info.description}")

        print(" ".join(line_parts))

    print()


def get_env_values(model_class: type[T]) -> dict[str, Any]:
    """Get environment variable values as a dictionary.

    Args:
        model_class: WryModel class

    Returns:
        Dictionary of field names to values from environment

    Raises:
        ValidationError: If environment value cannot be converted to field type
    """
    env_vars = get_env_var_names(model_class)
    values = {}
    type_hints = model_class.__annotations__

    for field_name, env_name in env_vars.items():
        env_value = os.environ.get(env_name)
        if env_value is not None:
            field_type = type_hints.get(field_name, str)

            # Convert string to appropriate type
            try:
                converted_value: Any
                if field_type is bool:
                    # Handle various boolean representations
                    lower_value = env_value.lower()
                    if lower_value in ("true", "1", "yes", "on"):
                        converted_value = True
                    elif lower_value in ("false", "0", "no", "off"):
                        converted_value = False
                    else:
                        raise ValueError(f"Invalid boolean value: {env_value}")
                elif field_type is int:
                    converted_value = int(env_value)
                elif field_type is float:
                    converted_value = float(env_value)
                else:
                    # For all other types, pass as string and let Pydantic validate
                    converted_value = env_value
                values[field_name] = converted_value
            except (ValueError, TypeError):
                # For invalid conversions, fall back to string value
                values[field_name] = env_value

    return values
