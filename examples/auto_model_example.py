#!/usr/bin/env python3
"""Example showing AutoWryModel - automatic Click option generation."""

from typing import Annotated

import click
from pydantic import Field

from wry import AutoOption, WryModel
from wry.auto_model import AutoWryModel, create_auto_model
from wry.click_integration import AutoClickParameter


# Traditional way - need to annotate every field
class TraditionalConfig(WryModel):
    """Traditional approach - explicit annotations needed."""

    host: Annotated[str, AutoOption] = Field(default="localhost", description="Server host")
    port: Annotated[int, AutoOption] = Field(default=8080, description="Server port", ge=1, le=65535)
    debug: Annotated[bool, AutoOption] = Field(default=False, description="Enable debug mode")
    workers: Annotated[int, AutoOption] = Field(default=4, description="Number of workers", ge=1)
    timeout: Annotated[float, AutoOption] = Field(default=30.0, description="Request timeout in seconds")


# New way - AutoWryModel generates options automatically!
class AutoConfig(AutoWryModel):
    """Auto approach - all fields become options automatically."""

    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port", ge=1, le=65535)
    debug: bool = Field(default=False, description="Enable debug mode")
    workers: int = Field(default=4, description="Number of workers", ge=1)
    timeout: float = Field(default=30.0, description="Request timeout in seconds")


# Mixed approach - auto with overrides
class MixedConfig(AutoWryModel):
    """Mixed approach - auto generation with selective overrides."""

    # These become options automatically
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port")

    # Override to make this an argument instead of option
    config_file: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Configuration file path")

    # Use a custom Click decorator
    verbose: Annotated[int, click.option("-v", "--verbose", count=True, help="Increase verbosity")] = Field(default=0)

    # This still becomes an auto option
    workers: int = Field(default=4, description="Number of workers")


# Dynamic model creation
DynamicConfig = create_auto_model(
    "DynamicConfig",
    {
        "api_key": Field(description="API key for authentication"),
        "endpoint": Field(default="https://api.example.com", description="API endpoint"),
        "retry_count": Field(default=3, description="Number of retries", ge=0, le=10),
        "verify_ssl": Field(default=True, description="Verify SSL certificates"),
    },
)


# Commands demonstrating each approach
@click.group()
def cli():
    """Examples of AutoWryModel usage."""
    pass


@cli.command("traditional")
@TraditionalConfig.generate_click_parameters()
@click.pass_context
def traditional_cmd(ctx, **kwargs):
    """Traditional approach with explicit annotations."""
    config = TraditionalConfig.from_click_context(ctx, **kwargs)
    click.echo("Traditional Config:")
    click.echo(f"  Host: {config.host}:{config.port}")
    click.echo(f"  Debug: {config.debug}")
    click.echo(f"  Workers: {config.workers}")


@cli.command("auto")
@AutoConfig.generate_click_parameters()
@click.pass_context
def auto_cmd(ctx, **kwargs):
    """Auto approach - much cleaner!"""
    config = AutoConfig.from_click_context(ctx, **kwargs)
    click.echo("Auto Config (same result, less code!):")
    click.echo(f"  Host: {config.host}:{config.port}")
    click.echo(f"  Debug: {config.debug}")
    click.echo(f"  Workers: {config.workers}")

    # Source tracking still works
    click.echo(f"  Host source: {config.source.host.value}")


@cli.command("mixed")
@MixedConfig.generate_click_parameters()
@click.pass_context
def mixed_cmd(ctx, **kwargs):
    """Mixed approach with overrides."""
    config = MixedConfig.from_click_context(ctx, **kwargs)
    click.echo("Mixed Config:")
    click.echo(f"  Config file: {config.config_file}")
    click.echo(f"  Host: {config.host}:{config.port}")
    click.echo(f"  Verbosity: {config.verbose}")
    click.echo(f"  Workers: {config.workers}")


@cli.command("dynamic")
@DynamicConfig.generate_click_parameters()
@click.pass_context
def dynamic_cmd(ctx, **kwargs):
    """Dynamic model creation."""
    config = DynamicConfig.from_click_context(ctx, **kwargs)
    click.echo("Dynamic Config:")
    click.echo(f"  API Key: {'***' if config.api_key else 'Not set'}")
    click.echo(f"  Endpoint: {config.endpoint}")
    click.echo(f"  Retries: {config.retry_count}")
    click.echo(f"  SSL Verify: {config.verify_ssl}")


@cli.command("help-comparison")
def help_comparison():
    """Show the difference in code."""
    traditional_lines = """
    # Traditional approach - verbose
    class TraditionalConfig(WryModel):
        host: Annotated[str, AutoOption] = Field(default="localhost")
        port: Annotated[int, AutoOption] = Field(default=8080)
        debug: Annotated[bool, AutoOption] = Field(default=False)
        # ... need Annotated[T, AutoOption] for every field
    """

    auto_lines = """
    # Auto approach - clean and simple
    class AutoConfig(AutoWryModel):
        host: str = Field(default="localhost")
        port: int = Field(default=8080)
        debug: bool = Field(default=False)
        # ... just define fields normally!
    """

    click.echo("Traditional approach requires explicit annotations:")
    click.echo(traditional_lines)
    click.echo("\nAuto approach is much cleaner:")
    click.echo(auto_lines)
    click.echo("\n✨ AutoWryModel automatically generates Click options for all fields!")


if __name__ == "__main__":
    import sys

    # If no arguments provided, run the demo
    if len(sys.argv) == 1:
        # Test the commands
        from click.testing import CliRunner

        runner = CliRunner()

        print("=== Traditional vs Auto Comparison ===\n")

        # Show help for traditional
        result = runner.invoke(traditional_cmd, ["--help"])
        print("Traditional command help:")
        print(result.output)

        # Show help for auto (should be identical!)
        result = runner.invoke(auto_cmd, ["--help"])
        print("\nAuto command help (same options, less code!):")
        print(result.output)

        # Test mixed approach
        print("\n=== Mixed Approach Test ===")
        result = runner.invoke(mixed_cmd, ["config.yaml", "-vvv", "--workers", "8"])
        print(result.output)

        # Test dynamic
        print("\n=== Dynamic Model Test ===")
        result = runner.invoke(dynamic_cmd, ["--api-key", "secret", "--retry-count", "5"])
        print(result.output)
    else:
        # Run the CLI normally
        cli()
