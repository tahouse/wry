"""Test WryModel default value handling."""

from typing import ClassVar

from pydantic import Field

from wry.core.model import WryModel


class TestDefaultValueHandling:
    """Test handling of default values and factories."""

    def test_load_from_env_with_simple_defaults(self):
        """Test that simple default values are properly tracked when loading from env."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "APP_"
            name: str = "default_name"
            port: int = 8080
            enabled: bool = True

        # Load without setting any env vars
        config = Config.load_from_env()

        # Values should use defaults
        assert config.name == "default_name"
        assert config.port == 8080
        assert config.enabled is True

        # Sources should be DEFAULT
        assert config.source.name.value == "default"
        assert config.source.port.value == "default"
        assert config.source.enabled.value == "default"

    def test_load_from_env_with_field_defaults(self):
        """Test Field() with explicit default values."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "TEST_"
            timeout: int = Field(default=30, description="Request timeout")
            retry_count: int = Field(default=3, ge=0, le=10)

        config = Config.load_from_env()

        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.source.timeout.value == "default"
        assert config.source.retry_count.value == "default"

    def test_mixed_defaults_and_factories(self):
        """Test models with both simple defaults and default factories."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "APP_"
            # Simple default
            name: str = "app"
            # Field with default
            port: int = Field(default=8080)
            # Default factory
            tags: list[str] = Field(default_factory=list)
            settings: dict[str, str] = Field(default_factory=lambda: {"debug": "false"})

        config = Config.load_from_env()

        assert config.name == "app"
        assert config.port == 8080
        assert config.tags == []
        assert config.settings == {"debug": "false"}

        # All should have DEFAULT source
        assert config.source.name.value == "default"
        assert config.source.port.value == "default"
        assert config.source.tags.value == "default"
        assert config.source.settings.value == "default"
