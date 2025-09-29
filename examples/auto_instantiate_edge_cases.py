#!/usr/bin/env python3
"""Edge cases for automatic model instantiation - mixing models with raw Click options."""

import click
from pydantic import Field

from examples.auto_instantiate_poc import auto_instantiate, multi_auto_instantiate
from wry import AutoWryModel


class ServerConfig(AutoWryModel):
    """Server configuration."""

    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port")


class DatabaseConfig(AutoWryModel):
    """Database configuration."""

    url: str = Field(default="sqlite:///app.db", description="Database URL")
    pool_size: int = Field(default=5, description="Connection pool size")


# Example 1: Single model + additional Click options
@click.command()
@click.option("--dry-run", is_flag=True, help="Don't actually start the server")
@click.option("--config-file", type=click.Path(), help="External config file")
@auto_instantiate(ServerConfig)
def mixed_single(server: ServerConfig, dry_run: bool, config_file: str):
    """Mix model with raw Click options."""
    if config_file:
        click.echo(f"Loading additional config from: {config_file}")

    if dry_run:
        click.echo("DRY RUN MODE - not starting server")
    else:
        click.echo(f"Starting server at {server.host}:{server.port}")


# Example 2: Multiple models + additional Click options
@click.command()
@click.option("--environment", type=click.Choice(["dev", "staging", "prod"]), default="dev")
@click.option("--force", is_flag=True, help="Force deployment")
@multi_auto_instantiate(ServerConfig, DatabaseConfig)
def mixed_multi(server: ServerConfig, db: DatabaseConfig, environment: str, force: bool):
    """Mix multiple models with raw Click options."""
    click.echo(f"Deploying to {environment} environment")

    if force:
        click.echo("FORCE mode enabled")

    click.echo(f"Server: {server.host}:{server.port}")
    click.echo(f"Database: {db.url}")


# Example 3: What happens with name conflicts?
class ConfigWithExtraOptions(AutoWryModel):
    """Model that might conflict with raw options."""

    name: str = Field(description="Application name")
    version: str = Field(default="1.0.0", description="Version")
    # Note: 'force' would conflict with the Click option below


@click.command()
@click.option("--force", is_flag=True, help="Force update")  # Raw Click option
@click.option("--verbose", "-v", count=True, help="Verbosity level")  # Another raw option
@auto_instantiate(ConfigWithExtraOptions)
def potential_conflict(config: ConfigWithExtraOptions, force: bool, verbose: int):
    """Test potential naming conflicts."""
    click.echo(f"App: {config.name} v{config.version}")
    click.echo(f"Force: {force}")
    click.echo(f"Verbosity: {verbose}")


# Example 4: Complex scenario - models + Click args + options
@click.command()
@click.argument("action", type=click.Choice(["start", "stop", "restart"]))
@click.option("--timeout", type=int, default=30, help="Operation timeout")
@multi_auto_instantiate(ServerConfig, DatabaseConfig)
def complex_command(action: str, server: ServerConfig, db: DatabaseConfig, timeout: int):
    """Complex mix of arguments, options, and models."""
    click.echo(f"Action: {action} (timeout: {timeout}s)")
    click.echo(f"Server: {server.host}:{server.port}")
    click.echo(f"Database: {db.url}")


# Example 5: How would parameter naming work?
def demonstrate_parameter_resolution():
    """Show how parameters are resolved in different scenarios."""

    scenarios = """
    Current POC behavior:

    1. The decorator inspects function signature for type hints
    2. Parameters with model types get the instantiated models
    3. Other parameters get their values from Click kwargs

    Example function signature:
        def cmd(server: ServerConfig, db: DatabaseConfig, force: bool, verbose: int)

    The decorator:
        - Finds 'server: ServerConfig' → injects ServerConfig instance
        - Finds 'db: DatabaseConfig' → injects DatabaseConfig instance
        - 'force' and 'verbose' → passed through from Click kwargs

    Potential issues:

    1. Name conflicts: If a model has a field 'force' and there's also a
       Click option '--force', they would conflict in kwargs

    2. Parameter order: Currently relies on **kwargs which doesn't preserve
       order, but function parameters have order

    3. Missing parameters: What if the function expects a parameter that
       isn't in kwargs or models?
    """

    return scenarios


# Test the examples
if __name__ == "__main__":
    import sys

    from click.testing import CliRunner

    runner = CliRunner()

    if len(sys.argv) > 1:
        # Allow running specific commands
        import importlib.util

        spec = importlib.util.spec_from_file_location("module", __file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cmd_name = sys.argv[1]
        cmd = getattr(module, cmd_name, None)
        if cmd and hasattr(cmd, "callback"):
            cmd(sys.argv[2:])
    else:
        # Run all tests
        print("=== Single Model + Raw Options ===")
        result = runner.invoke(mixed_single, ["--host", "0.0.0.0", "--dry-run", "--config-file", "app.yaml"])
        print(result.output)

        print("\n=== Multiple Models + Raw Options ===")
        result = runner.invoke(
            mixed_multi,
            ["--environment", "prod", "--force", "--host", "api.example.com", "--url", "postgres://prod-db/app"],
        )
        print(result.output)

        print("\n=== Potential Conflicts ===")
        result = runner.invoke(potential_conflict, ["--name", "MyApp", "--force", "-vvv"])
        print(result.output)

        print("\n=== Complex Scenario ===")
        result = runner.invoke(complex_command, ["restart", "--timeout", "60", "--port", "9000", "--pool-size", "20"])
        print(result.output)

        print("\n=== Parameter Resolution Logic ===")
        print(demonstrate_parameter_resolution())
