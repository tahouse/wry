#!/usr/bin/env python3
"""Example of using multiple Pydantic models with wry."""

from typing import Annotated

import click
from pydantic import Field

from wry import AutoOption, WryModel, generate_click_parameters
from wry.multi_model import create_models, multi_model, split_kwargs_by_model


# Define separate argument models
class ServerArgs(WryModel):
    """Server arguments."""

    host: Annotated[str, AutoOption] = Field(default="localhost", description="Server host")
    port: Annotated[int, AutoOption] = Field(default=8080, description="Server port", ge=1, le=65535)
    workers: Annotated[int, AutoOption] = Field(default=4, description="Number of workers")


class DatabaseArgs(WryModel):
    """Database arguments."""

    url: Annotated[str, AutoOption] = Field(description="Database URL")
    pool_size: Annotated[int, AutoOption] = Field(default=10, description="Connection pool size")
    timeout: Annotated[int, AutoOption] = Field(default=30, description="Query timeout in seconds")


class SecurityArgs(WryModel):
    """Security arguments."""

    api_key: Annotated[str, AutoOption] = Field(description="API key for authentication")
    enable_cors: Annotated[bool, AutoOption] = Field(default=True, description="Enable CORS")
    allowed_origins: Annotated[str, AutoOption] = Field(default="*", description="Allowed CORS origins")


# Method 1: Manual splitting
@click.command("manual")
@generate_click_parameters(ServerArgs)
@generate_click_parameters(DatabaseArgs)
@generate_click_parameters(SecurityArgs)
@click.pass_context
def manual_command(ctx: click.Context, **kwargs):
    """Example using manual kwargs splitting."""
    # Split kwargs manually
    server_kwargs = {k: v for k, v in kwargs.items() if k in ServerArgs.model_fields}
    db_kwargs = {k: v for k, v in kwargs.items() if k in DatabaseArgs.model_fields}
    security_kwargs = {k: v for k, v in kwargs.items() if k in SecurityArgs.model_fields}

    # Create model instances
    server = ServerArgs.from_click_context(ctx, **server_kwargs)
    database = DatabaseArgs.from_click_context(ctx, **db_kwargs)
    security = SecurityArgs.from_click_context(ctx, **security_kwargs)

    click.echo("=== Manual Method ===")
    click.echo(f"Server: {server.host}:{server.port} with {server.workers} workers")
    click.echo(f"Database: {database.url} (pool: {database.pool_size})")
    click.echo(f"Security: CORS={security.enable_cors}, Origins={security.allowed_origins}")

    # Show source tracking
    click.echo("\nSource tracking:")
    click.echo(f"  server.host source: {server.source.host.value}")
    click.echo(f"  database.url source: {database.source.url.value}")


# Method 2: Using split_kwargs_by_model helper
@click.command("helper")
@generate_click_parameters(ServerArgs)
@generate_click_parameters(DatabaseArgs)
@generate_click_parameters(SecurityArgs)
@click.pass_context
def helper_command(ctx: click.Context, **kwargs):
    """Example using the split_kwargs_by_model helper."""
    # Use helper to split kwargs
    _ = split_kwargs_by_model(kwargs, ServerArgs, DatabaseArgs, SecurityArgs)

    # Create model instances from split kwargs
    configs = create_models(ctx, kwargs, ServerArgs, DatabaseArgs, SecurityArgs)

    server = configs[ServerArgs]
    database = configs[DatabaseArgs]
    security = configs[SecurityArgs]

    click.echo("=== Helper Method ===")
    click.echo(f"Server: {server.host}:{server.port}")
    click.echo(f"Database: {database.url}")
    click.echo(f"Security: API key provided: {bool(security.api_key)}")


# Method 3: Using multi_model decorator (cleanest)
@click.command("multi")
@multi_model(ServerArgs, DatabaseArgs, SecurityArgs)
@click.pass_context
def multi_command(ctx: click.Context, **kwargs):
    """Example using the multi_model decorator.

    This approach applies all decorators in one go.
    """
    # Use create_models helper
    configs = create_models(ctx, kwargs, ServerArgs, DatabaseArgs, SecurityArgs)

    server = configs[ServerArgs]
    database = configs[DatabaseArgs]
    security = configs[SecurityArgs]

    click.echo("=== multi_model Decorator ===")
    click.echo(f"Server: {server.host}:{server.port}")
    click.echo(f"Database: {database.url}")
    click.echo(f"Security: API key = {security.api_key}")

    # Still have access to source tracking
    click.echo(f"\nServer host came from: {server.source.host.value}")


# CLI group
@click.group()
def cli():
    """Examples of multi-model argument handling."""
    pass


cli.add_command(manual_command)
cli.add_command(helper_command)
cli.add_command(multi_command)


# Add a command to show environment variables for all models
@cli.command("show-env")
def show_env():
    """Show all environment variables for all config models."""
    click.echo("=== Environment Variables ===")
    click.echo("\nServerArgs:")
    ServerArgs.print_env_vars()
    click.echo("\nDatabaseArgs:")
    DatabaseArgs.print_env_vars()
    click.echo("\nSecurityArgs:")
    SecurityArgs.print_env_vars()


if __name__ == "__main__":
    # Test the commands
    from click.testing import CliRunner

    runner = CliRunner()

    # Common arguments
    args = [
        "--host",
        "api.example.com",
        "--port",
        "443",
        "--url",
        "postgresql://localhost/mydb",
        "--api-key",
        "secret123",
        "--pool-size",
        "20",
    ]

    print("Testing manual command:")
    result = runner.invoke(manual_command, args)
    print(result.output)

    print("\nTesting helper command:")
    result = runner.invoke(helper_command, args)
    print(result.output)

    print("\nTesting multi command:")
    result = runner.invoke(multi_command, args)
    print(result.output)
