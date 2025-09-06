"""Intermediate example showing manual field annotations and source tracking.

This example demonstrates:
- Using Annotated types with AutoOption for fine control
- Environment variable support with custom prefix
- JSON config file loading
- Detailed source tracking and constraint access
- Type validation with Pydantic
"""

from typing import Annotated

import click
from pydantic import Field

from wry import (
    AutoOption,
    WryModel,
    generate_click_parameters,
)


class AppConfig(WryModel):
    """Configuration using manual annotations for fine control."""

    # Set custom environment variable prefix
    env_prefix = "MYAPP_"

    # Explicit annotations give you full control
    name: Annotated[str, AutoOption] = Field(description="Your name")

    age: Annotated[int, AutoOption] = Field(default=25, ge=0, le=120, description="Your age in years")

    verbose: Annotated[bool, AutoOption] = Field(default=False, description="Enable verbose output")

    # Optional field with constraints
    score: Annotated[float | None, AutoOption] = Field(default=None, ge=0.0, le=100.0, description="Score percentage")


@click.command()
@generate_click_parameters(AppConfig)
@click.pass_context
def main(ctx: click.Context, **kwargs) -> None:
    """Example CLI showing intermediate wry features."""
    # Create config from Click context with FULL source tracking
    # Note: @click.pass_context decorator is required for accurate source information
    config = AppConfig.from_click_context(ctx, **kwargs)

    # Access values normally
    click.echo(f"Hello, {config.name}!")
    click.echo(f"You are {config.age} years old.")

    if config.verbose:
        click.echo("\nConfiguration sources:")
        # Show where each value came from
        click.echo(f"  name: {config.source.name.value}")
        click.echo(f"  age: {config.source.age.value}")
        click.echo(f"  verbose: {config.source.verbose.value}")
        if config.score is not None:
            click.echo(f"  score: {config.source.score.value}")

        # Show value ranges
        click.echo("\nField constraints:")
        click.echo(f"  age: {config.minimum.age} - {config.maximum.age}")
        if config.score is not None:
            click.echo(f"  score: {config.minimum.score} - {config.maximum.score}")

    if config.score is not None:
        click.echo(f"Your score: {config.score}%")


if __name__ == "__main__":
    # Try these different ways to provide configuration:
    #
    # 1. CLI arguments:
    #    python intermediate_example.py --name "John Doe" --age 30 --verbose
    #
    # 2. Environment variables (note custom prefix):
    #    MYAPP_NAME="Jane" MYAPP_AGE=25 python intermediate_example.py --verbose
    #
    # 3. JSON config file:
    #    python intermediate_example.py --config config.json
    #
    # 4. Mix sources (CLI overrides JSON/ENV):
    #    MYAPP_NAME="Default Name" python intermediate_example.py --config config.json --age 40
    #
    # 5. Show environment variables:
    #    python intermediate_example.py --show-env-vars
    main()
