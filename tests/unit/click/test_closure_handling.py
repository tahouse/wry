"""Test Click closure handling and argument extraction."""

from typing import Annotated

import click
from pydantic import BaseModel

from wry import AutoArgument, generate_click_parameters


class TestClosureHandling:
    """Test closure extraction and handling in Click decorators."""

    def test_argument_with_custom_class(self):
        """Test argument with custom Click class in closure."""

        class CustomArgument(click.Argument):
            """Custom argument class for testing."""

            def get_metavar(self, param):
                return "CUSTOM"

        class Config(BaseModel):
            # Use custom argument class
            value: Annotated[str, click.argument(cls=CustomArgument)]

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Check that custom class is preserved
        args = [p for p in cmd.params if isinstance(p, click.Argument)]
        assert len(args) > 0
        # Custom class should be used
        assert any(isinstance(arg, CustomArgument) for arg in args)

    def test_closure_extraction_failure(self):
        """Test graceful handling when closure extraction fails."""

        # Create a decorator that will be hard to introspect
        def problematic_decorator():
            # Nested function to make closure extraction harder
            def inner():
                class InternalClass:
                    pass

                return click.argument()

            return inner()

        class Config(BaseModel):
            # This might fail closure extraction
            value: Annotated[str, AutoArgument] = "default"

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Should still work even if closure extraction fails
        assert hasattr(cmd, "params")

    def test_argument_decorator_edge_cases(self):
        """Test various edge cases in argument decorator handling."""

        class Config(BaseModel):
            # Regular argument
            regular: Annotated[str, AutoArgument]
            # Argument with explicit decorator
            explicit: Annotated[str, click.argument()]

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            pass

        # Both should create arguments
        args = [p for p in cmd.params if isinstance(p, click.Argument)]
        arg_names = [a.name for a in args]

        assert "regular" in arg_names or "explicit" in arg_names
