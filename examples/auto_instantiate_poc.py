#!/usr/bin/env python3
"""Proof of concept for automatic model instantiation."""

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

import click
from pydantic import BaseModel, Field

from wry import AutoWryModel, WryModel
from wry.click_integration import generate_click_parameters
from wry.multi_model import split_kwargs_by_model

T = TypeVar("T", bound=BaseModel)


def auto_instantiate(model_class: type[T]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that automatically instantiates a model from Click parameters.

    This decorator:
    1. Applies generate_click_parameters() to create CLI options
    2. Inspects the function signature to find the parameter expecting the model
    3. Automatically handles click.pass_context for source tracking
    4. Instantiates the model and passes it to the function

    Example:
        @click.command()
        @auto_instantiate(MyConfig)
        def main(my_model: MyConfig):
            print(f"Hello {my_model.name}")
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Check if the function is already wrapped by click.pass_context
        is_already_pass_context = hasattr(func, "__click_pass_context__") and func.__click_pass_context__

        # First, apply generate_click_parameters
        func = generate_click_parameters(model_class)(func)

        # Get function signature and type hints - use the original function if wrapped
        original_func = func.__wrapped__ if hasattr(func, "__wrapped__") else func
        sig = inspect.signature(original_func)
        type_hints = get_type_hints(original_func)

        # Find the parameter that expects our model type
        model_param_name = None
        has_context_param = False

        for param_name, _param in sig.parameters.items():
            param_type = type_hints.get(param_name)

            # Check if this parameter expects our model type
            if param_type == model_class:
                model_param_name = param_name

            # Check if function already expects context
            if param_type == click.Context or param_name == "ctx":
                has_context_param = True

        if model_param_name is None:
            raise ValueError(
                f"Function {func.__name__} must have a parameter with type annotation {model_class.__name__}"
            )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context if present
            ctx = None
            func_args = args

            if args and isinstance(args[0], click.Context):
                ctx = args[0]
                func_args = args[1:]  # Remove context from args
            else:
                # Try to get current context for source tracking
                try:
                    ctx = click.get_current_context()
                except RuntimeError:
                    ctx = None

            # Create the model instance
            if ctx and issubclass(model_class, WryModel):
                # Use from_click_context for source tracking
                model_instance = model_class.from_click_context(ctx, **kwargs)
            else:
                # Fallback to direct instantiation
                model_instance = model_class(**kwargs)

            # Prepare new kwargs with the model instance
            new_kwargs = {model_param_name: model_instance}

            # Call the original function
            if has_context_param and ctx:
                return func(ctx, *func_args, **new_kwargs)
            else:
                return func(*func_args, **new_kwargs)

        # If the function doesn't already have pass_context, add it
        # This ensures we can do source tracking
        if not has_context_param and not is_already_pass_context and issubclass(model_class, WryModel):
            wrapper = click.pass_context(wrapper)

        return wrapper

    return decorator


# Let's also create a method version that can be added to WryModel
def create_auto_command(model_class: type[T]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Alternative implementation as a classmethod for WryModel."""
    return auto_instantiate(model_class)


# Example models to test with
class ServerConfig(AutoWryModel):
    """Server configuration."""

    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port", ge=1, le=65535)
    debug: bool = Field(default=False, description="Debug mode")


class DatabaseConfig(AutoWryModel):
    """Database configuration."""

    url: str = Field(default="sqlite:///app.db", description="Database URL")
    pool_size: int = Field(default=5, description="Connection pool size", ge=1)
    echo: bool = Field(default=False, description="Echo SQL queries")


# Test commands demonstrating different usage patterns
@click.group()
def cli():
    """Test automatic instantiation."""
    pass


@cli.command("simple")
@auto_instantiate(ServerConfig)
def simple_command(server: ServerConfig):
    """Simple usage - function parameter named 'server'."""
    click.echo(f"Server running at {server.host}:{server.port}")
    click.echo(f"Debug mode: {server.debug}")

    # Source tracking works automatically!
    click.echo(f"\nHost source: {server.source.host}")
    click.echo(f"Port source: {server.source.port}")


@cli.command("custom-name")
@auto_instantiate(DatabaseConfig)
def custom_name_command(db_settings: DatabaseConfig):
    """Custom parameter name - 'db_settings' instead of 'config'."""
    click.echo(f"Database URL: {db_settings.url}")
    click.echo(f"Pool size: {db_settings.pool_size}")
    click.echo(f"Echo SQL: {db_settings.echo}")

    # Show source summary
    sources = db_settings.get_sources_summary()
    click.echo(f"\nConfiguration sources: {sources}")


@cli.command("with-context")
@click.pass_context
@auto_instantiate(ServerConfig)
def with_context_command(ctx: click.Context, my_server: ServerConfig):
    """Function that already uses click.pass_context."""
    click.echo(f"Command name: {ctx.info_name}")
    click.echo(f"Server: {my_server.host}:{my_server.port}")

    # Context is available as usual
    click.echo(f"Parent command: {ctx.parent.info_name if ctx.parent else 'None'}")


# Multi-model proof of concept
def multi_auto_instantiate(*model_classes: type[BaseModel]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Proof of concept for multiple model instantiation."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Apply generate_click_parameters for each model
        for i, model_class in enumerate(reversed(model_classes)):
            # Only first model uses strict=True, others use strict=False
            strict = i == 0
            func = generate_click_parameters(model_class, strict=strict)(func)

        # Get function signature and type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Map each model class to its parameter name
        model_params = {}
        has_context = False

        for param_name, _param in sig.parameters.items():
            param_type = type_hints.get(param_name)

            if param_type == click.Context or param_name == "ctx":
                has_context = True
            elif param_type in model_classes:
                model_params[param_type] = param_name

        # Verify all models have parameters
        missing = set(model_classes) - set(model_params.keys())
        if missing:
            raise ValueError(f"Function {func.__name__} missing parameters for models: {[m.__name__ for m in missing]}")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context
            ctx = None
            func_args = args

            if args and isinstance(args[0], click.Context):
                ctx = args[0]
                func_args = args[1:]
            else:
                try:
                    ctx = click.get_current_context()
                except RuntimeError:
                    pass

            # Split kwargs by model
            split_kwargs = split_kwargs_by_model(kwargs, *model_classes)

            # Create instances for each model
            instances = {}
            for model_class, param_name in model_params.items():
                model_kwargs = split_kwargs[model_class]

                # Create instance
                if ctx and issubclass(model_class, WryModel):
                    instance = model_class.from_click_context(ctx, **model_kwargs)
                else:
                    instance = model_class(**model_kwargs)

                instances[param_name] = instance

            # Call original function
            if has_context and ctx:
                return func(ctx, *func_args, **instances)
            else:
                return func(*func_args, **instances)

        # Add pass_context if needed
        if not has_context:
            wrapper = click.pass_context(wrapper)

        return wrapper

    return decorator


@cli.command("multi")
@multi_auto_instantiate(ServerConfig, DatabaseConfig)
def multi_command(server_cfg: ServerConfig, db: DatabaseConfig):
    """Multiple models with automatic instantiation."""
    click.echo("Server Configuration:")
    click.echo(f"  Host: {server_cfg.host}:{server_cfg.port}")
    click.echo(f"  Debug: {server_cfg.debug}")

    click.echo("\nDatabase Configuration:")
    click.echo(f"  URL: {db.url}")
    click.echo(f"  Pool Size: {db.pool_size}")

    click.echo("\nSources:")
    click.echo(f"  Server host from: {server_cfg.source.host}")
    click.echo(f"  Database URL from: {db.source.url}")


# Demonstrate as a classmethod approach
class AppConfig(AutoWryModel):
    """Example showing potential classmethod syntax."""

    name: str = Field(description="Application name")
    version: str = Field(default="1.0.0", description="Version")

    @classmethod
    def click_command(cls) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Potential API as a classmethod."""
        return auto_instantiate(cls)


@cli.command("classmethod")
@AppConfig.click_command()
def classmethod_command(app: AppConfig):
    """Using the classmethod approach."""
    click.echo(f"Running {app.name} v{app.version}")
    click.echo(f"Name source: {app.source.name}")


if __name__ == "__main__":
    # Test the commands
    import sys

    if len(sys.argv) > 1:
        # Run the CLI normally
        cli()
    else:
        # Run tests
        from click.testing import CliRunner

        runner = CliRunner()

        print("=== Simple Command Test ===")
        result = runner.invoke(cli, ["simple", "--host", "0.0.0.0", "--port", "9000", "--debug"])
        print(result.output)

        print("\n=== Custom Name Test ===")
        result = runner.invoke(cli, ["custom-name", "--url", "postgresql://localhost/mydb"])
        print(result.output)

        print("\n=== With Context Test ===")
        result = runner.invoke(cli, ["with-context", "--host", "192.168.1.1"])
        print(result.output)

        print("\n=== Multi-Model Test ===")
        result = runner.invoke(
            cli,
            ["multi", "--host", "api.example.com", "--debug", "--url", "mysql://localhost/app", "--pool-size", "10"],
        )
        print(result.output)

        print("\n=== Environment Variable Test ===")
        import os

        os.environ["WRY_NAME"] = "MyApp"
        result = runner.invoke(cli, ["classmethod", "--version", "2.0.0"])
        print(result.output)
