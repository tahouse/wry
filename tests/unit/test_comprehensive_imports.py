"""Comprehensive import test to ensure all modules load correctly."""

import sys
from importlib import import_module


class TestComprehensiveImports:
    """Test that all modules can be imported successfully."""

    def test_all_modules_importable(self):
        """Test importing all wry modules."""
        modules = [
            "wry",
            "wry.auto_model",
            "wry.click_integration",
            "wry.multi_model",
            "wry.core",
            "wry.core.accessors",
            "wry.core.env_utils",
            "wry.core.field_utils",
            "wry.core.model",
            "wry.core.sources",
        ]

        # Save original modules
        original_modules = {}
        for module_name in modules:
            if module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]

        try:
            for module_name in modules:
                # Remove from cache to force reimport
                if module_name in sys.modules:
                    del sys.modules[module_name]

                # Import module
                module = import_module(module_name)
                assert module is not None
        finally:
            # Restore original modules
            for module_name, module in original_modules.items():
                sys.modules[module_name] = module

    def test_all_public_exports_available(self):
        """Test that all public exports are available."""
        import wry

        # Main exports
        exports = [
            "WryModel",
            "AutoWryModel",
            "create_auto_model",
            "generate_click_parameters",
            "AutoOption",
            "AutoArgument",
            "AutoClickParameter",
            "ValueSource",
            "TrackedValue",
            "FieldWithSource",
            "multi_model",
            "create_models",
            "split_kwargs_by_model",
            "singleton_option",
        ]

        for export in exports:
            assert hasattr(wry, export), f"Missing export: {export}"

    def test_version_attributes(self):
        """Test version-related attributes."""
        import wry

        # Version attributes
        assert hasattr(wry, "__version__")
        assert isinstance(wry.__version__, str)
        assert wry.__version__  # Not empty

        # Version parsing worked
        assert hasattr(wry, "__version_full__")
        assert hasattr(wry, "__commit_id__")
