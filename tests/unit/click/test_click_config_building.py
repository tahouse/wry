"""Test Click configuration building functions."""

import click
from pydantic import BaseModel

from wry.click_integration import build_config_with_sources
from wry.core.model import WryModel


class TestConfigBuilding:
    """Test configuration building from Click context."""

    def test_build_config_with_sources_no_valid_class(self):
        """Test build_config_with_sources without valid config class."""
        try:
            # Call without any valid config class
            build_config_with_sources(None, None)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "config_class must be provided" in str(e)

    def test_build_config_with_sources_class_as_ctx(self):
        """Test when config class is passed as first argument."""

        class Config(BaseModel):
            name: str = "default"

        # Pass config class as first arg (ctx position)
        result = build_config_with_sources(Config, None, name="test")
        assert isinstance(result, Config)
        assert result.name == "test"

    def test_build_config_with_dry_model(self):
        """Test building WryModel with sources."""

        @click.command()
        def cmd():
            pass

        ctx = click.Context(cmd)

        class Config(WryModel):
            value: str = "default"

        # Build with context
        result = build_config_with_sources(ctx, Config, value="from_cli")
        assert isinstance(result, Config)
        assert result.value == "from_cli"
        # Should have source tracking
        if hasattr(result, "source"):
            assert result.source.value.value == "cli"
