"""Test coverage gaps in sources.py module."""

from wry.core.sources import FieldWithSource, TrackedValue, ValueSource


class TestTrackedValueCoverage:
    """Test TrackedValue coverage gaps."""

    def test_tracked_value_repr(self):
        """Test TrackedValue repr method."""
        tv = TrackedValue("test", ValueSource.CLI)
        assert repr(tv) == "TrackedValue('test', cli)"

        tv2 = TrackedValue(42, ValueSource.ENV)
        assert repr(tv2) == "TrackedValue(42, env)"


class TestFieldWithSourceCoverage:
    """Test FieldWithSource coverage gaps."""

    def test_field_with_source_eq_with_non_field(self):
        """Test FieldWithSource equality with non-FieldWithSource values."""
        field = FieldWithSource("test", ValueSource.CLI)

        # Should compare value with non-FieldWithSource
        assert field == "test"
        assert not (field == "other")

        # Test with different types
        field_int = FieldWithSource(42, ValueSource.ENV)
        assert field_int == 42
        assert not (field_int == 43)
