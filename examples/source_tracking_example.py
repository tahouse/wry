#!/usr/bin/env python3
"""Example demonstrating the different approaches to source tracking in wry."""

import os
from typing import Annotated

import click
from pydantic import Field

from wry import AutoOption, WryModel, generate_click_parameters


class Args(WryModel):
    """Arguments with source tracking demonstration."""

    name: Annotated[str, AutoOption] = Field(default="default-name", description="Your name")
    debug: Annotated[bool, AutoOption] = Field(default=False, description="Debug mode")
    port: Annotated[int, AutoOption] = Field(default=8080, ge=1, le=65535, description="Port number")

    # Custom env prefix
    env_prefix = "MYAPP_"


@click.group()
def cli():
    """Demonstrates different source tracking approaches."""
    pass


@cli.command()
@generate_click_parameters(Args)
def without_context(**kwargs):
    """Command WITHOUT @click.pass_context - no source tracking."""
    click.echo("=== WITHOUT @click.pass_context ===\n")

    # Direct instantiation (no source tracking)
    config = Args(**kwargs)
    click.echo("Direct instantiation - Args(**kwargs):")
    click.echo(f"   Values: name={config.name}, debug={config.debug}, port={config.port}")
    click.echo(f"   Sources: name={config.source.name}, debug={config.source.debug}, port={config.source.port}")
    click.echo("   ⚠️  All sources show as CLI regardless of actual source\n")

    # Note: from_click_context() requires context - will raise error without it
    try:
        _ = Args.from_click_context(**kwargs)
    except RuntimeError as e:
        click.echo("Trying Args.from_click_context(**kwargs) without context:")
        click.echo(f"   ❌ Error: {e}\n")


@cli.command()
@generate_click_parameters(Args)
@click.pass_context
def with_context(ctx, **kwargs):
    """Command WITH @click.pass_context - full source tracking."""
    click.echo("=== WITH @click.pass_context ===\n")

    # Full source tracking with context
    config = Args.from_click_context(ctx, **kwargs)
    click.echo("Full tracking - Args.from_click_context(ctx, **kwargs):")
    click.echo(f"   Values: name={config.name}, debug={config.debug}, port={config.port}")
    click.echo(f"   Sources: name={config.source.name}, debug={config.source.debug}, port={config.source.port}")
    click.echo("   ✓ Accurately tracks CLI, ENV, and DEFAULT sources\n")

    # Show source summary
    summary = config.get_sources_summary()
    click.echo("Source summary:")
    for source, fields in summary.items():
        if fields:
            click.echo(f"   {source}: {', '.join(fields)}")


@cli.command()
def show_examples():
    """Show example commands to demonstrate source tracking."""
    click.echo("Try these examples to see source tracking in action:\n")
    click.echo("1. Set an environment variable:")
    click.echo("   export MYAPP_NAME=EnvUser")
    click.echo("   python source_tracking_example.py without-context")
    click.echo("   python source_tracking_example.py with-context\n")

    click.echo("2. Mix CLI and environment:")
    click.echo("   export MYAPP_PORT=9000")
    click.echo("   python source_tracking_example.py without-context --name CliUser")
    click.echo("   python source_tracking_example.py with-context --name CliUser\n")

    click.echo("3. Use all defaults:")
    click.echo("   unset MYAPP_NAME MYAPP_PORT")
    click.echo("   python source_tracking_example.py without-context")
    click.echo("   python source_tracking_example.py with-context")


if __name__ == "__main__":
    # Show current environment for clarity
    env_vars = {k: v for k, v in os.environ.items() if k.startswith("MYAPP_")}
    if env_vars:
        click.echo("Current environment variables:")
        for k, v in env_vars.items():
            click.echo(f"  {k}={v}")
        click.echo()

    cli()
