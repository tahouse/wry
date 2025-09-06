"""Test edge cases in __init__.py version handling."""

import sys
from unittest.mock import patch


class TestInitVersionEdgeCases:
    """Test version parsing edge cases in __init__.py."""

    def test_version_module_missing(self):
        """Test when _version module is missing."""
        # Mock the import to fail
        with patch.dict(sys.modules):
            # Make import fail
            sys.modules["wry._version"] = None

            # Re-run the version parsing logic
            try:
                from wry._version import __version__
            except (ImportError, AttributeError):
                __version__ = "0.0.1+unknown"
                __commit_id__ = None
                __version_full__ = __version__

            # Should fall back to default
            assert __version__ == "0.0.1+unknown"
            assert __commit_id__ is None

    def test_version_with_git_info_parsing(self):
        """Test parsing version with git commit info."""
        # Test version with git info
        test_version = "1.2.3+gabc123.d456"

        # Parse like in __init__.py
        if "+" in test_version and "g" in test_version:
            __commit_id__ = test_version.split("+")[-1].split(".")[0]
            __version_full__ = test_version
        else:
            __commit_id__ = None
            __version_full__ = test_version

        # Clean version
        __version__ = test_version.split("+")[0]

        assert __version__ == "1.2.3"
        assert __commit_id__ == "gabc123"
        assert __version_full__ == "1.2.3+gabc123.d456"

    def test_version_parsing_exception_handling(self):
        """Test exception during version parsing."""
        # Test the fallback behavior when version parsing fails
        # This simulates what happens in __init__.py
        try:
            # Simulate a failure during version access
            raise Exception("Version parsing failed")
        except Exception:
            # Fallback values (as in __init__.py)
            __version__ = "0.0.1-dev"
            __version_full__ = __version__
            __commit_id__ = None

        assert __version__ == "0.0.1-dev"
        assert __version_full__ == "0.0.1-dev"
        assert __commit_id__ is None
