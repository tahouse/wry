"""Test __init__.py functionality."""

import pytest


class TestVersionHandling:
    """Test version handling in __init__.py."""

    def test_version_import_success(self):
        """Test successful version import."""
        import wry

        # Should have version attributes
        assert hasattr(wry, "__version__")
        assert hasattr(wry, "__version_full__")
        assert hasattr(wry, "__commit_id__")

        # Version should be a string
        assert isinstance(wry.__version__, str)
        # Version should be semantic
        assert len(wry.__version__.split(".")) >= 3

    def test_version_parsing_with_git_hash(self):
        """Test version parsing logic when git hash is present."""
        # Test the version parsing logic directly
        test_version = "1.2.3.dev4+g1234567"

        # Simulate the parsing logic from __init__.py
        if "+" in test_version and "g" in test_version:
            commit_id = test_version.split("+")[-1].split(".")[0]
            clean_version = test_version.split("+")[0]

            assert commit_id == "g1234567"
            assert clean_version == "1.2.3.dev4"

    def test_version_parsing_without_git_hash(self):
        """Test version parsing logic without git hash."""
        # Test the parsing logic directly
        test_version = "1.2.3"

        # Simulate the parsing logic from __init__.py
        if "+" in test_version and "g" in test_version:
            commit_id = test_version.split("+")[-1].split(".")[0]
        else:
            commit_id = None

        assert commit_id is None

    def test_version_attributes_consistency(self):
        """Test that version attributes are consistent."""
        import wry

        # __version__ should be clean (no git hash)
        assert "+" not in wry.__version__

        # __version_full__ should contain __version__
        assert wry.__version__ in wry.__version_full__

        # If there's a commit_id, it should be in version_full
        if wry.__commit_id__:
            assert wry.__commit_id__ in wry.__version_full__

    def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases work."""
        import wry

        # AutoOption should be an alias for AutoClickParameter.OPTION
        assert wry.AutoOption == wry.AutoClickParameter.OPTION

        # AutoArgument should be an alias for AutoClickParameter.ARGUMENT
        assert wry.AutoArgument == wry.AutoClickParameter.ARGUMENT

        # We removed backward compatibility aliases
        # generate_click_options is no longer available
        assert not hasattr(wry, "generate_click_options")

    def test_auto_dry_model_imports(self):
        """Test that AutoWryModel is properly imported."""
        import wry

        # Should have AutoWryModel
        assert hasattr(wry, "AutoWryModel")
        assert hasattr(wry, "create_auto_model")

        # Should be callable
        assert callable(wry.create_auto_model)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
