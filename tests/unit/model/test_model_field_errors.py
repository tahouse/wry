"""Test WryModel field error handling."""

import pytest
from pydantic import Field

from wry.core.model import WryModel


class TestFieldErrorHandling:
    """Test error handling for field operations."""

    def test_get_field_constraints_nonexistent_field(self):
        """Test getting constraints for a field that doesn't exist."""

        class Config(WryModel):
            name: str = "test"

        config = Config()

        with pytest.raises(AttributeError, match="Field 'missing' not found in model"):
            config.get_field_constraints("missing")

    def test_get_field_minimum_nonexistent_field(self):
        """Test getting minimum value for a field that doesn't exist."""

        class Config(WryModel):
            age: int = Field(default=25, ge=0)

        config = Config()

        with pytest.raises(AttributeError, match="Field 'missing' not found in model"):
            config.get_field_minimum("missing")

    def test_get_field_maximum_nonexistent_field(self):
        """Test getting maximum value for a field that doesn't exist."""

        class Config(WryModel):
            score: int = Field(default=50, le=100)

        config = Config()

        with pytest.raises(AttributeError, match="Field 'missing' not found in model"):
            config.get_field_maximum("missing")

    def test_get_field_default_nonexistent_field(self):
        """Test getting default value for a field that doesn't exist."""

        class Config(WryModel):
            name: str = "default"

        config = Config()

        with pytest.raises(AttributeError, match="Field 'missing' not found in model"):
            config.get_field_default("missing")
