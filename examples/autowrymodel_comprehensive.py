#!/usr/bin/env python3
"""Comprehensive AutoWryModel example - all features in one place.

AutoWryModel automatically generates Click options for all fields.
This example demonstrates:
- Simple fields with automatic option generation
- Field constraints (ge, le, min_length, max_length)
- Pydantic aliases for custom CLI option names (v0.3.2+)
- Explicit click.option() for advanced control (short flags, count)
- Field exclusion with AutoExclude
- Arguments with AutoArgument
- Boolean flags
- Environment variable support
- JSON config file support
"""

from datetime import datetime
from typing import Annotated, Any

import click
from pydantic import Field

from wry import AutoArgument, AutoExclude, AutoWryModel


class ComprehensiveConfig(AutoWryModel):
    """All AutoWryModel features in one model."""

    env_prefix = "APP_"

    # ============================================================================
    # ARGUMENTS - Positional parameters (required or with defaults)
    # ============================================================================

    input_file: Annotated[str, AutoArgument] = Field(
        description="Input file path to process (required positional argument)"
    )

    output_file: Annotated[str, AutoArgument] = Field(
        default="output.txt",
        description="Output file path (optional positional argument)",
    )

    # ============================================================================
    # SIMPLE OPTIONS - Automatically generated from field names
    # ============================================================================

    host: str = Field(
        default="localhost",
        description="Server host address",
    )

    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Server port number",
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # ============================================================================
    # CONSTRAINED FIELDS - Show constraints in help text
    # ============================================================================

    api_key: str = Field(
        default="",
        min_length=0,
        max_length=64,
        description="API key for authentication",
    )

    workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker processes",
    )

    timeout: float = Field(
        default=30.0,
        ge=0.1,
        le=300.0,
        description="Request timeout in seconds",
    )

    # ============================================================================
    # PYDANTIC ALIASES - Custom CLI option names (v0.3.2+)
    # Concise Python field names → Descriptive CLI options
    # No configuration needed - works automatically!
    # ============================================================================

    db_url: str = Field(
        alias="database_url",
        default="sqlite:///app.db",
        description="Database connection URL",
    )

    max_size: int = Field(
        alias="maximum_file_size",
        default=1024,
        ge=1,
        description="Maximum file size in KB",
    )

    use_cache: bool = Field(
        alias="enable_caching",
        default=True,
        description="Enable result caching",
    )

    # ============================================================================
    # EXPLICIT CLICK.OPTION - For advanced control
    # Use when you need: short flags, count behavior, custom Click types
    # ============================================================================

    verbose: Annotated[
        int,
        click.option(
            "-v",
            "--verbose",
            count=True,
            help="Increase verbosity (can be repeated: -vvv)",
        ),
    ] = Field(default=0)

    log_level: Annotated[
        str,
        click.option(
            "-l",
            "--log-level",
            type=click.Choice(["debug", "info", "warning", "error"]),
            help="Logging level",
        ),
    ] = Field(default="info")

    # ============================================================================
    # FIELD EXCLUSION - Internal fields not exposed to CLI
    # Use AutoExclude for: internal state, computed values, secrets
    # ============================================================================

    session_id: Annotated[str, AutoExclude] = Field(
        default="",
        description="Internal session ID (not a CLI option)",
    )

    last_processed: Annotated[datetime, AutoExclude] = Field(
        default_factory=datetime.now,
        description="Timestamp of last processing (internal)",
    )

    cache_dir: Annotated[str, AutoExclude] = Field(
        default="/tmp/cache",
        description="Internal cache directory",
    )


@click.command()
@ComprehensiveConfig.generate_click_parameters()
@click.pass_context
def main(ctx: click.Context, **kwargs: Any):
    """Comprehensive AutoWryModel example showing all features.

    This example demonstrates every major feature of AutoWryModel:
    - Positional arguments (input_file, output_file)
    - Simple options (host, port, debug)
    - Constrained fields (workers: 1-32, timeout: 0.1-300.0)
    - Pydantic aliases (--database-url from db_url field)
    - Explicit click.option (-v for verbose, -l for log-level)
    - Field exclusion (session_id, last_processed not in CLI)
    - Environment variables (APP_DATABASE_URL, APP_MAXIMUM_FILE_SIZE, etc.)
    - JSON config file support (--config)

    Examples:
        # Basic usage with required argument
        python examples/autowrymodel_comprehensive.py input.txt

        # All options
        python examples/autowrymodel_comprehensive.py input.txt output.txt \\
            --host 0.0.0.0 --port 3000 --debug \\
            --database-url postgres://localhost/db \\
            --maximum-file-size 2048 \\
            --workers 8 -vvv -l debug

        # Using alias-based options (note descriptive names)
        python examples/autowrymodel_comprehensive.py input.txt \\
            --database-url mysql://localhost/db \\
            --maximum-file-size 4096 \\
            --no-enable-caching

        # Environment variables (use alias names)
        export APP_DATABASE_URL=postgres://localhost/db
        export APP_MAXIMUM_FILE_SIZE=2048
        export APP_ENABLE_CACHING=false
        python examples/autowrymodel_comprehensive.py input.txt

        # JSON config (accepts both field names and aliases)
        python examples/autowrymodel_comprehensive.py input.txt --config config.json

        # Show all environment variables
        python examples/autowrymodel_comprehensive.py --show-env-vars
    """
    config = ComprehensiveConfig.from_click_context(ctx, **kwargs)

    click.echo("=" * 70)
    click.echo("COMPREHENSIVE AUTOWRYMODEL EXAMPLE")
    click.echo("=" * 70)

    click.echo("\n📁 Arguments (Positional):")
    click.echo(f"  Input File:  {config.input_file}")
    click.echo(f"  Output File: {config.output_file}")

    click.echo("\n🔧 Simple Options:")
    click.echo(f"  Host:    {config.host}")
    click.echo(f"  Port:    {config.port}")
    click.echo(f"  Debug:   {config.debug}")
    click.echo(f"  Workers: {config.workers}")
    click.echo(f"  Timeout: {config.timeout}s")

    click.echo("\n🏷️  Pydantic Aliases (concise Python → descriptive CLI):")
    click.echo(f"  Database URL:    {config.db_url}")
    click.echo(f"  Max File Size:   {config.max_size} KB")
    click.echo(f"  Caching:         {'enabled' if config.use_cache else 'disabled'}")

    click.echo("\n⚙️  Explicit Click Options (custom behavior):")
    click.echo(f"  Verbosity:   {config.verbose}")
    click.echo(f"  Log Level:   {config.log_level}")

    click.echo("\n🚫 Excluded Fields (internal, not in CLI):")
    click.echo(f"  Session ID:      {config.session_id or '(not set)'}")
    click.echo(f"  Last Processed:  {config.last_processed}")
    click.echo(f"  Cache Dir:       {config.cache_dir}")

    click.echo("\n📊 Configuration Sources:")
    sources_summary = config.get_sources_summary()
    for source, fields in sources_summary.items():
        if fields:
            click.echo(f"  {source.value.upper():8s} → {', '.join(fields)}")

    click.echo("\n✅ Configuration loaded successfully!")


if __name__ == "__main__":
    main()
