"""Test TYPE_CHECKING imports coverage."""


class TestTypeCheckingImports:
    """Test TYPE_CHECKING conditional imports."""

    def test_version_module_importable(self):
        """Test _version module can be imported and has version info."""
        import wry._version

        # The auto-generated module should always have version info
        assert hasattr(wry._version, "__version__")
        assert isinstance(wry._version.__version__, str)

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
