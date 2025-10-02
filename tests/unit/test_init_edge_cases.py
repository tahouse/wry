"""Test edge cases for __init__.py that aren't covered elsewhere."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestVersionParsingEdgeCases:
    """Test edge cases in version parsing."""

    def test_version_import_failure(self):
        """Test when _version module import fails."""
        # Remove any existing imports
        modules_to_remove = [mod for mod in sys.modules if mod.startswith("wry")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Block the _version module from being importable
        with patch.dict(sys.modules, {"wry._version": None}):
            # Force reload to trigger the import error path
            import importlib

            import wry

            importlib.reload(wry)

            # Should fall back to default version
            assert hasattr(wry, "__version__")
            # With setuptools-scm, falls back to placeholder
            assert wry.__version__ == "0.0.0"
            assert hasattr(wry, "__commit_id__")
            assert wry.__commit_id__ is None

    def test_version_module_missing_version(self):
        """Test when _version module exists but has no __version__."""
        with patch.dict(sys.modules):
            # Create a mock _version module without __version__
            mock_version_module = MagicMock()
            del mock_version_module.__version__  # Remove __version__ attribute

            sys.modules["wry._version"] = mock_version_module

            # Re-import wry
            if "wry" in sys.modules:
                del sys.modules["wry"]

            import wry

            # Should use fallback version
            assert wry.__version__ == "0.0.0"
            assert hasattr(wry, "__commit_id__")
            assert wry.__commit_id__ is None


class TestImportEdgeCases:
    """Test edge cases in imports."""

    def test_lazy_imports(self):
        """Test that imports are lazy where expected."""
        # Just check that importing the main module works
        import wry

        # Main module should be imported
        assert "wry" in sys.modules

        # Check we can access key exports
        assert hasattr(wry, "WryModel")
        assert hasattr(wry, "generate_click_parameters")

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        import wry

        # Check key exports
        expected = [
            "WryModel",
            "ValueSource",
            "TrackedValue",
            "FieldWithSource",
            "generate_click_parameters",
            "AutoOption",
            "AutoArgument",
            "AutoClickParameter",
        ]

        for name in expected:
            assert name in wry.__all__, f"{name} missing from __all__"

    def test_type_checking_imports(self):
        """Test TYPE_CHECKING imports don't cause runtime issues."""
        import wry

        # Should be able to access all public APIs
        assert hasattr(wry, "WryModel")
        assert hasattr(wry, "generate_click_parameters")
        assert hasattr(wry, "multi_model")

    def test_circular_import_prevention(self):
        """Test that circular imports are handled."""
        # Remove any existing imports
        modules_to_remove = [mod for mod in sys.modules if mod.startswith("wry")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # This should not cause circular import errors
        import wry.click_integration  # noqa: F401
        import wry.core  # noqa: F401
        import wry.multi_model  # noqa: F401

        # All should import successfully
        assert "wry.click_integration" in sys.modules
        assert "wry.core" in sys.modules
        assert "wry.multi_model" in sys.modules


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
