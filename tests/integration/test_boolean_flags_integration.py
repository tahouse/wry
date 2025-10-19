"""Integration tests for boolean on/off flags."""

import os
import tempfile
from typing import Annotated, Any, ClassVar

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoOption, AutoWryModel


class TestBooleanFlagsIntegration:
    """End-to-end tests for boolean on/off flags."""

    def test_cli_precedence_over_json(self):
        """Test that CLI flags override JSON config."""

        class Config(AutoWryModel):
            debug: bool = Field(default=False, description="Debug mode")
            verbose: bool = Field(default=False, description="Verbose output")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Debug: {config.debug} (source: {config.source.debug.value})")
            click.echo(f"Verbose: {config.verbose} (source: {config.source.verbose.value})")

        runner = CliRunner()

        # Create JSON config with values
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"debug": true, "verbose": true}')
            json_file = f.name

        try:
            # CLI should override JSON
            result = runner.invoke(cmd, ["--config", json_file, "--no-debug", "--no-verbose"])
            assert result.exit_code == 0
            assert "Debug: False (source: cli)" in result.output
            assert "Verbose: False (source: cli)" in result.output
        finally:
            os.unlink(json_file)

    def test_environment_variables_with_on_off_flags(self):
        """Test that environment variables work with on/off flags."""

        class Config(AutoWryModel):
            wry_env_prefix: ClassVar[str] = "TEST_"
            debug: bool = Field(default=False, description="Debug mode")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Debug: {config.debug}")
            click.echo(f"Source: {config.source.debug.value}")

        runner = CliRunner()

        # Test with env var
        result = runner.invoke(cmd, [], env={"TEST_DEBUG": "true"})
        assert result.exit_code == 0
        assert "Debug: True" in result.output
        assert "Source: env" in result.output

        # CLI should override env
        result = runner.invoke(cmd, ["--no-debug"], env={"TEST_DEBUG": "true"})
        assert result.exit_code == 0
        assert "Debug: False" in result.output
        assert "Source: cli" in result.output

    def test_all_sources_with_boolean(self):
        """Test DEFAULT < ENV < JSON < CLI precedence for boolean fields."""

        class Config(AutoWryModel):
            wry_env_prefix: ClassVar[str] = "TEST_"
            debug: bool = Field(default=False, description="Debug mode")
            trace: bool = Field(default=False, description="Trace")
            log: bool = Field(default=False, description="Log")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Debug: {config.debug} ({config.source.debug.value})")
            click.echo(f"Trace: {config.trace} ({config.source.trace.value})")
            click.echo(f"Log: {config.log} ({config.source.log.value})")

        runner = CliRunner()

        # Create JSON config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"trace": true}')  # Only trace in JSON
            json_file = f.name

        try:
            # Test precedence:
            # - debug: DEFAULT (false) - not in JSON, ENV, or CLI
            # - trace: JSON (true) - JSON wins (no ENV or CLI override)
            # - log: CLI (true) - CLI wins over all
            result = runner.invoke(cmd, ["--config", json_file, "--log"])
            assert result.exit_code == 0
            assert "Debug: False (default)" in result.output  # Uses default from model
            assert "Trace: True (json)" in result.output  # JSON wins
            assert "Log: True (cli)" in result.output  # CLI wins
        finally:
            os.unlink(json_file)

    def test_mixed_on_off_and_single_flags(self):
        """Test mixing on/off flags and single flags in same model."""

        class Config(AutoWryModel):
            on_off_flag: bool = Field(default=False, description="Uses on/off pattern")
            single_flag: Annotated[bool, AutoOption(flag_enable_on_off=False)] = Field(
                default=False, description="Uses single flag"
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"OnOff: {config.on_off_flag}, Single: {config.single_flag}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        # Check patterns
        assert "--on-off-flag" in result.output
        assert "--no-on-off-flag" in result.output
        assert "--single-flag" in result.output
        # Single flag shouldn't have no-option
        help_lines = result.output.split("\n")
        single_flag_line = [line for line in help_lines if "--single-flag" in line]
        if single_flag_line:
            # Make sure there's no --no-single-flag on the same line
            assert "--no-single-flag" not in single_flag_line[0]

    def test_custom_off_option_overrides_model_prefix(self):
        """Test that per-field flag_off_option overrides model-wide prefix."""

        class Config(AutoWryModel):
            wry_boolean_off_prefix: ClassVar[str] = "disable"

            # Uses model-wide prefix
            debug: bool = Field(default=False, description="Debug")

            # Overrides with custom off-option
            verbose: Annotated[bool, AutoOption(flag_off_option="quiet")] = Field(default=False, description="Verbose")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        # debug uses model-wide prefix
        assert "--debug" in result.output
        assert "--disable-debug" in result.output

        # verbose uses custom off-option
        assert "--verbose" in result.output
        assert "--quiet" in result.output
        assert "--no-verbose" not in result.output  # Shouldn't use default
        assert "--disable-verbose" not in result.output  # Shouldn't use model-wide
