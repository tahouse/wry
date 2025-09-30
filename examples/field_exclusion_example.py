#!/usr/bin/env python3
"""Example showing different ways to exclude fields from Click parameter generation."""

from typing import Annotated

import click
from pydantic import Field

from wry import AutoClickParameter, AutoWryModel


class ConfigWithExclusions(AutoWryModel):
    """Example showing different field exclusion patterns."""

    # Method 1: Don't use Annotated - field won't be a Click option
    polymorphic_input: str = "raw_input"

    # Method 2: Use Annotated for Click options
    name: Annotated[str, AutoClickParameter.OPTION] = "default"
    count: Annotated[int, AutoClickParameter.OPTION] = 0

    # Method 3: Internal/computed fields (no Annotated)
    computed_result: str = Field(default="", description="Computed from polymorphic_input")
    internal_state: dict = Field(default_factory=dict)

    def model_post_init(self, __context) -> None:
        """Post-initialization to handle polymorphic validation."""
        # Validate polymorphic_input into computed_result
        if self.polymorphic_input == "admin":
            self.computed_result = "administrator"
        elif self.polymorphic_input == "user":
            self.computed_result = "regular_user"
        else:
            self.computed_result = "unknown_role"


@click.command()
@ConfigWithExclusions.generate_click_parameters()
@click.pass_context
def main(ctx, **kwargs):
    """Example CLI with field exclusions."""
    config = ConfigWithExclusions.from_click_context(ctx, **kwargs)

    click.echo(f"Name: {config.name}")
    click.echo(f"Count: {config.count}")
    click.echo(f"Polymorphic input: {config.polymorphic_input}")
    click.echo(f"Computed result: {config.computed_result}")
    click.echo(f"Internal state: {config.internal_state}")


if __name__ == "__main__":
    main()
