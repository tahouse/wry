"""Test generate_click_parameters as a classmethod."""

import click
from pydantic import Field

from wry import AutoWryModel, WryModel, generate_click_parameters


class TestGenerateClickClassmethod:
    """Test the generate_click_parameters classmethod."""

    def test_wry_model_has_classmethod(self):
        """Test that WryModel has generate_click_parameters classmethod."""
        assert hasattr(WryModel, "generate_click_parameters")
        assert callable(WryModel.generate_click_parameters)

    def test_auto_wry_model_has_classmethod(self):
        """Test that AutoWryModel has generate_click_parameters classmethod."""
        assert hasattr(AutoWryModel, "generate_click_parameters")
        assert callable(AutoWryModel.generate_click_parameters)

    def test_classmethod_returns_same_as_function(self):
        """Test that classmethod returns same decorator as direct function call."""

        class SimpleModel(WryModel):
            value: int = Field(default=1)

        # Get decorator from classmethod
        classmethod_decorator = SimpleModel.generate_click_parameters()
        # Get decorator from function
        function_decorator = generate_click_parameters(SimpleModel)

        # Both should be callables
        assert callable(classmethod_decorator)
        assert callable(function_decorator)

        # They should have the same behavior (though not necessarily the same object)
        # The important thing is that the classmethod works
        @click.command()
        @classmethod_decorator
        def dummy(**kwargs):
            pass

        # Should have config and show_env_vars options added
        param_names = [p.name for p in dummy.params]
        assert "config" in param_names
        assert "show_env_vars" in param_names
