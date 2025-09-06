#!/usr/bin/env python3
"""The simplest wry example - automatic CLI from a Pydantic model."""

import click
from pydantic import Field

from wry import AutoWryModel, generate_click_parameters


class AppConfig(AutoWryModel):
    """Configuration for our application."""

    # AutoWryModel automatically generates CLI options for all fields
    name: str = Field(description="Your name")
    age: int = Field(default=25, ge=0, le=120, description="Your age")
    verbose: bool = Field(default=False, description="Enable verbose output")


@click.command()
@generate_click_parameters(AppConfig)
def main(**kwargs):
    """A simple greeting application."""
    # Direct instantiation - simple but no accurate source tracking
    config = AppConfig(**kwargs)

    click.echo(f"Hello, {config.name}! You are {config.age} years old.")

    if config.verbose:
        click.echo("\nConfiguration sources (limited accuracy without context):")
        click.echo(f"  name came from: {config.source.name}")
        click.echo(f"  age came from: {config.source.age}")
        click.echo("\nNote: For accurate source tracking, see intermediate_example.py")


if __name__ == "__main__":
    # Try these commands:
    # python simple_cli.py --name Alice --age 30
    # python simple_cli.py --name Bob --verbose
    # python simple_cli.py --help
    main()
