"""Test Click decorator edge cases."""

from typing import Annotated

import click
from pydantic import BaseModel

from wry import AutoOption, generate_click_parameters


class TestDecoratorEdgeCases:
    """Test edge cases in Click decorator handling."""

    def test_generate_parameters_with_no_annotated_fields(self):
        """Test decorator with model that has no Annotated fields."""

        class SimpleModel(BaseModel):
            name: str = "default"
            value: int = 0

        @click.command()
        @generate_click_parameters(SimpleModel)
        def cmd(**kwargs):
            pass

        # Should still work but not add any parameters
        assert hasattr(cmd, "params")
        # No parameters should be added for non-annotated fields
        param_names = [p.name for p in cmd.params]
        assert "name" not in param_names
        assert "value" not in param_names

    def test_generate_parameters_handles_field_errors(self):
        """Test decorator handles errors in field processing."""

        class ProblematicModel(BaseModel):
            # Valid field
            good: Annotated[str, AutoOption] = "default"
            # Field with complex type that might cause issues
            complex_field: Annotated[dict[str, list[int]], AutoOption] = {}

        @click.command()
        @generate_click_parameters(ProblematicModel)
        def cmd(**kwargs):
            pass

        # Should process what it can
        param_names = [p.name for p in cmd.params]
        assert "good" in param_names
        # Complex field might be skipped or handled

    def test_decorator_preserves_function_attributes(self):
        """Test that decorator preserves original function attributes."""

        @click.command()
        @generate_click_parameters(BaseModel)
        def cmd(**kwargs):
            """Command docstring."""
            return "result"

        # Should preserve docstring and name
        assert cmd.__doc__ == "Command docstring."
        assert "cmd" in cmd.name

    def test_model_with_special_field_names(self):
        """Test model with field names that need special handling."""

        class SpecialNamesModel(BaseModel):
            # Field names that might conflict or need escaping
            help: Annotated[str, AutoOption] = "default"
            type: Annotated[str, AutoOption] = "default"
            default: Annotated[str, AutoOption] = "default"

        @click.command()
        @generate_click_parameters(SpecialNamesModel)
        def cmd(**kwargs):
            pass

        # Should handle special names appropriately
        param_names = [p.name for p in cmd.params]
        # Click might modify these names to avoid conflicts
