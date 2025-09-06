"""Utilities for handling multiple models with generate_click_parameters.

This module provides helper functions and decorators for working with
multiple Pydantic models in a single Click command.
"""

from typing import Any, Protocol, TypeVar, runtime_checkable

import click
from pydantic import BaseModel

from .core import WryModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class HasFromClickContext(Protocol):
    """Protocol for models that have from_click_context method."""

    @classmethod
    def from_click_context(cls, ctx: Any, **kwargs: Any) -> Any: ...


def split_kwargs_by_model(
    kwargs: dict[str, Any], *model_classes: type[BaseModel]
) -> dict[type[BaseModel], dict[str, Any]]:
    """Split kwargs among multiple model classes based on their fields.

    Args:
        kwargs: All keyword arguments from Click
        *model_classes: Pydantic model classes to split kwargs for

    Returns:
        Dictionary mapping each model class to its relevant kwargs

    Example:
        ```python
        @click.command()
        @generate_click_parameters(ServerConfig)
        @generate_click_parameters(DatabaseConfig)
        def cmd(**kwargs):
            configs = split_kwargs_by_model(kwargs, ServerConfig, DatabaseConfig)
            server_config = ServerConfig(**configs[ServerConfig])
            db_config = DatabaseConfig(**configs[DatabaseConfig])
        ```
    """
    result: dict[type[BaseModel], dict[str, Any]] = {}
    used_fields: set[str] = set()

    for model_class in model_classes:
        model_kwargs = {}
        for field_name in model_class.model_fields:
            if field_name in kwargs:
                model_kwargs[field_name] = kwargs[field_name]
                used_fields.add(field_name)
        result[model_class] = model_kwargs

    # Check for unused kwargs
    unused = set(kwargs.keys()) - used_fields
    if unused:
        import warnings

        warnings.warn(
            f"Unused kwargs that don't belong to any model: {unused}",
            UserWarning,
            stacklevel=2,
        )

    return result


def create_models(
    ctx: click.Context, kwargs: dict[str, Any], *model_classes: type[BaseModel]
) -> dict[type[BaseModel], BaseModel]:
    """Create model instances from kwargs, with source tracking if available.

    Args:
        ctx: Click context for source tracking
        kwargs: All keyword arguments from Click
        *model_classes: Pydantic model classes to instantiate

    Returns:
        Dictionary mapping each model class to its instance

    Example:
        ```python
        @click.command()
        @generate_click_parameters(ServerModel)
        @generate_click_parameters(DatabaseModel)
        @click.pass_context
        def cmd(ctx, **kwargs):
            models = create_models(ctx, kwargs, ServerModel, DatabaseModel)
            server = models[ServerModel]
            db = models[DatabaseModel]
        ```
    """
    split_kwargs = split_kwargs_by_model(kwargs, *model_classes)
    result: dict[type[BaseModel], BaseModel] = {}

    for model_class in model_classes:
        model_kwargs = split_kwargs[model_class]

        # Use from_click_context if available for source tracking
        instance: BaseModel
        if ctx is not None and issubclass(model_class, WryModel):
            # WryModel has from_click_context method
            instance = model_class.from_click_context(ctx, **model_kwargs)
        else:
            instance = model_class(**model_kwargs)

        result[model_class] = instance

    return result


def multi_model(*model_classes: type[BaseModel], strict: bool = False) -> Any:
    """Decorator for commands using multiple Pydantic models.

    This provides a cleaner interface for commands that need multiple
    configuration models, automatically handling kwargs splitting.

    Note: If you need source tracking, add @click.pass_context to your function.

    Example:
        ```python
        @click.command()
        @multi_model(ServerModel, DatabaseModel)
        @click.pass_context  # Add this for source tracking
        def my_command(ctx, **kwargs):
            models = create_models(ctx, kwargs, ServerModel, DatabaseModel)
            server = models[ServerModel]
            database = models[DatabaseModel]
            print(f"Server: {server.host}:{server.port}")
            print(f"Database: {database.url}")
        ```
    """

    def decorator(func: Any) -> Any:
        # Import here to avoid circular imports
        from .click_integration import generate_click_parameters

        # Apply generate_click_parameters for each model
        decorated = func
        for model_class in reversed(model_classes):
            decorated = generate_click_parameters(model_class, strict=strict)(decorated)

        return decorated

    return decorator


# Singleton option support
_SINGLETON_OPTIONS: dict[str, Any] = {}  # Stores decorators, not Option instances


def singleton_option(*args: Any, **kwargs: Any) -> Any:
    """Create a singleton Click option that's only added once per command.

    This is useful for options that should appear only once even when
    multiple models are used.

    Example:
        ```python
        # In your model
        class MyConfig(WryModel):
            debug: Annotated[bool, singleton_option("--debug", is_flag=True)] = Field(
                default=False, description="Enable debug mode"
            )
        ```
    """
    # Create a unique key for this option
    option_names = args if args else [kwargs.get("param_decls", ["--unknown"])[0]]
    key = ",".join(str(name) for name in option_names)

    # Return existing option if already created
    if key in _SINGLETON_OPTIONS:
        return _SINGLETON_OPTIONS[key]

    # Create new option and cache it
    option = click.option(*args, **kwargs)
    _SINGLETON_OPTIONS[key] = option

    # Mark it as singleton
    option._is_singleton = True  # type: ignore

    return option
