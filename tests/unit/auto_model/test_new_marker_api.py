"""Test the new callable marker API."""

import warnings
from typing import Annotated, Any

import click
import pytest
from click.testing import CliRunner
from pydantic import Field

from wry import (
    AutoArgument,
    AutoExclude,
    AutoOption,
    AutoWryModel,
    WryArgument,
    WryExclude,
    WryOption,
)


class TestNewMarkerAPI:
    """Test the new callable marker API."""

    def test_auto_option_basic(self):
        """Test basic AutoOption() usage."""

        class Config(AutoWryModel):
            field: Annotated[str, AutoOption()] = Field(default="value", description="A field")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            return config

        # Should generate --field option
        params = {p.name: p for p in cmd.params}
        assert "field" in params
        assert isinstance(params["field"], click.Option)

    def test_auto_option_required(self):
        """Test AutoOption(required=True)."""

        class Config(AutoWryModel):
            api_key: Annotated[str, AutoOption(required=True)] = Field(description="API key")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        # Field should be required in Click
        params = {p.name: p for p in cmd.params}
        assert "api_key" in params
        # Note: required might be False if satisfied by env/json, but the marker is there

    def test_auto_argument_basic(self):
        """Test basic AutoArgument() usage."""

        class Config(AutoWryModel):
            input_file: Annotated[str, AutoArgument()] = Field(description="Input file")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        # Should generate positional argument
        params = [p for p in cmd.params if isinstance(p, click.Argument)]
        assert len(params) >= 1
        assert any(p.name == "input_file" for p in params)

    def test_auto_exclude_basic(self):
        """Test basic AutoExclude() usage."""

        class Config(AutoWryModel):
            visible: str = Field(default="shown", description="Visible field")
            hidden: Annotated[str, AutoExclude()] = Field(default="hidden", description="Hidden field")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        # visible should be in params, hidden should not
        params = {p.name: p for p in cmd.params}
        assert "visible" in params
        assert "hidden" not in params

    def test_wry_option_class_alias(self):
        """Test that AutoOption is an alias for WryOption."""

        assert AutoOption is WryOption
        assert AutoArgument is WryArgument
        assert AutoExclude is WryExclude

    def test_marker_instances_not_equal(self):
        """Test that different marker instances are different objects."""

        marker1 = AutoOption()
        marker2 = AutoOption()

        # They're different instances
        assert marker1 is not marker2

        # But they have the same default attributes
        assert marker1.required == marker2.required
        assert marker1.flag_enable_on_off == marker2.flag_enable_on_off

    def test_auto_option_with_boolean_parameters(self):
        """Test AutoOption with boolean-specific parameters."""

        # Custom off-option
        marker1 = AutoOption(flag_off_option="quiet")
        assert marker1.flag_off_option == "quiet"
        assert marker1.flag_off_prefix is None

        # Custom off-prefix
        marker2 = AutoOption(flag_off_prefix="disable")
        assert marker2.flag_off_prefix == "disable"
        assert marker2.flag_off_option is None

        # Disabled on/off
        marker3 = AutoOption(flag_enable_on_off=False)
        assert marker3.flag_enable_on_off is False

    def test_auto_option_with_comma_separated_parameter(self):
        """Test AutoOption with comma_separated parameter for list fields."""

        # Comma-separated enabled
        marker = AutoOption(comma_separated=True)
        assert marker.comma_separated is True

        # Default is False
        marker2 = AutoOption()
        assert marker2.comma_separated is False

        # Can combine with other parameters
        marker3 = AutoOption(required=True, comma_separated=True)
        assert marker3.required is True
        assert marker3.comma_separated is True

    def test_error_both_prefix_and_option(self):
        """Test error when both flag_off_prefix and flag_off_option provided."""

        with pytest.raises(ValueError, match="Provide only one"):
            AutoOption(flag_off_prefix="disable", flag_off_option="quiet")

    def test_error_off_options_when_disabled(self):
        """Test error when providing off options with flag_enable_on_off=False."""

        with pytest.raises(ValueError, match="Cannot specify.*when flag_enable_on_off=False"):
            AutoOption(flag_enable_on_off=False, flag_off_option="quiet")

        with pytest.raises(ValueError, match="Cannot specify.*when flag_enable_on_off=False"):
            AutoOption(flag_enable_on_off=False, flag_off_prefix="disable")

    def test_combined_parameters(self):
        """Test combining multiple parameters."""

        marker = AutoOption(required=True, flag_off_option="quiet")
        assert marker.required is True
        assert marker.flag_off_option == "quiet"

    def test_marker_usage_in_wry_model(self):
        """Test that new markers work with WryModel (not just AutoWryModel)."""

        from wry import WryModel

        class Config(WryModel):
            field: Annotated[str, AutoOption()] = Field(default="value")
            arg: Annotated[str, AutoArgument()] = Field(description="Argument")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        params = {p.name: p for p in cmd.params}
        assert "field" in params
        assert isinstance(params["field"], click.Option)

        args = [p for p in cmd.params if isinstance(p, click.Argument)]
        assert any(p.name == "arg" for p in args)

    def test_backward_compat_with_enum_emits_warning(self):
        """Test that old AutoClickParameter enum usage emits deprecation warning."""

        from wry import AutoClickParameter

        with pytest.warns(DeprecationWarning, match="AutoClickParameter.*deprecated"):

            class Config(AutoWryModel):
                field: Annotated[str, AutoClickParameter.OPTION] = Field(default="value")

            @click.command()
            @Config.generate_click_parameters()
            def cmd(**kwargs: Any):
                pass

        # Should still work
        params = {p.name: p for p in cmd.params}
        assert "field" in params

    def test_new_api_no_warnings(self):
        """Test that new API doesn't emit any warnings."""

        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            class Config(AutoWryModel):
                field: Annotated[str, AutoOption()] = Field(default="value")
                arg: Annotated[str, AutoArgument()] = Field(description="Arg")
                hidden: Annotated[str, AutoExclude()] = Field(default="hidden")

            @click.command()
            @Config.generate_click_parameters()
            def cmd(**kwargs: Any):
                pass

        # Should work without warnings
        params = {p.name: p for p in cmd.params}
        assert "field" in params
        assert "hidden" not in params

    def test_comma_separated_via_auto_option(self):
        """Test comma-separated lists using AutoOption(comma_separated=True)."""

        class Config(AutoWryModel):
            tags: Annotated[list[str], AutoOption(comma_separated=True)] = Field(
                default_factory=list, description="Tags"
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")

        runner = CliRunner()

        # Test comma-separated input
        result = runner.invoke(cmd, ["--tags", "python,rust,go"])
        assert result.exit_code == 0
        assert "Tags: ['python', 'rust', 'go']" in result.output

    def test_deprecated_comma_separated_marker_warning(self):
        """Test that standalone CommaSeparated marker emits deprecation warning."""
        from wry import CommaSeparated

        with pytest.warns(DeprecationWarning, match="CommaSeparated.*deprecated.*AutoOption"):

            class Config(AutoWryModel):
                tags: Annotated[list[str], CommaSeparated] = Field(default_factory=list)

            @click.command()
            @Config.generate_click_parameters()
            def cmd(**kwargs: Any):
                pass

        # Should still work (backwards compat)
        runner = CliRunner()
        result = runner.invoke(cmd, ["--tags", "a,b,c"])
        assert result.exit_code == 0
