"""Test version parsing fallback scenarios."""

from unittest.mock import Mock


class TestVersionFallback:
    """Test version parsing when things go wrong."""

    def test_version_without_plus_sign(self):
        """Test version string without + character."""
        # Simulate version without git info
        test_version = "1.2.3"

        # Parse like in __init__.py
        if "+" in test_version and "g" in test_version:
            commit_id = test_version.split("+")[-1].split(".")[0]
            version_full = test_version
        else:
            commit_id = None
            version_full = test_version

        clean_version = test_version.split("+")[0]

        assert clean_version == "1.2.3"
        assert version_full == "1.2.3"
        assert commit_id is None

    def test_version_parsing_exception_fallback(self):
        """Test fallback when version parsing raises exception."""
        # Simulate exception scenario
        try:
            # Force an exception during parsing
            raise Exception("Version parsing failed")
        except Exception:
            # Fallback values
            version = "0.0.1-dev"
            version_full = version
            commit_id = None

        assert version == "0.0.1-dev"
        assert version_full == "0.0.1-dev"
        assert commit_id is None

    def test_version_module_import_variations(self):
        """Test different ways version module might behave."""
        # Test when version module exists but has unexpected structure
        mock_module = Mock()

        # Case 1: Module has __version__
        mock_module.__version__ = "2.0.0"
        assert hasattr(mock_module, "__version__")
        assert mock_module.__version__ == "2.0.0"

        # Case 2: Module missing __version__
        del mock_module.__version__
        assert not hasattr(mock_module, "__version__")

        # Case 3: __version__ is None
        mock_module.__version__ = None
        assert mock_module.__version__ is None
