"""Core WryModel implementation."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast

import click
from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticUndefined

if TYPE_CHECKING:
    from click.decorators import FC

from .accessors import (
    ConstraintsAccessor,
    DefaultsAccessor,
    MaximumAccessor,
    MinimumAccessor,
    SourceAccessor,
)
from .env_utils import get_env_values, get_env_var_names, print_env_vars
from .field_utils import extract_field_constraints, get_field_maximum, get_field_minimum
from .sources import FieldWithSource, TrackedValue, ValueSource

# TypeVar for generic return types
T = TypeVar("T", bound="WryModel")


class WryModel(BaseModel):
    """Pydantic model with value source tracking.

    This model tracks where each configuration value came from:
    - DEFAULT: Model defaults
    - CLI: Command line arguments
    - ENV: Environment variables
    - JSON: Configuration file

    The precedence order is: CLI > ENV > JSON > DEFAULT

    Example:
        ```python
        class Config(WryModel):
            env_prefix = "APP_"
            name: str = "default"
            count: int = 0

        # Access value sources
        config = Config(name="Alice")
        print(config.source.name)  # ValueSource.CLI
        print(config.source.count)  # ValueSource.DEFAULT
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Class variables that should not trigger Pydantic warnings
    env_prefix: ClassVar[str] = ""
    _value_sources: dict[str, ValueSource] = {}
    _accessor_instances: dict[str, Any] = {}

    def __init__(self, **data: Any) -> None:
        # Standard Pydantic initialization
        super().__init__(**data)
        # Initialize source tracking after validation
        if "_value_sources" not in data:
            # Only initialize sources if not already provided
            self._value_sources = {}
            for field_name in self.__class__.model_fields:
                # Mark non-default values as programmatic
                if field_name in data:
                    self._value_sources[field_name] = ValueSource.CLI
                else:
                    self._value_sources[field_name] = ValueSource.DEFAULT

    @property
    def source(self) -> SourceAccessor:
        """Access to field source information."""
        if "source" not in self._accessor_instances:
            accessor = SourceAccessor(self)
            object.__setattr__(self, "_accessor_instances", {**self._accessor_instances, "source": accessor})
        accessor = object.__getattribute__(self, "_accessor_instances")["source"]
        assert isinstance(accessor, SourceAccessor)
        return accessor

    @property
    def minimum(self) -> MinimumAccessor:
        """Access to field minimum values via attribute notation.

        Examples:
            >>> config.minimum.age  # Returns minimum age constraint
            >>> config.minimum.score  # Returns minimum score constraint
        """
        if "minimum" not in self._accessor_instances:
            accessor = MinimumAccessor(self)
            object.__setattr__(self, "_accessor_instances", {**self._accessor_instances, "minimum": accessor})
        accessor = object.__getattribute__(self, "_accessor_instances")["minimum"]
        assert isinstance(accessor, MinimumAccessor)
        return accessor

    @property
    def maximum(self) -> MaximumAccessor:
        """Access to field maximum values via attribute notation.

        Examples:
            >>> config.maximum.age  # Returns maximum age constraint
            >>> config.maximum.score  # Returns maximum score constraint
        """
        if "maximum" not in self._accessor_instances:
            accessor = MaximumAccessor(self)
            object.__setattr__(self, "_accessor_instances", {**self._accessor_instances, "maximum": accessor})
        accessor = object.__getattribute__(self, "_accessor_instances")["maximum"]
        assert isinstance(accessor, MaximumAccessor)
        return accessor

    @property
    def constraints(self) -> ConstraintsAccessor:
        """Access to all field constraints via attribute notation.

        Examples:
            >>> config.constraints.age  # Returns {'ge': 0, 'le': 120}
            >>> config.constraints.name  # Returns {'min_length': 1}
        """
        if "constraints" not in self._accessor_instances:
            accessor = ConstraintsAccessor(self)
            object.__setattr__(self, "_accessor_instances", {**self._accessor_instances, "constraints": accessor})
        accessor = object.__getattribute__(self, "_accessor_instances")["constraints"]
        assert isinstance(accessor, ConstraintsAccessor)
        return accessor

    @property
    def defaults(self) -> DefaultsAccessor:
        """Access to field default values via attribute notation.

        Examples:
            >>> config.defaults.timeout  # Returns default timeout value
            >>> config.defaults.retries  # Returns default retries value
        """
        if "defaults" not in self._accessor_instances:
            accessor = DefaultsAccessor(self)
            object.__setattr__(self, "_accessor_instances", {**self._accessor_instances, "defaults": accessor})
        accessor = object.__getattribute__(self, "_accessor_instances")["defaults"]
        assert isinstance(accessor, DefaultsAccessor)
        return accessor

    @classmethod
    def create_with_sources(cls: type[T], config_data: dict[str, TrackedValue]) -> T:
        """Create a model instance from TrackedValue objects with source tracking.

        Args:
            config_data: Dictionary of field names to TrackedValue objects

        Returns:
            Model instance with source tracking

        Example:
            ```python
            config = MyConfig.create_with_sources({
                'name': TrackedValue('Alice', ValueSource.CLI),
                'count': TrackedValue(5, ValueSource.ENV)
            })
            ```
        """
        # Extract values and sources
        values = {}
        sources = {}
        for field_name, config_value in config_data.items():
            values[field_name] = config_value.value
            sources[field_name] = config_value.source

        # Create instance with values
        instance = cls(**values)
        # Set the source tracking
        instance._value_sources = sources
        return instance

    def get_value_source(self, field_name: str) -> ValueSource:
        """Get the source of a specific field value.

        Args:
            field_name: Name of the field

        Returns:
            ValueSource enum indicating where the value came from
        """
        sources: dict[str, ValueSource] = getattr(self, "_value_sources", {})
        return sources.get(field_name, ValueSource.DEFAULT)

    def get_sources_summary(self) -> dict[ValueSource, list[str]]:
        """Get a summary of which fields came from which sources.

        Returns:
            Dictionary mapping sources to list of field names
        """
        sources = getattr(self, "_value_sources", {})
        summary: dict[ValueSource, list[str]] = {}
        for field_name, source in sources.items():
            summary.setdefault(source, []).append(field_name)
        return summary

    def model_dump_with_sources(self, **kwargs: Any) -> dict[str, Any]:
        """Dump model data with source information.

        Returns:
            Dictionary with both values and their sources
        """
        data = self.model_dump(**kwargs)
        sources = {k: v.value for k, v in self._value_sources.items()}
        return {"values": data, "sources": sources}

    def get_field_with_source(self, field_name: str) -> FieldWithSource:
        """Get a field value wrapped with its source information.

        Args:
            field_name: Name of the field

        Returns:
            FieldWithSource object containing value and source
        """
        value = getattr(self, field_name)
        source = self.get_value_source(field_name)
        return FieldWithSource(value=value, source=source)

    def get_field_constraints(self, field_name: str) -> dict[str, Any]:
        """Extract all constraints from a field.

        Args:
            field_name: Name of the field

        Returns:
            Dictionary of constraint names to values

        Raises:
            AttributeError: If field doesn't exist
        """
        if field_name not in self.__class__.model_fields:
            raise AttributeError(f"Field '{field_name}' not found in model")
        return extract_field_constraints(self.__class__.model_fields[field_name])

    def get_field_minimum(self, field_name: str) -> int | float | None:
        """Extract the minimum value from a field's constraints or default.

        Priority order:
        1. 'ge' (greater than or equal) constraint
        2. 'gt' (greater than) constraint
        3. Default value if numeric and positive

        Args:
            field_name: Name of the field

        Returns:
            Minimum value or None if no minimum constraint

        Raises:
            AttributeError: If field doesn't exist
        """
        if field_name not in self.__class__.model_fields:
            raise AttributeError(f"Field '{field_name}' not found in model")
        return get_field_minimum(self.__class__.model_fields[field_name])

    def get_field_maximum(self, field_name: str) -> int | float | None:
        """Extract the maximum value from a field's constraints.

        Priority order:
        1. 'le' (less than or equal) constraint
        2. 'lt' (less than) constraint

        Args:
            field_name: Name of the field

        Returns:
            Maximum value or None if no maximum constraint

        Raises:
            AttributeError: If field doesn't exist
        """
        if field_name not in self.__class__.model_fields:
            raise AttributeError(f"Field '{field_name}' not found in model")
        return get_field_maximum(self.__class__.model_fields[field_name])

    def get_field_range(self, field_name: str) -> tuple[int | float | None, int | float | None]:
        """Extract the valid range from a field's constraints.

        Args:
            field_name: Name of the field

        Returns:
            Tuple of (min, max) values, either can be None
        """
        return (self.get_field_minimum(field_name), self.get_field_maximum(field_name))

    def get_field_default(self, field_name: str) -> Any:
        """Get the default value for a field.

        Args:
            field_name: Name of the field

        Returns:
            Default value or None

        Raises:
            AttributeError: If field doesn't exist
        """
        if field_name not in self.__class__.model_fields:
            raise AttributeError(f"Field '{field_name}' not found in model")
        return self.__class__.model_fields[field_name].default

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to exclude all accessor properties from serialization.

        This prevents the source, minimum, maximum, constraints, and defaults
        accessors from appearing in the output.
        """
        # Get the base dump
        data = super().model_dump(**kwargs)
        # Remove any accessor keys that might have been included
        accessor_keys = {"source", "minimum", "maximum", "constraints", "defaults"}
        return {k: v for k, v in data.items() if k not in accessor_keys}

    @classmethod
    def from_json_file(cls: type[T], file_path: Path) -> T:
        """Load configuration from a JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Model instance with values loaded from file

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
            ValidationError: If data doesn't match model schema
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        # Convert to TrackedValue objects
        config_data = {}
        for field_name, value in data.items():
            if field_name in cls.model_fields:
                config_data[field_name] = TrackedValue(value, ValueSource.JSON)

        # Create instance with source tracking
        return cls.create_with_sources(config_data)

    def to_json_file(self, file_path: Path) -> None:
        """Save configuration to a JSON file.

        Args:
            file_path: Path to save JSON file
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def get_env_var_names(cls: type[T]) -> dict[str, str]:
        """Get mapping of field names to their environment variable names.

        Returns:
            Dictionary mapping field names to environment variable names
        """
        return get_env_var_names(cls)

    @classmethod
    def print_env_vars(cls: type[T]) -> None:
        """Print all supported environment variables with their types and descriptions."""
        print_env_vars(cls)

    @classmethod
    def get_env_values(cls: type[T]) -> dict[str, Any]:
        """Get environment variable values as a dictionary.

        Returns:
            Dictionary of field names to values from environment

        Raises:
            ValidationError: If environment value cannot be converted to field type
        """
        return get_env_values(cls)

    @classmethod
    def load_from_env(cls: type[T]) -> T:
        """Load configuration from environment variables.

        Returns:
            Model instance with values from environment

        Example:
            ```bash
            export APP_NAME="MyApp"
            export APP_DEBUG=true
            ```

            ```python
            class AppConfig(WryModel):
                env_prefix = "APP_"
                name: str = "default"
                debug: bool = False

            config = AppConfig.load_from_env()
            print(config.name)  # "MyApp"
            print(config.source.name)  # ValueSource.ENV
            ```
        """
        env_values = cls.get_env_values()

        # Convert to TrackedValue objects
        config_data = {}
        for field_name, value in env_values.items():
            config_data[field_name] = TrackedValue(value, ValueSource.ENV)

        # Add defaults for missing fields
        for field_name, field_info in cls.model_fields.items():
            if field_name not in config_data:
                if field_info.default is not PydanticUndefined:
                    config_data[field_name] = TrackedValue(field_info.default, ValueSource.DEFAULT)
                elif field_info.default_factory is not None:
                    config_data[field_name] = TrackedValue(
                        cast(Callable[[], Any], field_info.default_factory)(),
                        ValueSource.DEFAULT,
                    )

        return cls.create_with_sources(config_data)

    @classmethod
    def from_click_context(cls: type[T], ctx: Any = None, strict: bool | None = None, **kwargs: Any) -> T:
        """Build configuration from Click context with full source tracking.

        Args:
            ctx: Click context (required for source tracking)
            strict: How to handle extra kwargs
                   - None (default): Use cls.model_config.get('extra', 'ignore')
                   - True: Raise error if kwargs contains non-model fields
                   - False: Silently ignore non-model fields
            **kwargs: Additional keyword arguments (typically from Click)

        Returns:
            Model instance with full source tracking

        Raises:
            RuntimeError: If no Click context is available

        Example:
            ```python
            @click.command()
            @generate_click_parameters(MyConfig)
            @click.pass_context
            def my_command(ctx, **kwargs):
                config = MyConfig.from_click_context(ctx, **kwargs)
                print(f"Hello {config.name}")
                print(f"Source: {config.source.name}")  # Accurate source
            ```
        """
        # Get the current context if not provided
        if ctx is None:
            try:
                ctx = click.get_current_context()
            except RuntimeError:
                # No Click context available
                raise RuntimeError(
                    "No Click context available. "
                    "Use @click.pass_context and call from_click_context(ctx, **kwargs) for source tracking, "
                    "or use direct instantiation Model(**kwargs) without source tracking."
                ) from None

        # Handle strict mode
        if strict is None:
            # Default to model's extra config
            strict = cls.model_config.get("extra", "ignore") == "forbid"

        if strict:
            # Check for extra fields
            extra_fields = set(kwargs.keys()) - set(cls.model_fields.keys())
            if extra_fields:
                raise ValueError(f"Extra fields not allowed: {extra_fields}")

        # Filter kwargs to only include model fields
        model_fields = set(cls.model_fields.keys())
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in model_fields}

        # If kwargs are empty but ctx.params has values, use those (for test compatibility)
        if not filtered_kwargs and hasattr(ctx, "params") and ctx.params:
            filtered_kwargs = {k: v for k, v in ctx.params.items() if k in model_fields}

        # Get JSON data from context if available
        json_data = ctx.obj.get("json_data", {}) if ctx.obj else {}

        # Get environment variable values
        env_values = cls.get_env_values()

        # Build config data with proper precedence: defaults < env < json < cli
        config_data = {}

        # 1. Start with defaults for all fields
        for field_name, field_info in cls.model_fields.items():
            if field_info.default is not PydanticUndefined:
                config_data[field_name] = TrackedValue(field_info.default, ValueSource.DEFAULT)
            elif field_info.default_factory is not None:
                factory = field_info.default_factory
                config_data[field_name] = TrackedValue(cast(Callable[[], Any], factory)(), ValueSource.DEFAULT)

        # 2. Override with environment values
        for field_name, value in env_values.items():
            config_data[field_name] = TrackedValue(value, ValueSource.ENV)

        # 3. Override with JSON values
        for field_name, value in json_data.items():
            if field_name in cls.model_fields:
                config_data[field_name] = TrackedValue(value, ValueSource.JSON)

        # 4. Override with CLI values from kwargs (but respect Click's source info)
        for field_name in cls.model_fields:
            if field_name in filtered_kwargs:
                value = filtered_kwargs[field_name]

                # Check Click's parameter source if available
                try:
                    param_source = ctx.get_parameter_source(field_name)
                    if param_source is not None:
                        source_str = str(param_source)
                        # Only override if it's actually from CLI
                        if "COMMANDLINE" in source_str:
                            config_data[field_name] = TrackedValue(value, ValueSource.CLI)
                            continue
                        # Skip if it's DEFAULT or ENVIRONMENT - already handled above
                        continue
                except (AttributeError, RuntimeError):
                    pass

                # No source info - if value differs from what we have, assume CLI
                if field_name not in config_data or config_data[field_name].value != value:
                    config_data[field_name] = TrackedValue(value, ValueSource.CLI)

            elif hasattr(ctx, "params") and field_name in ctx.params:
                # Handle values that are in ctx.params but not in kwargs (test scenarios)
                value = ctx.params[field_name]
                if field_name not in config_data or config_data[field_name].value != value:
                    config_data[field_name] = TrackedValue(value, ValueSource.CLI)

        return cls.create_with_sources(config_data)

    def extract_subset(self, target_model: type[BaseModel]) -> dict[str, Any]:
        """Extract fields from this config that match target model's structure.

        Useful for passing configuration subsets to different components.

        Args:
            target_model: The Pydantic model to extract fields for

        Returns:
            Dictionary of field names to values that exist in target model

        Example:
            ```python
            class DatabaseConfig(BaseModel):
                host: str
                port: int

            class AppConfig(WryModel):
                app_name: str
                host: str = "localhost"
                port: int = 5432
                debug: bool = False

            app_config = AppConfig(app_name="myapp", host="db.example.com")
            db_config = DatabaseConfig(**app_config.extract_subset(DatabaseConfig))
            # db_config.host = "db.example.com"
            # db_config.port = 5432
            ```
        """
        return self.extract_subset_from(self, target_model)

    @classmethod
    def extract_subset_from(cls, source: Any, target_model: type[BaseModel] | None = None) -> dict[str, Any]:
        """Class method to extract fields from any source matching target model.

        Args:
            source: Source object (dict, BaseModel instance, etc.)
            target_model: The Pydantic model to extract fields for (defaults to cls)

        Returns:
            Dictionary of field names to values that exist in target model
        """
        if target_model is None:
            target_model = cls

        target_fields = set(target_model.model_fields.keys())
        result = {}

        # Handle different source types
        if isinstance(source, dict):
            source_data = source
        elif isinstance(source, BaseModel):
            source_data = source.model_dump()
        elif hasattr(source, "__dict__"):
            # First get instance attributes
            source_data = {k: v for k, v in source.__dict__.items() if not k.startswith("_")}
            # Also check class attributes if instance dict is empty
            if not source_data:
                for attr in dir(source):
                    if not attr.startswith("_") and attr not in source_data:
                        try:
                            value = getattr(source, attr)
                            if not callable(value):
                                source_data[attr] = value
                        except (AttributeError, TypeError):
                            pass
        else:
            # Try to extract attributes from object
            source_data = {}
            for attr in dir(source):
                if not attr.startswith("_"):
                    try:
                        value = getattr(source, attr)
                        if not callable(value):
                            source_data[attr] = value
                    except (AttributeError, TypeError):
                        pass

        # Extract matching fields
        for field_name in target_fields:
            if field_name in source_data:
                result[field_name] = source_data[field_name]
            else:
                # Check if target field has a default value
                field_info = target_model.model_fields[field_name]
                if field_info.default is not PydanticUndefined:
                    result[field_name] = field_info.default
                elif field_info.default_factory is not None:
                    result[field_name] = cast(Callable[[], Any], field_info.default_factory)()

        return result

    @classmethod
    def generate_click_parameters(cls) -> "Callable[[FC], FC]":
        """Generate Click parameters decorator for this model.

        This is a convenience method that allows using the decorator
        directly from the model class without needing to import it.

        Example:
            ```python
            @click.command()
            @MyConfig.generate_click_parameters()
            @click.pass_context
            def cli(ctx, **kwargs):
                config = MyConfig.from_click_context(ctx, **kwargs)
            ```

        Returns:
            The generate_click_parameters decorator configured for this model
        """
        from ..click_integration import generate_click_parameters

        return generate_click_parameters(cls)
