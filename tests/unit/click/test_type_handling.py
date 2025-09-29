"""Test Click type handling for various field types."""

from typing import Annotated

import click
from pydantic import BaseModel

from wry import AutoOption, generate_click_parameters


class TestClickTypeHandling:
    """Test how different Python types are mapped to Click types."""

    def test_optional_type_extraction(self):
        """Test extraction of non-None type from Optional."""

        class Config(BaseModel):
            # Optional types
            optional_int: Annotated[int | None, AutoOption] = None
            optional_float: Annotated[float | None, AutoOption] = None
            optional_bool: Annotated[bool | None, AutoOption] = None
            optional_str: Annotated[str | None, AutoOption] = None

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Check that correct Click types are assigned
        params_by_name = {p.name: p for p in cmd.params}

        # INT type for optional int
        assert "optional_int" in params_by_name
        assert params_by_name["optional_int"].type == click.INT

        # FLOAT type for optional float
        assert "optional_float" in params_by_name
        assert params_by_name["optional_float"].type == click.FLOAT

        # BOOL type for optional bool
        assert "optional_bool" in params_by_name
        assert isinstance(params_by_name["optional_bool"].type, click.types.BoolParamType)

        # String is Click's default, might not have explicit type
        assert "optional_str" in params_by_name

    def test_basic_type_mapping(self):
        """Test mapping of basic Python types to Click types."""

        class Config(BaseModel):
            int_field: Annotated[int, AutoOption] = 0
            float_field: Annotated[float, AutoOption] = 0.0
            bool_field: Annotated[bool, AutoOption] = False
            str_field: Annotated[str, AutoOption] = ""

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        params_by_name = {p.name: p for p in cmd.params}

        assert params_by_name["int_field"].type == click.INT
        assert params_by_name["float_field"].type == click.FLOAT
        assert isinstance(params_by_name["bool_field"].type, click.types.BoolParamType)
        # String might use default or click.STRING

    def test_custom_type_handling(self):
        """Test handling of custom types that aren't built-in."""
        from pathlib import Path

        class Config(BaseModel):
            # Custom type (not int/float/bool/str)
            path_field: Annotated[Path, AutoOption] = Path(".")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        params_by_name = {p.name: p for p in cmd.params}

        # Custom types should be passed through
        assert "path_field" in params_by_name
        # Path gets converted to Click's STRING type
        param_type = params_by_name["path_field"].type
        assert str(param_type) == "STRING"  # Click's string type
