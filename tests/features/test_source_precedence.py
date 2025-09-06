"""Test configuration source precedence and interactions."""

import json
import os
from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoOption, WryModel, generate_click_parameters


class TestSourcePrecedence:
    """Test that configuration sources work together with correct precedence."""

    def test_complete_precedence_chain(self):
        """Test full precedence: defaults < env < json < cli."""

        class Config(WryModel):
            env_prefix = "TESTAPP_"

            # Field with all possible sources
            name: Annotated[str, AutoOption] = Field(default="default-name", description="Name")

            # Field with no default (required)
            api_key: Annotated[str, AutoOption] = Field(description="API key")

            # Field with type conversion
            port: Annotated[int, AutoOption] = Field(default=8080, description="Port")

            # Boolean field
            debug: Annotated[bool, AutoOption] = Field(default=False, description="Debug mode")

        @click.command()
        @generate_click_parameters(Config)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = Config.from_click_context(ctx, **kwargs)

            # Print values
            click.echo(f"name={config.name}")
            click.echo(f"api_key={config.api_key}")
            click.echo(f"port={config.port}")
            click.echo(f"debug={config.debug}")

            # Print sources
            click.echo(f"name_source={config.source.name.value}")
            click.echo(f"api_key_source={config.source.api_key.value}")
            click.echo(f"port_source={config.source.port.value}")
            click.echo(f"debug_source={config.source.debug.value}")

        runner = CliRunner()

        # Save original env
        original_env = {}
        test_env = {
            "TESTAPP_NAME": "env-name",
            "TESTAPP_API_KEY": "env-key",
            "TESTAPP_PORT": "9000",
            "TESTAPP_DEBUG": "true",
        }

        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            with runner.isolated_filesystem():
                # Create config file
                config_data = {
                    "name": "json-name",
                    "api_key": "json-key",
                    "port": 9090,
                    # debug not in JSON, should come from env
                }
                with open("config.json", "w") as f:
                    json.dump(config_data, f)

                # Test 1: Only defaults and env
                result = runner.invoke(test_command, [])
                if result.exit_code != 0:
                    print(f"Command failed with output:\n{result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0
                assert "name=env-name" in result.output
                assert "api_key=env-key" in result.output
                assert "port=9000" in result.output
                assert "debug=True" in result.output
                assert "name_source=env" in result.output
                assert "api_key_source=env" in result.output
                assert "port_source=env" in result.output
                assert "debug_source=env" in result.output

                # Test 2: Add JSON config (overrides env for some fields)
                result = runner.invoke(test_command, ["--config", "config.json"])
                if result.exit_code != 0:
                    print(f"Command failed with output:\n{result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0
                assert "name=json-name" in result.output  # JSON overrides env
                assert "api_key=json-key" in result.output  # JSON overrides env
                assert "port=9090" in result.output  # JSON overrides env
                assert "debug=True" in result.output  # Still from env (not in JSON)
                assert "name_source=json" in result.output
                assert "api_key_source=json" in result.output
                assert "port_source=json" in result.output
                assert "debug_source=env" in result.output

                # Test 3: CLI overrides everything
                result = runner.invoke(
                    test_command,
                    [
                        "--config",
                        "config.json",
                        "--name",
                        "cli-name",
                        "--port",
                        "8888",
                        # Skip boolean flag test for now
                    ],
                )
                if result.exit_code != 0:
                    print(f"Command failed with output:\n{result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0
                assert "name=cli-name" in result.output  # CLI overrides JSON
                assert "api_key=json-key" in result.output  # Still from JSON
                assert "port=8888" in result.output  # CLI overrides JSON
                assert "debug=True" in result.output  # Still from env (no CLI override)
                assert "name_source=cli" in result.output
                assert "api_key_source=json" in result.output
                assert "port_source=cli" in result.output
                assert "debug_source=env" in result.output

        finally:
            # Restore env
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_partial_sources(self):
        """Test when only some sources provide values."""

        class Config(WryModel):
            env_prefix = "PARTIAL_"

            field1: Annotated[str, AutoOption] = Field(default="default1")
            field2: Annotated[str, AutoOption] = Field(default="default2")
            field3: Annotated[str, AutoOption] = Field(default="default3")
            field4: Annotated[str, AutoOption] = Field(default="default4")

        @click.command()
        @generate_click_parameters(Config)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = Config.from_click_context(ctx, **kwargs)
            for field in ["field1", "field2", "field3", "field4"]:
                value = getattr(config, field)
                source = getattr(config.source, field).value
                click.echo(f"{field}={value} (source={source})")

        runner = CliRunner()

        # Set only field2 in env
        os.environ["PARTIAL_FIELD2"] = "env-value2"

        try:
            with runner.isolated_filesystem():
                # JSON has field2 and field3
                with open("config.json", "w") as f:
                    json.dump({"field2": "json-value2", "field3": "json-value3"}, f)

                # CLI provides field3 and field4
                result = runner.invoke(
                    test_command, ["--config", "config.json", "--field3", "cli-value3", "--field4", "cli-value4"]
                )

                if result.exit_code != 0:
                    print(f"Command failed with output:\n{result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0
                # field1: only has default
                assert "field1=default1 (source=default)" in result.output
                # field2: env < json (json wins)
                assert "field2=json-value2 (source=json)" in result.output
                # field3: json < cli (cli wins)
                assert "field3=cli-value3 (source=cli)" in result.output
                # field4: default < cli (cli wins)
                assert "field4=cli-value4 (source=cli)" in result.output

        finally:
            os.environ.pop("PARTIAL_FIELD2", None)

    def test_type_conversion_across_sources(self):
        """Test that type conversion works correctly for all sources."""

        class Config(WryModel):
            env_prefix = "TYPES_"

            count: Annotated[int, AutoOption] = Field(default=1)
            ratio: Annotated[float, AutoOption] = Field(default=1.0)
            enabled: Annotated[bool, AutoOption] = Field(default=False)

        @click.command()
        @generate_click_parameters(Config)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"count={config.count} (type={type(config.count).__name__})")
            click.echo(f"ratio={config.ratio} (type={type(config.ratio).__name__})")
            click.echo(f"enabled={config.enabled} (type={type(config.enabled).__name__})")

        runner = CliRunner()

        # Test env var type conversion
        os.environ["TYPES_COUNT"] = "42"
        os.environ["TYPES_RATIO"] = "3.14"
        os.environ["TYPES_ENABLED"] = "yes"

        try:
            result = runner.invoke(test_command, [])
            assert result.exit_code == 0
            assert "count=42 (type=int)" in result.output
            assert "ratio=3.14 (type=float)" in result.output
            assert "enabled=True (type=bool)" in result.output

            # Test JSON type handling
            with runner.isolated_filesystem():
                with open("config.json", "w") as f:
                    json.dump({"count": 100, "ratio": 2.5, "enabled": True}, f)

                result = runner.invoke(test_command, ["--config", "config.json"])
                if result.exit_code != 0:
                    print(f"Command failed with output:\n{result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0
                assert "count=100 (type=int)" in result.output
                assert "ratio=2.5 (type=float)" in result.output
                assert "enabled=True (type=bool)" in result.output

        finally:
            for key in ["TYPES_COUNT", "TYPES_RATIO", "TYPES_ENABLED"]:
                os.environ.pop(key, None)

    def test_missing_required_field_fallback(self):
        """Test that required fields are satisfied by any source in precedence order."""

        class Config(WryModel):
            env_prefix = "REQ_"
            required_field: Annotated[str, AutoOption] = Field(description="Required")

        @click.command()
        @generate_click_parameters(Config)
        @click.pass_context
        def test_command(ctx: click.Context, **kwargs):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"value={config.required_field}")
            click.echo(f"source={config.source.required_field.value}")

        runner = CliRunner()

        # Test 1: Env provides required field
        os.environ["REQ_REQUIRED_FIELD"] = "from-env"
        try:
            result = runner.invoke(test_command, [])
            assert result.exit_code == 0
            assert "value=from-env" in result.output
            assert "source=env" in result.output
        finally:
            os.environ.pop("REQ_REQUIRED_FIELD", None)

        # Test 2: JSON provides required field
        with runner.isolated_filesystem():
            with open("config.json", "w") as f:
                json.dump({"required_field": "from-json"}, f)

            result = runner.invoke(test_command, ["--config", "config.json"])
            assert result.exit_code == 0
            assert "value=from-json" in result.output
            assert "source=json" in result.output

        # Test 3: CLI provides required field
        result = runner.invoke(test_command, ["--required-field", "from-cli"])
        assert result.exit_code == 0
        assert "value=from-cli" in result.output
        assert "source=cli" in result.output

        # Test 4: No source provides it - should fail
        result = runner.invoke(test_command, [])
        assert result.exit_code != 0
        # The error comes from Click (missing required option) or Pydantic (validation error)
        # Check both stdout and the exception message
        error_text = str(result.exception) if result.exception else result.output
        assert (
            "Missing option" in error_text
            or "required" in error_text.lower()
            or "Field required" in error_text
            or "validation error" in error_text
        )
