"""Test coverage gaps in env_utils.py module."""

import os
from typing import ClassVar

from pydantic import Field

from wry.core.env_utils import get_env_values
from wry.core.model import WryModel


class TestEnvUtilsCoverage:
    """Test env_utils coverage gaps."""

    def test_get_env_values_invalid_boolean(self):
        """Test get_env_values with invalid boolean value."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "APP_"
            enabled: bool = Field(default=True)

        # Set invalid boolean value
        os.environ["APP_ENABLED"] = "invalid"
        try:
            values = get_env_values(Config)
            # Should fall back to string value on ValueError
            assert values == {"enabled": "invalid"}
        finally:
            del os.environ["APP_ENABLED"]

    def test_get_env_values_various_conversions(self):
        """Test get_env_values with various type conversions."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "TEST_"
            # Test successful conversions
            count: int = Field(default=0)
            ratio: float = Field(default=0.0)
            enabled: bool = Field(default=False)
            name: str = Field(default="")

        # Set environment variables
        os.environ["TEST_COUNT"] = "42"
        os.environ["TEST_RATIO"] = "3.14"
        os.environ["TEST_ENABLED"] = "yes"  # Valid boolean
        os.environ["TEST_NAME"] = "test"

        try:
            values = get_env_values(Config)
            assert values == {"count": 42, "ratio": 3.14, "enabled": True, "name": "test"}
        finally:
            for key in ["TEST_COUNT", "TEST_RATIO", "TEST_ENABLED", "TEST_NAME"]:
                del os.environ[key]

    def test_get_env_values_conversion_errors(self):
        """Test get_env_values with conversion errors."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "APP_"
            count: int = Field(default=0)
            ratio: float = Field(default=0.0)

        # Set invalid values
        os.environ["APP_COUNT"] = "not_a_number"
        os.environ["APP_RATIO"] = "not_a_float"

        try:
            values = get_env_values(Config)
            # Should fall back to string values on conversion errors
            assert values == {"count": "not_a_number", "ratio": "not_a_float"}
        finally:
            del os.environ["APP_COUNT"]
            del os.environ["APP_RATIO"]
