"""Test Click integration functionality."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import (
    AutoArgument,
    AutoOption,
    WryModel,
    generate_click_parameters,
)


class TestClickIntegration:
    """Test Click parameter generation and integration."""

    def test_auto_option_generation(self):
        """Test automatic Click option generation."""

        class TestConfig(WryModel):
            name: Annotated[str, AutoOption] = Field(default="test", description="Name parameter")
            count: Annotated[int, AutoOption] = Field(default=1, ge=1, le=100, description="Count parameter")
            verbose: Annotated[bool, AutoOption] = Field(default=False, description="Verbose flag")

        @click.command()
        @generate_click_parameters(TestConfig)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = TestConfig.from_click_context(ctx, **kwargs)
            click.echo(f"name={config.name}")
            click.echo(f"count={config.count}")
            click.echo(f"verbose={config.verbose}")
            click.echo(f"name_source={config.source.name.value}")
            click.echo(f"count_source={config.source.count.value}")

        runner = CliRunner()

        # Test with defaults
        result = runner.invoke(test_command, [])
        assert result.exit_code == 0
        assert "name=test" in result.output
        assert "count=1" in result.output
        assert "verbose=False" in result.output
        assert "name_source=default" in result.output

        # Test with CLI args
        result = runner.invoke(test_command, ["--name", "cli-test", "--count", "5", "--verbose"])
        assert result.exit_code == 0
        assert "name=cli-test" in result.output
        assert "count=5" in result.output
        assert "verbose=True" in result.output
        assert "name_source=cli" in result.output
        assert "count_source=cli" in result.output

    def test_auto_argument_generation(self):
        """Test automatic Click argument generation."""

        class TestConfig(WryModel):
            filename: Annotated[str, AutoArgument] = Field(description="Input filename")
            optional_arg: Annotated[str | None, AutoOption] = Field(default=None, description="Optional parameter")

        @click.command()
        @generate_click_parameters(TestConfig)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = TestConfig.from_click_context(ctx, **kwargs)
            click.echo(f"filename={config.filename}")
            if config.optional_arg:
                click.echo(f"optional={config.optional_arg}")

        runner = CliRunner()

        # Test with argument
        result = runner.invoke(test_command, ["test.txt"])
        assert result.exit_code == 0
        assert "filename=test.txt" in result.output

    def test_config_file_loading(self):
        """Test JSON config file loading."""

        class TestConfig(WryModel):
            name: Annotated[str, AutoOption] = Field(description="Name")
            value: Annotated[int, AutoOption] = Field(default=42)

        @click.command()
        @generate_click_parameters(TestConfig)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = TestConfig.from_click_context(ctx, **kwargs)
            click.echo(f"name={config.name}")
            click.echo(f"value={config.value}")
            click.echo(f"name_source={config.source.name.value}")
            click.echo(f"value_source={config.source.value.value}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a config file
            with open("config.json", "w") as f:
                f.write('{"name": "from-json", "value": 100}')

            # Test loading from config
            result = runner.invoke(test_command, ["--config", "config.json"])
            assert result.exit_code == 0
            assert "name=from-json" in result.output
            assert "value=100" in result.output
            assert "name_source=json" in result.output
            assert "value_source=json" in result.output

            # Test CLI override of config
            result = runner.invoke(test_command, ["--config", "config.json", "--name", "cli-override"])
            assert result.exit_code == 0
            assert "name=cli-override" in result.output
            assert "value=100" in result.output
            assert "name_source=cli" in result.output
            assert "value_source=json" in result.output

    def test_environment_variables(self):
        """Test environment variable handling."""
        import os

        class TestConfig(WryModel):
            env_prefix = "DRYCLI_"
            api_key: Annotated[str, AutoOption] = Field(description="API key")
            timeout: Annotated[int, AutoOption] = Field(default=30)

        @click.command()
        @generate_click_parameters(TestConfig)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = TestConfig.from_click_context(ctx, **kwargs)
            click.echo(f"api_key={config.api_key}")
            click.echo(f"timeout={config.timeout}")
            click.echo(f"api_key_source={config.source.api_key.value}")
            click.echo(f"timeout_source={config.source.timeout.value}")

        runner = CliRunner()

        # Set env vars - need to set in actual os.environ for param generation
        original_env = {}
        env_vars = {"DRYCLI_API_KEY": "env-secret-key", "DRYCLI_TIMEOUT": "60"}

        # Save original values and set new ones
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # Test with env vars
            result = runner.invoke(test_command, [])
            assert result.exit_code == 0
            assert "api_key=env-secret-key" in result.output
            assert "timeout=60" in result.output
            assert "api_key_source=env" in result.output
            assert "timeout_source=env" in result.output

            # Test CLI override of env
            result = runner.invoke(test_command, ["--timeout", "90"])
            assert result.exit_code == 0
            assert "timeout=90" in result.output
            assert "timeout_source=cli" in result.output
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_constraint_display_in_help(self):
        """Test that constraints are shown in help text."""

        class TestConfig(WryModel):
            age: Annotated[int, AutoOption] = Field(default=25, ge=0, le=120, description="Your age")
            score: Annotated[float, AutoOption] = Field(
                default=0.0, ge=0.0, le=100.0, multiple_of=0.5, description="Score"
            )

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(test_command, ["--help"])

        assert result.exit_code == 0
        # Check that constraints are shown in help
        assert ">= 0" in result.output
        assert "<= 120" in result.output
        assert "<= 100.0" in result.output
        assert "multiple of 0.5" in result.output

    def test_show_env_vars_option(self):
        """Test the --show-env-vars option."""

        class TestConfig(WryModel):
            env_prefix = "DRYCLI_"
            debug: Annotated[bool, AutoOption] = Field(default=False, description="Enable debug mode")
            port: Annotated[int, AutoOption] = Field(default=8080, description="Server port")

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(test_command, ["--show-env-vars"])

        assert result.exit_code == 0
        assert "DRYCLI_DEBUG" in result.output
        assert "DRYCLI_PORT" in result.output
        assert "Enable debug mode" in result.output
        assert "Server port" in result.output
