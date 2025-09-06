"""Test Click length constraint formatting."""

import annotated_types

from wry.click_integration import extract_constraint_text


class TestLengthConstraints:
    """Test length constraint handling."""

    def test_len_constraint_equal_length(self):
        """Test Len constraint when min and max are equal."""
        # Equal min and max length
        len_constraint = annotated_types.Len(min_length=5, max_length=5)
        result = extract_constraint_text(len_constraint)
        # Len is a GroupedMetadata containing MinLen and MaxLen
        assert result == "min length 5 AND max length 5"

    def test_len_constraint_range(self):
        """Test Len constraint with different min and max."""
        len_constraint = annotated_types.Len(min_length=2, max_length=10)
        result = extract_constraint_text(len_constraint)
        assert result == "min length 2 AND max length 10"

    def test_len_constraint_min_only(self):
        """Test Len constraint with only minimum."""
        len_constraint = annotated_types.Len(min_length=3)
        result = extract_constraint_text(len_constraint)
        assert result == "min length 3"

    def test_len_constraint_max_only(self):
        """Test Len constraint with only maximum."""
        len_constraint = annotated_types.Len(max_length=50)
        result = extract_constraint_text(len_constraint)
        assert result == "max length 50"

    def test_min_len_constraint(self):
        """Test MinLen constraint."""
        min_len = annotated_types.MinLen(5)
        result = extract_constraint_text(min_len)
        assert result == "min length 5"

    def test_max_len_constraint(self):
        """Test MaxLen constraint."""
        max_len = annotated_types.MaxLen(100)
        result = extract_constraint_text(max_len)
        assert result == "max length 100"
