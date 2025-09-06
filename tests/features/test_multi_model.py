"""Tests for multi-model support functionality."""

from typing import Annotated

import click
import pytest
from click.testing import CliRunner
from pydantic import Field

from wry import (
    AutoOption,
    WryModel,
    create_models,
    generate_click_parameters,
    multi_model,
    singleton_option,
    split_kwargs_by_model,
)


class DatabaseArgs(WryModel):
    """Database arguments."""

    host: Annotated[str, AutoOption] = Field(default="localhost", description="Database host")
    port: Annotated[int, AutoOption] = Field(default=5432, ge=1, le=65535, description="Database port")
    user: Annotated[str, AutoOption] = Field(default="admin", description="Database user")


class AppArgs(WryModel):
    """Application arguments."""

    debug: Annotated[bool, AutoOption] = Field(default=False, description="Enable debug mode")
    workers: Annotated[int, AutoOption] = Field(default=4, ge=1, le=100, description="Number of workers")
    timeout: Annotated[float, AutoOption] = Field(default=30.0, gt=0, description="Request timeout")


class CacheArgs(WryModel):
    """Cache arguments."""

    enabled: Annotated[bool, AutoOption] = Field(default=True, description="Enable caching")
    ttl: Annotated[int, AutoOption] = Field(default=3600, ge=0, description="Cache TTL in seconds")


class TestSplitKwargs:
    """Test the split_kwargs_by_model function."""

    def test_split_kwargs_basic(self):
        """Test basic kwarg splitting between models."""
        kwargs = {"host": "example.com", "port": 3306, "debug": True, "workers": 8, "unknown": "ignored"}

        result = split_kwargs_by_model(kwargs, DatabaseArgs, AppArgs)

        assert result[DatabaseArgs] == {"host": "example.com", "port": 3306}
        assert result[AppArgs] == {"debug": True, "workers": 8}

    def test_split_kwargs_overlapping_fields(self):
        """Test handling of fields that exist in multiple models."""

        class Model1(WryModel):
            name: str = Field(default="model1")
            shared: int = Field(default=1)

        class Model2(WryModel):
            name: str = Field(default="model2")
            shared: int = Field(default=2)

        kwargs = {"name": "test", "shared": 42}

        # Both models should get the overlapping fields
        result = split_kwargs_by_model(kwargs, Model1, Model2)

        # Both models get the same values for overlapping fields
        assert result[Model1] == {"name": "test", "shared": 42}
        assert result[Model2] == {"name": "test", "shared": 42}

    def test_split_kwargs_empty(self):
        """Test splitting empty kwargs."""
        result = split_kwargs_by_model({}, DatabaseArgs, AppArgs)

        assert result[DatabaseArgs] == {}
        assert result[AppArgs] == {}

    def test_split_kwargs_single_model(self):
        """Test splitting with a single model."""
        kwargs = {"host": "example.com", "port": 3306}
        result = split_kwargs_by_model(kwargs, DatabaseArgs)

        assert result[DatabaseArgs] == {"host": "example.com", "port": 3306}


class TestCreateModels:
    """Test the create_models helper function."""

    def test_create_models_basic(self):
        """Test creating models from kwargs."""
        import click

        ctx = click.Context(click.Command("test"))
        kwargs = {"host": "db.example.com", "debug": True, "workers": 16}

        configs = create_models(ctx, kwargs, DatabaseArgs, AppArgs)

        assert isinstance(configs[DatabaseArgs], DatabaseArgs)
        assert configs[DatabaseArgs].host == "db.example.com"
        assert configs[DatabaseArgs].port == 5432  # default

        assert isinstance(configs[AppArgs], AppArgs)
        assert configs[AppArgs].debug is True
        assert configs[AppArgs].workers == 16

    def test_create_models_with_source_tracking(self):
        """Test that create_models preserves source tracking."""
        import click

        ctx = click.Context(click.Command("test"))
        kwargs = {"host": "db.example.com"}

        configs = create_models(ctx, kwargs, DatabaseArgs)
        db_config = configs[DatabaseArgs]

        # Check source tracking
        assert db_config.source.host.value == "cli"  # from kwargs
        assert db_config.source.port.value == "default"  # default value

    def test_create_models_validation(self):
        """Test that validation works in created models."""
        import click

        ctx = click.Context(click.Command("test"))
        kwargs = {"port": 99999}  # Invalid port

        with pytest.raises(ValueError, match="less than or equal to 65535"):
            create_models(ctx, kwargs, DatabaseArgs)


