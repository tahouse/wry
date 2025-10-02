"""Comprehensive example demonstrating source tracking with all input types.

This example shows how wry tracks configuration values from:
- DEFAULT: Model default values
- ENV: Environment variables
- JSON: Configuration files
- CLI: Command-line arguments

Run examples:
    # With defaults only
    python source_tracking_comprehensive.py

    # With environment variables
    export MYAPP_HOST=env-host.com
    export MYAPP_PORT=9000
    python source_tracking_comprehensive.py

    # With JSON config
    python source_tracking_comprehensive.py --config examples/config.json

    # With CLI arguments (highest priority)
    python source_tracking_comprehensive.py --host cli-host.com --port 8080 --debug

    # Mix all sources
    export MYAPP_TIMEOUT=60
    python source_tracking_comprehensive.py --config examples/config.json --port 3000
"""

from typing import ClassVar

import click
from pydantic import Field

from wry import AutoWryModel, ValueSource


class AppConfig(AutoWryModel):
    """Application configuration with source tracking."""

    # Set environment variable prefix (ClassVar, not a field)
    env_prefix: ClassVar[str] = "MYAPP_"

    # Field with default - can be overridden by ENV, JSON, or CLI
    host: str = Field(default="localhost", description="Server hostname")

    # Field with default - can be overridden by ENV, JSON, or CLI
    port: int = Field(default=8080, description="Server port")

    # Boolean field with default
    debug: bool = Field(default=False, description="Enable debug mode")

    # Field with default - can be overridden
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")

    # Field with default string
    log_level: str = Field(default="INFO", description="Logging level")


@click.command()
@AppConfig.generate_click_parameters()
@click.pass_context
def main(ctx, **kwargs):
    """Application with comprehensive source tracking demonstration.

    This example shows how wry tracks where each configuration value comes from.
    """
    # Use from_click_context for full source tracking
    config = AppConfig.from_click_context(ctx, **kwargs)

    # Display configuration
    click.echo("=" * 60)
    click.echo("Configuration Values and Sources")
    click.echo("=" * 60)
    click.echo()

    # Show each field's value and source
    fields = ["host", "port", "debug", "timeout", "log_level"]

    for field_name in fields:
        value = getattr(config, field_name)
        source = getattr(config.source, field_name)

        # Color code by source
        if source == ValueSource.CLI:
            source_str = click.style("CLI", fg="green", bold=True)
        elif source == ValueSource.JSON:
            source_str = click.style("JSON", fg="blue", bold=True)
        elif source == ValueSource.ENV:
            source_str = click.style("ENV", fg="yellow", bold=True)
        elif source == ValueSource.DEFAULT:
            source_str = click.style("DEFAULT", fg="white", dim=True)
        else:
            source_str = str(source.value)

        click.echo(f"  {field_name:12} = {str(value):20} [from {source_str}]")

    click.echo()
    click.echo("-" * 60)

    # Show source summary
    summary = config.get_sources_summary()
    click.echo("Source Summary:")
    click.echo()

    for source, field_names in summary.items():
        if field_names:
            click.echo(f"  {source.value.upper():8} : {', '.join(field_names)}")

    click.echo()
    click.echo("=" * 60)
    click.echo()

    # Show precedence order
    click.echo("Configuration Precedence (highest to lowest):")
    click.echo("  1. CLI arguments    (e.g., --host myhost.com)")
    click.echo("  2. Environment vars (e.g., export MYAPP_HOST=myhost.com)")
    click.echo("  3. Config file      (e.g., --config config.json)")
    click.echo("  4. Default values   (defined in the model)")
    click.echo()

    # Show available environment variables
    click.echo("Available Environment Variables:")
    click.echo(f"  MYAPP_HOST      - Override host (current: {config.host})")
    click.echo(f"  MYAPP_PORT      - Override port (current: {config.port})")
    click.echo(f"  MYAPP_DEBUG     - Override debug (current: {config.debug})")
    click.echo(f"  MYAPP_TIMEOUT   - Override timeout (current: {config.timeout})")
    click.echo(f"  MYAPP_LOG_LEVEL - Override log level (current: {config.log_level})")
    click.echo()
    click.echo("Run with --show-env-vars for formatted list")


if __name__ == "__main__":
    main()
