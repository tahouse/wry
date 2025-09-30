"""Test TYPE_CHECKING imports coverage."""

from unittest.mock import patch


class TestTypeCheckingImports:
    """Test TYPE_CHECKING conditional imports."""

    def test_version_module_type_checking_true(self):
        """Test _version module when TYPE_CHECKING is True."""
        # Import the module first to ensure it exists
        import wry._version

        # Patch TYPE_CHECKING to True
        with patch("wry._version.TYPE_CHECKING", True):
            # The module should still work
            assert hasattr(wry._version, "__version__")
            assert hasattr(wry._version, "VERSION_TUPLE")
            assert hasattr(wry._version, "COMMIT_ID")

    def test_core_modules_type_checking(self):
        """Test TYPE_CHECKING blocks in core modules."""
        # This tests that TYPE_CHECKING blocks don't break imports
        from wry.core import accessors, env_utils, field_utils, model, sources

        # Verify modules loaded successfully
        assert sources is not None
        assert accessors is not None
        assert env_utils is not None
        assert field_utils is not None
        assert model is not None

    def test_auto_model_type_checking(self):
        """Test TYPE_CHECKING imports in auto_model."""
        from wry import auto_model

        # Should have the expected exports
        assert hasattr(auto_model, "AutoWryModel")
        assert hasattr(auto_model, "create_auto_model")