class TestMultiModelDecorator:
    """Test the multi_model decorator."""

    def test_multi_model_basic(self):
        """Test basic multi-model command."""

        @click.command()
        @multi_model(DatabaseArgs, AppArgs)
        @click.pass_context
        def cmd(ctx, **kwargs):
            configs = create_models(ctx, kwargs, DatabaseArgs, AppArgs)
            db = configs[DatabaseArgs]
            app = configs[AppArgs]

            click.echo(f"Database: {db.host}:{db.port}")
            click.echo(f"App: debug={app.debug}, workers={app.workers}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--host", "mydb", "--port", "3306", "--debug", "--workers", "10"])

        assert result.exit_code == 0
        assert "Database: mydb:3306" in result.output
        assert "App: debug=True, workers=10" in result.output

    def test_multi_model_help(self):
        """Test that help text includes all model fields."""

        @click.command()
        @multi_model(DatabaseArgs, AppArgs)
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        assert result.exit_code == 0
        # Database options
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--user" in result.output
        # App options
        assert "--debug" in result.output
        assert "--workers" in result.output
        assert "--timeout" in result.output

    def test_multi_model_three_models(self):
        """Test with three models."""

        @click.command()
        @multi_model(DatabaseArgs, AppArgs, CacheArgs)
        @click.pass_context
        def cmd(ctx, **kwargs):
            configs = create_models(ctx, kwargs, DatabaseArgs, AppArgs, CacheArgs)
            cache = configs[CacheArgs]
            click.echo(f"Cache: enabled={cache.enabled}, ttl={cache.ttl}")

        runner = CliRunner()
        # For boolean fields, we need to use the actual option name
        result = runner.invoke(cmd, ["--ttl", "7200"])  # enabled defaults to True

        # Debug output
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert "Cache: enabled=True, ttl=7200" in result.output

    def test_multi_model_with_json_file(self):
        """Test multi-model with JSON file input."""
        import json
        import tempfile

        @click.command()
        @multi_model(DatabaseArgs, AppArgs)
        @click.pass_context
        def cmd(ctx, **kwargs):
            configs = create_models(ctx, kwargs, DatabaseArgs, AppArgs)
            db = configs[DatabaseArgs]
            app = configs[AppArgs]

            click.echo(f"Database: {db.host}")
            click.echo(f"Debug: {app.debug}")

        config_data = {"host": "config-db", "debug": True}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            runner = CliRunner()
            result = runner.invoke(cmd, ["--config", config_file])

            assert result.exit_code == 0
            assert "Database: config-db" in result.output
            assert "Debug: True" in result.output
        finally:
            import os

            os.unlink(config_file)

    def test_multi_model_no_strict(self):
        """Test multi-model with strict=False."""

        @click.command()
        @multi_model(DatabaseArgs, AppArgs, strict=False)
        def cmd(**kwargs):
            pass

        # Should work without error
        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0


class TestSingletonOption:
    """Test the singleton_option utility."""

    def test_singleton_option_creates_same_instance(self):
        """Test that singleton option returns the same instance."""
        # Clear the cache first
        from wry.multi_model import _SINGLETON_OPTIONS

        _SINGLETON_OPTIONS.clear()

        # Create two identical singleton options
        option1 = singleton_option("--verbose", "-v", is_flag=True, help="Verbose output")
        option2 = singleton_option("--verbose", "-v", is_flag=True, help="Verbose output")

        # They should be the exact same object
        assert option1 is option2

    def test_singleton_option_different_keys(self):
        """Test that different option names create different instances."""
        from wry.multi_model import _SINGLETON_OPTIONS

        _SINGLETON_OPTIONS.clear()

        option1 = singleton_option("--verbose", is_flag=True)
        option2 = singleton_option("--debug", is_flag=True)

        # They should be different objects
        assert option1 is not option2

    def test_singleton_option_in_model(self):
        """Test using singleton option in a model."""
        from wry.multi_model import _SINGLETON_OPTIONS

        _SINGLETON_OPTIONS.clear()

        class Model1(WryModel):
            verbose: Annotated[bool, singleton_option("--verbose", "-v", is_flag=True)] = Field(default=False)

        class Model2(WryModel):
            verbose: Annotated[bool, singleton_option("--verbose", "-v", is_flag=True)] = Field(default=False)

        @click.command()
        @generate_click_parameters(Model1, strict=False)
        @generate_click_parameters(Model2, strict=False)
        def cmd(**kwargs):
            click.echo(f"Verbose: {kwargs.get('verbose', False)}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--verbose"])

        assert result.exit_code == 0
        assert "Verbose: True" in result.output
