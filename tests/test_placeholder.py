"""Basic tests for drycli placeholder functionality."""

from drycli import AutoOption, DryModel, coming_soon, generate_click_options


def test_coming_soon():
    """Test the coming_soon placeholder function."""
    result = coming_soon()
    assert isinstance(result, str)
    assert "DRY CLI is coming soon!" in result
    assert "🚧" in result


def test_placeholder_classes_exist():
    """Test that placeholder classes are importable."""
    # These are just placeholders, so we just test they exist
    assert DryModel is not None
    assert AutoOption is not None
    assert generate_click_options is not None


def test_package_metadata():
    """Test package metadata is accessible."""
    import drycli

    assert hasattr(drycli, "__version__")
    assert hasattr(drycli, "__author__")
    assert hasattr(drycli, "__email__")

    # Version is now dynamic from git tags, just check it exists and is a string
    assert isinstance(drycli.__version__, str)
    assert len(drycli.__version__) > 0
    assert drycli.__author__ == "Tyler House"
    assert drycli.__email__ == "26489166+tahouse@users.noreply.github.com"


def test_exports():
    """Test that all expected exports are available."""
    import drycli

    expected_exports = [
        "DryModel",
        "AutoOption",
        "AutoArgument",
        "generate_click_options",
        "ValueSource",
        "coming_soon",
    ]

    for export in expected_exports:
        assert hasattr(drycli, export), f"Missing export: {export}"
        assert export in drycli.__all__, f"Export {export} not in __all__"
