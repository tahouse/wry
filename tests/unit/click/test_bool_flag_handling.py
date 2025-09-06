"""Test Click boolean flag handling."""

from typing import Annotated

import click
from pydantic import BaseModel

from wry import AutoOption, generate_click_parameters


class TestBoolFlagHandling:
    """Test how boolean fields are converted to Click flags."""

    def test_bool_field_becomes_flag(self):
        """Test that boolean fields become Click flags."""

        class Config(BaseModel):
            # Regular bool
            enabled: Annotated[bool, AutoOption] = False
            # Optional bool
            verbose: Annotated[bool | None, AutoOption] = None

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        params_by_name = {p.name: p for p in cmd.params}

        # Bool fields should be flags
        assert "enabled" in params_by_name
        enabled_param = params_by_name["enabled"]
        assert enabled_param.is_flag
        # Flags don't show defaults
        assert not hasattr(enabled_param, "show_default") or not enabled_param.show_default

        # Optional bool should also be a flag
        assert "verbose" in params_by_name
        verbose_param = params_by_name["verbose"]
        assert verbose_param.is_flag

    def test_bool_with_union_type(self):
        """Test boolean in Union types."""

        class Config(BaseModel):
            # Union with bool
            flag: Annotated[bool | None, AutoOption] = None

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        params_by_name = {p.name: p for p in cmd.params}

        # Should still recognize as bool and make it a flag
        assert "flag" in params_by_name
        assert params_by_name["flag"].is_flag
