"""Tests for AutoWryModel functionality."""

from typing import Annotated

import click
import pytest
from click.testing import CliRunner
from pydantic import Field

from wry import AutoArgument, AutoWryModel, create_auto_model, generate_click_parameters


class TestAutoWryModel:
    """Test the AutoWryModel base class."""

    def test_auto_model_basic(self):
        """Test basic AutoWryModel functionality."""

        class Config(AutoWryModel):
            name: str = Field(description="User name")
            age: int = Field(default=25, description="User age")
            active: bool = Field(default=True, description="Is active")

        # Check that fields are annotated
        hints = Config.__annotations__
        assert "name" in hints
        assert "age" in hints
        assert "active" in hints

    def test_auto_model_with_cli(self):
        """Test AutoWryModel with Click integration."""

        class Config(AutoWryModel):
            name: str = Field(description="Your name")
            count: int = Field(default=1, ge=1, le=10, description="Count")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            config = Config(**kwargs)
            click.echo(f"{config.name}: {config.count}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--name", "Alice", "--count", "5"])

        assert result.exit_code == 0
        assert "Alice: 5" in result.output

    def test_auto_model_inheritance(self):
        """Test that AutoWryModel properly inherits from WryModel."""

        class Config(AutoWryModel):
            value: int = Field(default=42)

        config = Config()

        # Should have all WryModel features
        assert hasattr(config, "source")
        assert hasattr(config, "minimum")
        assert hasattr(config, "maximum")
        assert config.value == 42
        assert config.source.value.value == "default"

    def test_auto_model_mixed_annotations(self):
        """Test AutoWryModel with some fields already annotated."""

        class Config(AutoWryModel):
            # This field already has annotation - should be preserved
            special: Annotated[str, AutoArgument] = Field(description="Special arg")
            # These should get AutoOption
            name: str = Field(description="Name")
            value: int = Field(default=10)

        # Build CLI to verify
        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # special should be an argument (positional)
        # name and value should be options
        assert any(isinstance(p, click.Argument) and p.name == "special" for p in cmd.params)  # positional
        assert any(isinstance(p, click.Option) and "--name" in p.opts for p in cmd.params)  # option
        assert any(isinstance(p, click.Option) and "--value" in p.opts for p in cmd.params)  # option

    def test_auto_model_env_prefix(self):
        """Test that AutoWryModel respects env_prefix."""

        class Config(AutoWryModel):
            env_prefix = "MYAPP_"

            api_key: str = Field(default="", description="API key")

        import os

        os.environ["MYAPP_API_KEY"] = "secret123"

        try:
            config = Config.load_from_env()
            assert config.api_key == "secret123"
            assert config.source.api_key.value == "env"
        finally:
            del os.environ["MYAPP_API_KEY"]

    def test_auto_model_complex_types(self):
        """Test AutoWryModel with complex field types."""

        class Config(AutoWryModel):
            # Optional field
            optional_value: int | None = Field(default=None, description="Optional")
            # Float with constraints
            ratio: float = Field(default=0.5, ge=0.0, le=1.0, description="Ratio")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            config = Config(**kwargs)
            click.echo(f"Optional: {config.optional_value}")
            click.echo(f"Ratio: {config.ratio}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--optional-value", "42", "--ratio", "0.75"])

        assert result.exit_code == 0
        assert "Optional: 42" in result.output
        assert "Ratio: 0.75" in result.output


class TestCreateAutoModel:
    """Test the create_auto_model function."""

    def test_create_auto_model_basic(self):
        """Test basic dynamic model creation."""
        DynamicConfig = create_auto_model(
            "DynamicConfig",
            {
                "name": (str, Field(description="Name")),
                "age": (int, Field(default=30, ge=0, description="Age")),
                "active": (bool, Field(default=True, description="Active")),
            },
        )

        # Test instantiation
        config = DynamicConfig(name="Bob")
        assert config.name == "Bob"
        assert config.age == 30
        assert config.active is True

    def test_create_auto_model_with_cli(self):
        """Test dynamic model with CLI."""
        UserConfig = create_auto_model(
            "UserConfig",
            {
                "username": (str, Field(description="Username")),
                "email": (str, Field(description="Email address")),
                "admin": (bool, Field(default=False, description="Admin user")),
            },
        )

        @click.command()
        @generate_click_parameters(UserConfig)
        def cmd(**kwargs):
            config = UserConfig(**kwargs)
            click.echo(f"User: {config.username} ({config.email})")
            if config.admin:
                click.echo("Admin access granted")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--username", "alice", "--email", "alice@example.com", "--admin"])

        assert result.exit_code == 0
        assert "User: alice (alice@example.com)" in result.output
        assert "Admin access granted" in result.output

    def test_create_auto_model_validation(self):
        """Test that validation works on dynamic models."""
        NumericConfig = create_auto_model(
            "NumericConfig", {"value": (int, Field(ge=0, le=100, description="Value between 0-100"))}
        )

        # Valid value
        config = NumericConfig(value=50)
        assert config.value == 50

        # Invalid value
        with pytest.raises(ValueError, match="less than or equal to 100"):
            NumericConfig(value=150)

    def test_create_auto_model_with_base(self):
        """Test creating model with custom base class."""

        class MyBase(AutoWryModel):
            env_prefix = "TEST_"

            def custom_method(self):
                return "custom"

        CustomConfig = create_auto_model("CustomConfig", {"setting": (str, Field(default="test"))}, __base__=MyBase)

        config = CustomConfig()
        assert config.setting == "test"
        assert config.custom_method() == "custom"
        assert config.env_prefix == "TEST_"

    def test_create_auto_model_type_annotations(self):
        """Test various type annotations in dynamic models."""
        ComplexConfig = create_auto_model(
            "ComplexConfig",
            {
                # Simple types
                "text": (str, Field(description="Text")),
                "number": (int, Field(default=0)),
                "flag": (bool, Field(default=False)),
                # Optional
                "optional": (str | None, Field(default=None)),
                # List
                "items": (list[str], Field(default_factory=list)),
                # Dict
                "mapping": (dict[str, int], Field(default_factory=dict)),
            },
        )

        config = ComplexConfig(text="hello", items=["a", "b"], mapping={"x": 1})
        assert config.text == "hello"
        assert config.items == ["a", "b"]
        assert config.mapping == {"x": 1}
        assert config.optional is None

    def test_create_auto_model_source_tracking(self):
        """Test that dynamic models have source tracking."""
        import os

        TrackingConfig = create_auto_model(
            "TrackingConfig", {"key": (str, Field(default="default"))}, env_prefix="TRACK_"
        )

        # Test with environment variable
        os.environ["TRACK_KEY"] = "from-env"
        try:
            config = TrackingConfig.load_from_env()
            assert config.key == "from-env"
            assert config.source.key.value == "env"
        finally:
            del os.environ["TRACK_KEY"]

    def test_create_auto_model_empty(self):
        """Test creating model with no fields."""
        EmptyConfig = create_auto_model("EmptyConfig", {})

        config = EmptyConfig()
        # Should still have WryModel features
        assert hasattr(config, "source")
        assert hasattr(config, "model_dump")
