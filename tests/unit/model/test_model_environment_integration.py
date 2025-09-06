"""Test WryModel environment variable integration."""

import os
from typing import ClassVar

from pydantic import Field

from wry.core.model import WryModel


class TestEnvironmentVariableIntegration:
    """Test environment variable loading and configuration."""

    def test_get_env_var_names_with_prefix(self):
        """Test getting environment variable names with prefix."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "APP_"
            host: str = "localhost"
            port: int = 8080

        config = Config()

        env_vars = config.get_env_var_names()
        assert env_vars == {"host": "APP_HOST", "port": "APP_PORT"}

    def test_load_from_env_with_default_factory(self):
        """Test loading from environment with fields that have default factories."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "APP_"
            tags: list[str] = Field(default_factory=list)
            settings: dict[str, str] = Field(default_factory=dict)

        # Don't set any env vars, should use default_factory
        config = Config.load_from_env()
        assert config.tags == []
        assert isinstance(config.tags, list)
        assert config.settings == {}
        assert isinstance(config.settings, dict)

    def test_environment_source_tracking(self):
        """Test that environment variables are properly tracked as sources."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "TEST_"
            api_key: str = "default"
            timeout: int = 30

        # Set environment variable
        os.environ["TEST_API_KEY"] = "secret-key"
        os.environ["TEST_TIMEOUT"] = "60"

        try:
            config = Config.load_from_env()

            assert config.api_key == "secret-key"
            assert config.timeout == 60

            # Check sources
            assert config.source.api_key.value == "env"
            assert config.source.timeout.value == "env"

        finally:
            del os.environ["TEST_API_KEY"]
            del os.environ["TEST_TIMEOUT"]
