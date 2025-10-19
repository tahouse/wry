"""Test boolean on/off flag support."""

from typing import Annotated, Any, ClassVar

import click
import pytest
from click.testing import CliRunner
from pydantic import Field

from wry import AutoOption, AutoWryModel, WryModel


class TestBooleanOnOffFlags:
    """Test boolean on/off flag generation."""

    def test_default_on_off_pattern(self):
        """Test that boolean fields generate --option/--no-option by default."""

        class Config(AutoWryModel):
            debug: bool = Field(default=False, description="Enable debug mode")
            enabled: bool = Field(default=True, description="Enable feature")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            return config

        # Check generated options
        params_by_name = {p.name: p for p in cmd.params}

        assert "debug" in params_by_name
        debug_param = params_by_name["debug"]
        # Should be a flag
        assert debug_param.is_flag
        # Should have both on and off options
        assert "--debug" in debug_param.opts or any(
            "debug" in opt and "no-debug" in str(debug_param.opts) for opt in debug_param.opts
        )

        # Test CLI usage
        runner = CliRunner()

        # Test --debug sets to True
        result = runner.invoke(cmd, ["--debug"])
        assert result.exit_code == 0

        # Test --no-debug sets to False
        result = runner.invoke(cmd, ["--no-debug"])
        assert result.exit_code == 0

    def test_custom_off_option(self):
        """Test custom off-option name via AutoOption(flag_off_option=...)."""

        class Config(AutoWryModel):
            verbose: Annotated[bool, AutoOption(flag_off_option="quiet")] = Field(
                default=False, description="Verbose output"
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"Verbose: {config.verbose}")

        # Check that it has --verbose/--quiet
        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--verbose" in result.output
        assert "--quiet" in result.output

        # Test --verbose sets True
        result = runner.invoke(cmd, ["--verbose"])
        assert result.exit_code == 0
        assert "Verbose: True" in result.output

        # Test --quiet sets False
        result = runner.invoke(cmd, ["--quiet"])
        assert result.exit_code == 0
        assert "Verbose: False" in result.output

    def test_custom_off_prefix(self):
        """Test custom off-prefix via AutoOption(flag_off_prefix=...)."""

        class Config(AutoWryModel):
            enabled: Annotated[bool, AutoOption(flag_off_prefix="disable")] = Field(
                default=True, description="Enable feature"
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"Enabled: {config.enabled}")

        # Check that it has --enabled/--disable-enabled
        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--enabled" in result.output
        assert "--disable-enabled" in result.output

        # Test both flags
        result = runner.invoke(cmd, ["--enabled"])
        assert result.exit_code == 0
        assert "Enabled: True" in result.output

        result = runner.invoke(cmd, ["--disable-enabled"])
        assert result.exit_code == 0
        assert "Enabled: False" in result.output

    def test_model_wide_off_prefix(self):
        """Test model-wide wry_boolean_off_prefix ClassVar."""

        class Config(AutoWryModel):
            wry_boolean_off_prefix: ClassVar[str] = "disable"

            debug: bool = Field(default=False, description="Debug mode")
            enabled: bool = Field(default=True, description="Enable feature")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        # Check that all booleans use the custom prefix
        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--debug" in result.output
        assert "--disable-debug" in result.output
        assert "--enabled" in result.output
        assert "--disable-enabled" in result.output

    def test_opt_out_to_single_flag(self):
        """Test opting out to single flag via AutoOption(flag_enable_on_off=False)."""

        class Config(AutoWryModel):
            simple: Annotated[bool, AutoOption(flag_enable_on_off=False)] = Field(
                default=False, description="Simple flag"
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"Simple: {config.simple}")

        # Check that it only has --simple
        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--simple" in result.output
        assert "--no-simple" not in result.output

        # Test that --simple sets True
        result = runner.invoke(cmd, ["--simple"])
        assert result.exit_code == 0
        assert "Simple: True" in result.output

        # Test that without flag it's False
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Simple: False" in result.output

    def test_collision_detection(self):
        """Test collision detection when off-option conflicts with existing field."""

        class Config(AutoWryModel):
            debug: bool = Field(default=False, description="Debug mode")
            no_debug: str = Field(default="something", description="Unrelated field")

        # Should emit warning and fall back to single flag
        with pytest.warns(UserWarning, match="collides with existing field"):

            @click.command()
            @Config.generate_click_parameters()
            def cmd(**kwargs: Any):
                pass

        # Check that debug is a single flag (fallback)
        params_by_name = {p.name: p for p in cmd.params}
        assert "debug" in params_by_name
        assert params_by_name["debug"].is_flag

    def test_boolean_with_alias(self):
        """Test that boolean on/off uses alias name."""

        class Config(AutoWryModel):
            dbg: bool = Field(alias="debug", default=False, description="Debug mode")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"Debug: {config.dbg}")

        # Should use alias name for options
        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--debug" in result.output
        assert "--no-debug" in result.output

        # Test using alias
        result = runner.invoke(cmd, ["--debug"])
        assert result.exit_code == 0
        assert "Debug: True" in result.output

    def test_error_both_off_prefix_and_option(self):
        """Test that providing both flag_off_prefix and flag_off_option raises error."""

        with pytest.raises(ValueError, match="Provide only one"):
            AutoOption(flag_off_prefix="disable", flag_off_option="off")

    def test_error_off_options_with_disabled_on_off(self):
        """Test that providing off options when flag_enable_on_off=False raises error."""

        with pytest.raises(ValueError, match="Cannot specify.*when flag_enable_on_off=False"):
            AutoOption(flag_enable_on_off=False, flag_off_option="quiet")

        with pytest.raises(ValueError, match="Cannot specify.*when flag_enable_on_off=False"):
            AutoOption(flag_enable_on_off=False, flag_off_prefix="disable")

    def test_wry_model_with_on_off_flags(self):
        """Test that WryModel also supports on/off flags."""

        class Config(WryModel):
            debug: Annotated[bool, AutoOption()] = Field(default=False, description="Debug mode")
            verbose: Annotated[bool, AutoOption(flag_off_option="quiet")] = Field(
                default=False, description="Verbose output"
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"Debug: {config.debug}, Verbose: {config.verbose}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        # Check both patterns
        assert "--debug" in result.output
        assert "--no-debug" in result.output
        assert "--verbose" in result.output
        assert "--quiet" in result.output

    def test_source_tracking_with_on_off_flags(self):
        """Test that source tracking works correctly with on/off flags."""

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

        # Test CLI source
        result = runner.invoke(cmd, ["--debug"])
        assert result.exit_code == 0
        assert "Debug: True" in result.output
        assert "Source: cli" in result.output

        # Test no-option also tracked as CLI
        result = runner.invoke(cmd, ["--no-debug"])
        assert result.exit_code == 0
        assert "Debug: False" in result.output
        assert "Source: cli" in result.output

    def test_json_config_with_boolean_flags(self):
        """Test that JSON config works with boolean on/off flags."""
        import tempfile

        class Config(AutoWryModel):
            debug: bool = Field(default=False, description="Debug mode")
            enabled: bool = Field(default=True, description="Feature enabled")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Debug: {config.debug}, Enabled: {config.enabled}")

        runner = CliRunner()

        # Create temp JSON config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"debug": true, "enabled": false}')
            json_file = f.name

        try:
            result = runner.invoke(cmd, ["--config", json_file])
            assert result.exit_code == 0
            assert "Debug: True" in result.output
            assert "Enabled: False" in result.output
        finally:
            import os

            os.unlink(json_file)

    def test_required_boolean_with_on_off(self):
        """Test required boolean field with on/off pattern."""

        class Config(AutoWryModel):
            accept: Annotated[bool, AutoOption(required=True)] = Field(description="Accept terms")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"Accepted: {config.accept}")

        runner = CliRunner()

        # Should work with either flag
        result = runner.invoke(cmd, ["--accept"])
        assert result.exit_code == 0
        assert "Accepted: True" in result.output

        result = runner.invoke(cmd, ["--no-accept"])
        assert result.exit_code == 0
        assert "Accepted: False" in result.output
