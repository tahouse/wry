"""Test closure extraction error handling."""

from typing import Annotated

import click
from pydantic import BaseModel

from wry import generate_click_parameters


class TestClosureExtractionErrors:
    """Test error handling in closure variable extraction."""

    def test_closure_with_non_class_contents(self):
        """Test closure inspection when contents is not a class."""

        # Create a complex closure that might fail inspection
        def create_complex_decorator():
            # Closure variable that's not a class
            not_a_class = "string_value"

            def decorator():
                # Reference the closure variable
                _ = not_a_class
                return click.argument()

            return decorator()

        class Config(BaseModel):
            # Use the complex decorator
            value: Annotated[str, create_complex_decorator()]

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Should still create the command
        assert hasattr(cmd, "params")

    def test_closure_with_attribute_error(self):
        """Test handling of AttributeError during closure inspection."""

        # Create a problematic object in closure
        class ProblematicClass:
            def __getattr__(self, name):
                raise AttributeError(f"No attribute {name}")

        def create_problematic_decorator():
            cls = ProblematicClass()

            def decorator():
                _ = cls  # Reference in closure
                return click.argument()

            return decorator()

        class Config(BaseModel):
            value: Annotated[str, create_problematic_decorator()]

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Should handle the error gracefully
        assert hasattr(cmd, "params")

    def test_closure_inspection_general_exception(self):
        """Test general exception during closure inspection."""
        # Create a decorator that might cause issues
        import types

        # Create a function with modified closure
        def base_func():
            return click.argument()

        # Try to create a function with problematic closure
        modified_func = types.FunctionType(
            base_func.__code__,
            {"click": click},
            closure=(),  # Empty closure
        )

        class Config(BaseModel):
            value: Annotated[str, modified_func()]

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Should still work
        assert hasattr(cmd, "params")
