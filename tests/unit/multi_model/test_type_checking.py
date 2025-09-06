"""Test TYPE_CHECKING in multi_model module."""

import sys


class TestMultiModelTypeChecking:
    """Test TYPE_CHECKING imports in multi_model."""

    def test_multi_model_imports_work(self):
        """Test that multi_model module imports correctly."""
        # Remove from cache if present
        if "wry.multi_model" in sys.modules:
            del sys.modules["wry.multi_model"]

        # Import the module directly

        # Also check we can import functions from wry
        from wry import create_models, multi_model, singleton_option, split_kwargs_by_model

        # Verify the functions are callable
        assert callable(multi_model)
        assert callable(split_kwargs_by_model)
        assert callable(create_models)
        assert callable(singleton_option)
