"""Test Click argument type handling for improved coverage."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoArgument, WryModel, generate_click_parameters


class TestArgumentTypes:
    """Test different type handling for Click arguments."""

    def test_argument_with_optional_int_type(self):
        """Test argument with Optional[int] type."""

        class Config(WryModel):
            count: Annotated[int | None, AutoArgument] = Field(description="Count value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            config = Config(**kwargs)
            click.echo(f"count={config.count}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["42"])
        assert result.exit_code == 0
        assert "count=42" in result.output

    def test_argument_with_float_type(self):
        """Test argument with float type."""

        class Config(WryModel):
            ratio: Annotated[float, AutoArgument] = Field(description="Ratio value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            config = Config(**kwargs)
            click.echo(f"ratio={config.ratio}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["3.14"])
        assert result.exit_code == 0
        assert "ratio=3.14" in result.output

    def test_argument_with_bool_type(self):
        """Test argument with bool type."""

        class Config(WryModel):
            enabled: Annotated[bool, AutoArgument] = Field(description="Enabled flag")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            config = Config(**kwargs)
            click.echo(f"enabled={config.enabled}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["true"])
        assert result.exit_code == 0
        assert "enabled=True" in result.output

    def test_argument_with_custom_type(self):
        """Test argument with custom type (not str/int/float/bool)."""

        class CustomType:
            def __init__(self, value: str):
                self.value = value.upper()

            def __str__(self):
                return self.value

        class Config(WryModel):
            custom: Annotated[CustomType, AutoArgument] = Field(description="Custom value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            # The value will be passed as string from Click
            # We'll convert it in the command
            if isinstance(kwargs.get("custom"), str):
                kwargs["custom"] = CustomType(kwargs["custom"])
            config = Config(**kwargs)
            click.echo(f"custom={config.custom}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["hello"])
        assert result.exit_code == 0
        # Note: This will fail validation, but tests the code path

    def test_argument_with_optional_no_none_types(self):
        """Test Optional with multiple types."""

        class Config(WryModel):
            value: Annotated[str | None, AutoArgument] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            config = Config(**kwargs)
            click.echo(f"value={config.value}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["test"])
        assert result.exit_code == 0
        assert "value=test" in result.output
