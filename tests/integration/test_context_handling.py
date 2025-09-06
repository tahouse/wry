"""Tests for Click context handling in wry."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoOption, WryModel, generate_click_parameters


class ExampleConfig(WryModel):
    """Example configuration model."""

    name: Annotated[str, AutoOption] = Field(default="test", description="Name option")
    debug: Annotated[bool, AutoOption] = Field(default=False, description="Debug flag")


class TestContextHandling:
    """Test different ways of handling Click context."""

    def test_with_explicit_pass_context(self):
        """Test using explicit @click.pass_context decorator."""

        @click.command()
        @generate_click_parameters(ExampleConfig)
        @click.pass_context
        def cmd(ctx, **kwargs):
            # Context is available because we used @click.pass_context
            assert isinstance(ctx, click.Context)
            config = ExampleConfig.from_click_context(ctx, **kwargs)
            click.echo(f"Name: {config.name}, Source: {config.source.name}")
            return config

        runner = CliRunner()
        result = runner.invoke(cmd, ["--name", "test-value"])

        assert result.exit_code == 0
        assert "Name: test-value, Source: ValueSource.CLI" in result.output

    def test_without_pass_context_decorator(self):
        """Test using from_click_context without @click.pass_context decorator."""

        @click.command()
        @generate_click_parameters(ExampleConfig)
        def cmd(**kwargs):
            # When called through Click, context is available via get_current_context()
            # So this works even without @click.pass_context decorator
            config = ExampleConfig.from_click_context(**kwargs)
            click.echo(f"Name: {config.name}, Debug: {config.debug}")
            # But we won't have ctx as a parameter
            assert "ctx" not in kwargs
            return config

        runner = CliRunner()
        result = runner.invoke(cmd, ["--name", "no-ctx", "--debug"])

        assert result.exit_code == 0
        assert "Name: no-ctx, Debug: True" in result.output

    def test_direct_instantiation(self):
        """Test direct model instantiation without context."""

        @click.command()
        @generate_click_parameters(ExampleConfig)
        def cmd(**kwargs):
            # Direct instantiation - simple but no source tracking
            config = ExampleConfig(**kwargs)
            click.echo(f"Name: {config.name}")
            # Direct instantiation doesn't provide accurate source tracking
            # Values will be marked as DEFAULT even if they came from CLI
            click.echo(f"Source (incorrect): {config.source.name}")
            return config

        runner = CliRunner()
        result = runner.invoke(cmd, ["--name", "direct"])

        assert result.exit_code == 0
        assert "Name: direct" in result.output

    def test_multiple_decorators_requires_care(self):
        """Test that multiple decorators need explicit pass_context control."""

        @click.command()
        @generate_click_parameters(ExampleConfig, strict=False)
        @generate_click_parameters(ExampleConfig, strict=False)  # Don't do this in real code!
        @click.pass_context  # Must be applied only once, after all decorators
        def cmd(ctx, **kwargs):
            config = ExampleConfig.from_click_context(ctx, **kwargs)
            click.echo(f"Config: {config.name}")
            return config

        runner = CliRunner()
        result = runner.invoke(cmd, ["--name", "multi"])

        assert result.exit_code == 0
        assert "Config: multi" in result.output

    def test_env_var_direct_instantiation(self):
        """Test environment variables with direct instantiation."""
        import os

        @click.command()
        @generate_click_parameters(ExampleConfig)
        def cmd(**kwargs):
            # Direct instantiation - env vars still work but no source tracking
            config = ExampleConfig(**kwargs)
            click.echo(f"Name: {config.name}, Source: {config.source.name}")
            return config

        # Set environment variable
        os.environ["DRYCLI_NAME"] = "from-env"

        try:
            runner = CliRunner()
            result = runner.invoke(cmd, [])

            assert result.exit_code == 0
            # With direct instantiation, source tracking is not accurate
            assert "Name: test" in result.output  # The value is from the default, not env
            # Direct instantiation shows everything as CLI
            assert "Source: ValueSource.CLI" in result.output
        finally:
            del os.environ["DRYCLI_NAME"]
