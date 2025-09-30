#!/usr/bin/env python3
"""Example demonstrating field exclusion with AutoClickParameter.EXCLUDE."""

from typing import Annotated

import click
from pydantic import Field, field_validator

from wry import AutoClickParameter, AutoWryModel


class AppConfig(AutoWryModel):
    """Application configuration with excluded fields."""

    # Regular CLI options
    name: str = Field(default="MyApp", description="Application name")
    port: int = Field(default=8080, description="Server port", ge=1, le=65535)
    debug: bool = Field(default=False, description="Enable debug mode")

    # Polymorphic input field - user provides a role string
    role_input: str = Field(default="user", description="User role (admin/user/guest)")

    # Computed/internal fields - excluded from CLI
    is_admin: Annotated[bool, AutoClickParameter.EXCLUDE] = False
    permissions: Annotated[list[str], AutoClickParameter.EXCLUDE] = Field(default_factory=list)
    internal_id: Annotated[str, AutoClickParameter.EXCLUDE] = Field(default="", description="Internal use only")

    @field_validator("role_input")
    def validate_role(cls, v):
        """Validate and normalize role input."""
        valid_roles = {"admin", "user", "guest"}
        if v.lower() not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return v.lower()

    def model_post_init(self, __context) -> None:
        """Post-initialization to compute derived fields."""
        # Set computed fields based on role
        if self.role_input == "admin":
            self.is_admin = True
            self.permissions = ["read", "write", "delete", "manage_users"]
        elif self.role_input == "user":
            self.is_admin = False
            self.permissions = ["read", "write"]
        else:  # guest
            self.is_admin = False
            self.permissions = ["read"]

        # Generate internal ID
        self.internal_id = f"{self.name.lower().replace(' ', '-')}-{self.port}"


@click.command()
@AppConfig.generate_click_parameters()
@click.pass_context
def main(ctx, **kwargs):
    """Example application with field exclusion."""
    # Create config with source tracking
    config = AppConfig.from_click_context(ctx, **kwargs)

    click.echo(f"🚀 Starting {config.name} on port {config.port}")
    click.echo(f"Debug mode: {'ON' if config.debug else 'OFF'}")
    click.echo(f"Role: {config.role_input} (Admin: {config.is_admin})")
    click.echo(f"Permissions: {', '.join(config.permissions)}")
    click.echo(f"Internal ID: {config.internal_id}")

    # Show value sources
    click.echo("\nValue sources:")
    click.echo(f"- name: {config.source.name}")
    click.echo(f"- port: {config.source.port}")
    click.echo(f"- debug: {config.source.debug}")
    click.echo(f"- role_input: {config.source.role_input}")
    click.echo(f"- is_admin: {config.source.is_admin} (computed)")
    click.echo(f"- permissions: {config.source.permissions} (computed)")


if __name__ == "__main__":
    # Example usage:
    # python examples/field_exclusion.py --name "My Service" --port 3000 --role-input admin
    # python examples/field_exclusion.py --debug --role-input guest
    # python examples/field_exclusion.py --help
    main()
