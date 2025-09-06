"""Test WryModel Click context handling."""

import os
from typing import ClassVar

import pytest
from click import Context, command, option

from wry.core.model import WryModel
from wry.core.sources import TrackedValue, ValueSource


class TestClickContextHandling:
    """Test Click context integration and parameter handling."""

    def test_from_click_context_with_params_in_context(self):
        """Test that ctx.params values are properly used."""

        @command()
        @option("--name", default="test")
        def cmd(name: str):
            pass

        ctx = Context(cmd)
        ctx.params = {"name": "from_params"}

        class Config(WryModel):
            name: str = "default"

        config = Config.from_click_context(ctx)
        assert config.name == "from_params"

    def test_from_click_context_kwargs_override_params(self):
        """Test that kwargs override ctx.params values."""

        @command()
        @option("--name", default="default")
        @option("--value", type=int, default=10)
        def cmd(name: str, value: int):
            pass

        ctx = Context(cmd)
        ctx.params = {"name": "from_params", "value": 99}

        class Config(WryModel):
            name: str = "default"
            value: int = 0

        # kwargs should override ctx.params
        config = Config.from_click_context(ctx, name="from_kwargs")

        assert config.name == "from_kwargs"  # from kwargs
        assert config.value == 99  # from ctx.params

    def test_from_click_context_without_context_raises_error(self):
        """Test that calling without context raises appropriate error."""

        class Config(WryModel):
            name: str = "default"

        with pytest.raises(RuntimeError, match="No Click context available"):
            Config.from_click_context(None)

    def test_from_click_context_strict_mode_rejects_extra_fields(self):
        """Test strict mode validation of extra fields."""

        @command()
        def cmd():
            pass

        ctx = Context(cmd)

        class Config(WryModel):
            name: str = "default"

        with pytest.raises(ValueError, match="Extra fields not allowed"):
            Config.from_click_context(ctx, strict=True, name="test", extra_field="not_allowed")

    def test_source_tracking_with_tracked_values(self):
        """Test that TrackedValue objects preserve their source information."""

        @command()
        def cmd():
            pass

        _ = Context(cmd)

        class Config(WryModel):
            value: int = 10

        config_data = {"value": TrackedValue(42, ValueSource.CLI)}
        config = Config.create_with_sources(config_data)

        assert config.value == 42
        assert config.source.value.value == "cli"

    def test_mixed_source_tracking(self):
        """Test tracking multiple sources in a single configuration."""

        @command()
        def cmd():
            pass

        ctx = Context(cmd)

        class Config(WryModel):
            env_prefix: ClassVar[str] = "TEST_"
            cli_val: str = "default"
            env_val: str = "default"

        os.environ["TEST_ENV_VAL"] = "from_env"

        try:
            config = Config.from_click_context(ctx, cli_val="from_cli")

            assert config.cli_val == "from_cli"
            assert config.env_val == "from_env"

            assert config.source.cli_val.value == "cli"
            assert config.source.env_val.value == "env"

        finally:
            del os.environ["TEST_ENV_VAL"]
