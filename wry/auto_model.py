"""Auto-generating Click options for all model fields.

This module provides AutoWryModel, which automatically generates Click
options for all fields without requiring explicit annotations.
"""

# For type checking in mixed examples
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from pydantic.fields import FieldInfo

from .click_integration import AutoClickParameter
from .core import WryModel

if TYPE_CHECKING:
    pass


class AutoWryModel(WryModel):
    """A WryModel that automatically generates Click options for all fields.

    This class automatically treats all fields as if they were annotated with
    AutoOption, unless they already have explicit Click decorators.

    Example:
        ```python
        class MyConfig(AutoWryModel):
            # These automatically become --name and --count options
            name: str = Field(default="test", description="Your name")
            count: int = Field(default=1, description="Number of items")

            # You can still use explicit annotations to override
            verbose: Annotated[bool, AutoArgument] = Field(default=False)

            # Or use custom Click decorators
            input_file: Annotated[str, click.argument("input")] = Field()
        ```
    """

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Automatically add AutoOption to all unannotated fields."""
        super().__init_subclass__(**kwargs)

        # Skip if we've already processed this class
        if hasattr(cls, "_autowrymodel_processed"):
            return

        # Mark this class as processed
        cls._autowrymodel_processed = True  # type: ignore[attr-defined]

        # Process annotations to add AutoOption where needed
        if not hasattr(cls, "__annotations__"):
            cls.__annotations__ = {}

        # Process all annotations to add AutoOption where needed
        for attr_name, annotation in cls.__annotations__.copy().items():
            if attr_name.startswith("_"):
                continue

            # Check if it's already Annotated
            origin = get_origin(annotation)
            # Compare using string representation to handle module reload scenarios
            if origin is not None and str(origin) == "<class 'typing.Annotated'>":
                # Check if it has any Click-related metadata
                metadata = get_args(annotation)[1:]
                has_click_metadata = any(
                    # Check for AutoClickParameter enums
                    isinstance(m, AutoClickParameter)
                    or
                    # Check for Click decorators
                    (hasattr(m, "__module__") and "click" in str(m.__module__))
                    for m in metadata
                )

                if has_click_metadata:
                    # Already has Click configuration, skip
                    continue

                # Add AutoOption to existing annotation
                base_type = get_args(annotation)[0]
                # For Python 3.10 compatibility, we need to reconstruct manually
                # Create a new annotation with AutoOption prepended to existing metadata
                if not metadata:
                    cls.__annotations__[attr_name] = Annotated[base_type, AutoClickParameter.OPTION]
                elif len(metadata) == 1:
                    cls.__annotations__[attr_name] = Annotated[base_type, AutoClickParameter.OPTION, metadata[0]]
                elif len(metadata) == 2:
                    cls.__annotations__[attr_name] = Annotated[
                        base_type, AutoClickParameter.OPTION, metadata[0], metadata[1]
                    ]
                else:
                    # For more metadata, we skip adding AutoOption to avoid complexity
                    # This is a rare case and the field will still work
                    pass
            else:
                # Not annotated, add AutoOption
                cls.__annotations__[attr_name] = Annotated[annotation, AutoClickParameter.OPTION]

        # Also process fields that are defined with Field() but not in annotations
        for attr_name in dir(cls):
            if attr_name.startswith("_") or attr_name in cls.__annotations__:
                continue

            attr_value = getattr(cls, attr_name)

            # Check if it's a field
            if isinstance(attr_value, FieldInfo):
                # No annotation, infer type from field
                field_type = attr_value.annotation or Any
                cls.__annotations__[attr_name] = Annotated[field_type, AutoClickParameter.OPTION]


# Convenience function for creating auto models dynamically
def create_auto_model(name: str, fields: dict[str, Any], **kwargs: Any) -> type[AutoWryModel]:
    """Create an AutoWryModel dynamically.

    Args:
        name: Name of the model class
        fields: Dictionary of field names to field definitions
        **kwargs: Additional class attributes

    Returns:
        A new AutoWryModel subclass

    Example:
        ```python
        # Create a model dynamically
        MyConfig = create_auto_model(
            "MyConfig",
            {
                "host": Field(default="localhost", description="Server host"),
                "port": Field(default=8080, description="Server port"),
                "debug": Field(default=False, description="Debug mode"),
            }
        )

        # Use it with Click
        @click.command()
        @generate_click_parameters(MyConfig)
        def my_command(**kwargs):
            config = MyConfig.from_click_context(**kwargs)
            print(f"Connecting to {config.host}:{config.port}")
        ```
    """
    # Build annotations from fields
    annotations = {}
    field_definitions = {}

    for field_name, field_def in fields.items():
        if isinstance(field_def, tuple) and len(field_def) == 2:
            # Handle (type, Field(...)) format
            field_type, field_info = field_def
            annotations[field_name] = field_type
            field_definitions[field_name] = field_info
        elif isinstance(field_def, FieldInfo):
            # Extract type from field if possible
            field_type = field_def.annotation or Any
            annotations[field_name] = field_type
            field_definitions[field_name] = field_def
        else:
            # Assume it's a default value
            annotations[field_name] = type(field_def)
            field_definitions[field_name] = field_def

    # Create the class
    class_dict = {
        "__annotations__": annotations,
        "__module__": kwargs.get("__module__", "wry.auto_model"),
        **field_definitions,
        **kwargs,
    }

    # Use the base class if provided
    base_class = kwargs.get("__base__", AutoWryModel)
    if "__base__" in kwargs:
        del class_dict["__base__"]

    return type(name, (base_class,), class_dict)
