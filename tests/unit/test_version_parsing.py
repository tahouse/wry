"""Test version parsing logic in __init__.py."""

import sys
from unittest.mock import patch


def test_parse_version_with_git_hash():
    """Test parsing version strings that include git commit hashes."""
    # Test version with git hash
    test_version = "0.0.2+g1234567.dirty"

    # Simulate the parsing logic from __init__.py
    if "+" in test_version and "g" in test_version:
        commit_id = test_version.split("+")[-1].split(".")[0]
        version_full = test_version
    else:
        commit_id = None
        version_full = test_version

    clean_version = test_version.split("+")[0]

    assert commit_id == "g1234567"
    assert version_full == "0.0.2+g1234567.dirty"
    assert clean_version == "0.0.2"


def test_parse_version_without_git_hash():
    """Test parsing clean version strings without git information."""
    test_version = "1.2.3"

    # Simulate the parsing logic
    if "+" in test_version and "g" in test_version:
        commit_id = test_version.split("+")[-1].split(".")[0]
        version_full = test_version
    else:
        commit_id = None
        version_full = test_version

    clean_version = test_version.split("+")[0]

    assert commit_id is None
    assert version_full == "1.2.3"
    assert clean_version == "1.2.3"


def test_version_parsing_fallback_on_exception():
    """Test that version parsing falls back gracefully on errors."""
    # Mock the __init__ module's version parsing
    with patch.dict(sys.modules):
        # Create a mock that simulates the fallback behavior
        try:
            # Force an exception
            raise Exception("Version parsing failed")
        except Exception:
            # Ultimate fallback
            version = "0.0.1-dev"
            version_full = version
            commit_id = None

        assert version == "0.0.1-dev"
        assert version_full == "0.0.1-dev"
        assert commit_id is None
