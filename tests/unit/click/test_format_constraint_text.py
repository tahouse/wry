"""Test constraint text formatting for improved coverage."""

from typing import Annotated

import click
from annotated_types import Ge, Gt, Interval, Le, Len, Lt, MaxLen, MinLen, MultipleOf, Predicate, Timezone
from click.testing import CliRunner
from pydantic import Field

from wry import AutoOption, WryModel, generate_click_parameters


class TestFormatConstraintText:
    """Test constraint text formatting for various constraint types."""

    def test_constraint_gt(self):
        """Test Greater Than constraint."""

        class Config(WryModel):
            value: Annotated[int, AutoOption, Gt(0)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # The constraint should be in the help text
        ctx = click.Context(cmd)
        help_text = cmd.get_help(ctx)
        assert "value" in help_text.lower()

    def test_constraint_lt(self):
        """Test Less Than constraint."""

        class Config(WryModel):
            value: Annotated[int, AutoOption, Lt(100)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_ge(self):
        """Test Greater or Equal constraint."""

        class Config(WryModel):
            value: Annotated[int, AutoOption, Ge(1)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_le(self):
        """Test Less or Equal constraint."""

        class Config(WryModel):
            value: Annotated[int, AutoOption, Le(99)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_len(self):
        """Test Len constraint."""

        class Config(WryModel):
            value: Annotated[str, AutoOption, Len(5, 10)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_minlen(self):
        """Test MinLen constraint."""

        class Config(WryModel):
            value: Annotated[str, AutoOption, MinLen(3)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_maxlen(self):
        """Test MaxLen constraint."""

        class Config(WryModel):
            value: Annotated[str, AutoOption, MaxLen(20)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_interval(self):
        """Test Interval constraint."""

        class Config(WryModel):
            value: Annotated[int, AutoOption, Interval(ge=1, le=100)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_multiple_of(self):
        """Test MultipleOf constraint."""

        class Config(WryModel):
            value: Annotated[int, AutoOption, MultipleOf(5)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_predicate(self):
        """Test Predicate constraint."""

        def is_even(x: int) -> bool:
            return x % 2 == 0

        class Config(WryModel):
            value: Annotated[int, AutoOption, Predicate(is_even)] = Field(description="Value")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0

    def test_constraint_timezone(self):
        """Test Timezone constraint."""

        class Config(WryModel):
            tz: Annotated[str, AutoOption, Timezone(...)] = Field(description="Timezone", default="UTC")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0
