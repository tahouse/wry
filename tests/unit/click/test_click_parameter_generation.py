"""Test Click parameter generation from Pydantic models."""

from typing import Annotated

import click
from pydantic import BaseModel, Field

from wry import AutoOption, generate_click_parameters
from wry.click_integration import _extract_predicate_description


class TestClickParameterGeneration:
    """Test generating Click parameters from model fields."""

    def test_predicate_description_extraction(self):
        """Test extracting descriptions from various predicate types."""

        # Named function
        def validate_positive(x: int) -> bool:
            return x > 0

        desc = _extract_predicate_description(validate_positive)
        assert desc == "predicate: validate_positive"

        # Lambda
        def lambda_func(x):
            return x > 0

        lambda_func.__name__ = "<lambda>"
        desc = _extract_predicate_description(lambda_func)
        assert "greater than 0" in desc or "> 0" in desc

        # Lambda with specific patterns
        def contains_at(s):
            return "@" in s

        contains_at.__name__ = "<lambda>"
        desc = _extract_predicate_description(contains_at)
        # Should return custom predicate since it's not a real lambda
        assert "custom predicate" in desc or "@" in desc

        def startswith_http(s):
            return s.startswith("http")

        startswith_http.__name__ = "<lambda>"
        desc = _extract_predicate_description(startswith_http)
        # Should return custom predicate since it's not a real lambda
        assert "custom predicate" in desc or "http" in desc

    def test_generate_parameters_with_complex_types(self):
        """Test parameter generation for complex field types."""

        class Config(BaseModel):
            # List type
            tags: Annotated[list[str], AutoOption] = Field(default_factory=list)
            # Dict type
            settings: Annotated[dict[str, str], AutoOption] = Field(default_factory=dict)
            # Optional
            optional_value: Annotated[str | None, AutoOption] = None

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Check parameters were generated
        assert any(p.name == "tags" for p in cmd.params)
        assert any(p.name == "settings" for p in cmd.params)
        assert any(p.name == "optional_value" for p in cmd.params)

    def test_generate_parameters_respects_field_metadata(self):
        """Test that field metadata is used in parameter generation."""

        class Config(BaseModel):
            # Required field
            api_key: Annotated[str, AutoOption]
            # Field with constraints
            port: Annotated[int, AutoOption] = Field(default=8080, ge=1, le=65535)

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Find the port parameter
        port_param = next(p for p in cmd.params if p.name == "port")
        assert port_param.default == 8080
        # Help should include constraints
        assert "1" in port_param.help or "65535" in port_param.help

    def test_show_env_vars_callback(self):
        """Test the --show-env-vars callback functionality."""

        class Config(BaseModel):
            env_prefix: str = "APP_"
            database_url: str = "postgresql://localhost/db"
            api_key: str

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Find the show-env-vars option
        show_env_param = next((p for p in cmd.params if p.name == "show_env_vars"), None)
        assert show_env_param is not None
        assert show_env_param.is_eager
        assert show_env_param.expose_value is False
