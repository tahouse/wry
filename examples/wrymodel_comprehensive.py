#!/usr/bin/env python3
"""Comprehensive WryModel example - manual control with full source tracking.

WryModel requires manual annotation of fields with AutoOption/AutoArgument.
This gives you complete control over which fields become CLI parameters.

This example demonstrates:
- Manual field annotation with AutoOption and AutoArgument
- Full source tracking (CLI/ENV/JSON/DEFAULT)
- Configuration precedence: CLI > JSON > ENV > DEFAULT
- from_click_context() for source tracking
- get_sources_summary() for debugging
- Mixed arguments and options
- Environment variable support with custom prefix
"""

from typing import Annotated, Any

import click
from pydantic import Field

from wry import AutoArgument, AutoOption, ValueSource, WryModel


class ServerConfig(WryModel):
    """Server configuration with manual field control and source tracking."""

    env_prefix = "SERVER_"

    # ============================================================================
    # ARGUMENTS - Must explicitly annotate with AutoArgument
    # ============================================================================

    config_file: Annotated[str, AutoArgument] = Field(
        description="Configuration file path (required positional argument)"
    )

    # ============================================================================
    # OPTIONS - Must explicitly annotate with AutoOption
    # ============================================================================

    host: Annotated[str, AutoOption] = Field(
        default="localhost",
        description="Server host address",
    )

    port: Annotated[int, AutoOption] = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Server port number",
    )

    debug: Annotated[bool, AutoOption] = Field(
        default=False,
        description="Enable debug mode",
    )

    workers: Annotated[int, AutoOption] = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker processes",
    )

    # ============================================================================
    # PYDANTIC ALIASES - Work with WryModel too! (v0.3.2+)
    # Concise Python field names → Descriptive CLI options
    # ============================================================================

    db_url: Annotated[str, AutoOption] = Field(
        alias="database_url",
        default="sqlite:///app.db",
        description="Database connection URL",
    )

    max_conns: Annotated[int, AutoOption] = Field(
        alias="maximum_connections",
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of connections",
    )

    # ============================================================================
    # FIELDS WITHOUT ANNOTATION - Not exposed to CLI
    # With WryModel, fields without AutoOption/AutoArgument are automatically excluded
    # ============================================================================

    internal_state: str = Field(
        default="",
        description="Internal state (not a CLI option)",
    )

    computed_value: int = Field(
        default=0,
        description="Computed value (not a CLI option)",
    )


@click.command()
@ServerConfig.generate_click_parameters()
@click.pass_context
def main(ctx: click.Context, **kwargs: Any):
    """Comprehensive WryModel example with full source tracking.

    WryModel gives you manual control - only fields annotated with
    AutoOption or AutoArgument become CLI parameters.

    Key differences from AutoWryModel:
    - Must explicitly annotate each field with AutoOption/AutoArgument
    - Fields without annotations are automatically excluded from CLI
    - Full source tracking with from_click_context()
    - See where each value came from: CLI, ENV, JSON, or DEFAULT

    Configuration precedence: CLI > JSON > ENV > DEFAULT

    Examples:
        # Basic usage
        python examples/wrymodel_comprehensive.py config.yaml

        # Override with CLI options (including alias-based options)
        python examples/wrymodel_comprehensive.py config.yaml \\
            --host 0.0.0.0 --port 3000 --debug --workers 8 \\
            --database-url postgres://localhost/db --maximum-connections 200

        # Environment variables (use alias names for aliased fields)
        export SERVER_HOST=0.0.0.0
        export SERVER_PORT=3000
        export SERVER_DEBUG=true
        export SERVER_DATABASE_URL=postgres://localhost/db
        export SERVER_MAXIMUM_CONNECTIONS=200
        python examples/wrymodel_comprehensive.py config.yaml

        # JSON config (lower precedence than ENV)
        python examples/wrymodel_comprehensive.py config.yaml \\
            --config server.json

        # CLI overrides everything
        export SERVER_PORT=3000
        python examples/wrymodel_comprehensive.py config.yaml \\
            --config server.json --port 8080
        # Result: port=8080 (CLI wins)

        # Show environment variables
        python examples/wrymodel_comprehensive.py --show-env-vars
    """
    # Use from_click_context() for full source tracking
    config = ServerConfig.from_click_context(ctx, **kwargs)

    click.echo("=" * 70)
    click.echo("COMPREHENSIVE WRYMODEL EXAMPLE - Source Tracking")
    click.echo("=" * 70)

    click.echo("\n📁 Argument:")
    click.echo(f"  Config File: {config.config_file}")
    click.echo(f"    Source: {config.source.config_file.value}")

    click.echo("\n🔧 Options with Source Tracking:")
    click.echo(f"  Host:    {config.host:20s} (from: {config.source.host.value})")
    click.echo(f"  Port:    {config.port:<20d} (from: {config.source.port.value})")
    click.echo(f"  Debug:   {str(config.debug):20s} (from: {config.source.debug.value})")
    click.echo(f"  Workers: {config.workers:<20d} (from: {config.source.workers.value})")

    click.echo("\n🏷️  Pydantic Aliases (work with WryModel too!):")
    click.echo(f"  Database URL:    {config.db_url:30s} (from: {config.source.db_url.value})")
    click.echo(f"  Max Connections: {config.max_conns:<30d} (from: {config.source.max_conns.value})")

    click.echo("\n🚫 Non-CLI Fields (no AutoOption annotation):")
    click.echo(f"  Internal State:  {config.internal_state or '(empty)'}")
    click.echo(f"  Computed Value:  {config.computed_value}")

    click.echo("\n📊 Configuration Sources Summary:")
    click.echo("  (Shows which source was used for each field)")
    click.echo()

    sources_summary = config.get_sources_summary()
    for source in [ValueSource.CLI, ValueSource.JSON, ValueSource.ENV, ValueSource.DEFAULT]:
        fields = sources_summary.get(source, [])
        if fields:
            click.echo(f"  {source.value.upper():8s} → {', '.join(fields)}")

    click.echo("\n📈 Configuration Precedence:")
    click.echo("  CLI > JSON > ENV > DEFAULT")
    click.echo()
    click.echo("  This means:")
    click.echo("  - CLI arguments override everything")
    click.echo("  - JSON config overrides ENV and DEFAULT")
    click.echo("  - ENV variables override DEFAULT")
    click.echo("  - DEFAULT is used if nothing else is set")

    click.echo("\n💡 Why use WryModel?")
    click.echo("  - Explicit control over which fields are CLI parameters")
    click.echo("  - Full source tracking (know where each value came from)")
    click.echo("  - Perfect for debugging configuration issues")
    click.echo("  - Fields without AutoOption/AutoArgument are auto-excluded")

    click.echo("\n✅ Configuration loaded successfully!")


if __name__ == "__main__":
    main()
