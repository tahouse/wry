#!/usr/bin/env python3
"""Example demonstrating automatic argument help injection into docstrings.

Since Click doesn't show help text for arguments (they're positional),
wry automatically injects argument descriptions from your Pydantic model
into the command's docstring.
"""

from typing import Annotated

import click
from pydantic import Field

from wry import AutoClickParameter, AutoWryModel


class DeployConfig(AutoWryModel):
    """Configuration for deployment command."""

    environment: Annotated[
        str,
        AutoClickParameter.ARGUMENT,
    ] = Field(description="Target environment (dev, staging, prod)")

    version: Annotated[
        str,
        AutoClickParameter.ARGUMENT,
    ] = Field(description="Version to deploy")

    force: bool = Field(default=False, description="Force deployment even if checks fail")
    dry_run: bool = Field(default=False, description="Show what would be deployed without deploying")


@click.command()
@DeployConfig.generate_click_parameters()
def deploy(**kwargs):
    """Deploy the application to a specific environment.

    This command handles deployment with proper validation and safety checks.
    """
    config = DeployConfig(**kwargs)

    click.echo(f"Deploying version {config.version} to {config.environment}")
    click.echo(f"Force: {config.force}")
    click.echo(f"Dry run: {config.dry_run}")


if __name__ == "__main__":
    # Try: python examples/argument_help_injection.py --help
    # You'll see the argument descriptions in the help text!
    deploy()
