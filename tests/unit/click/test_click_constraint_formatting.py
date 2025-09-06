"""Test Click constraint formatting functions."""

import annotated_types
from pydantic import BaseModel, Field

from wry.click_integration import extract_constraint_text, format_constraint_text


class TestConstraintFormatting:
    """Test formatting of constraints for Click help text."""

    def test_format_interval_constraints(self):
        """Test formatting Interval constraints with various combinations."""
        # Test all combinations of gt/ge/lt/le
        result = format_constraint_text({"gt": 0, "lt": 100})
        assert result == ["> 0", "< 100"]

        result = format_constraint_text({"ge": 0, "le": 100})
        assert result == [">= 0", "<= 100"]

        result = format_constraint_text({"gt": 0, "le": 100})
        assert result == ["> 0", "<= 100"]

        result = format_constraint_text({"ge": 0, "lt": 100})
        assert result == [">= 0", "< 100"]

        # Single constraint
        result = format_constraint_text({"gt": 0})
        assert result == ["> 0"]

    def test_format_multiple_of_constraint(self):
        """Test formatting MultipleOf constraints."""
        result = format_constraint_text({"multiple_of": 5})
        assert result == ["multiple of 5"]

        result = format_constraint_text({"multiple_of": 0.1})
        assert result == ["multiple of 0.1"]

    def test_extract_constraint_from_interval_metadata(self):
        """Test extracting constraints from Interval metadata."""
        # Test the constraint object directly
        interval = annotated_types.Interval(ge=0, le=100)
        result = extract_constraint_text(interval)
        assert result == ">= 0 AND <= 100"

    def test_extract_constraint_from_multiple_of_metadata(self):
        """Test extracting constraints from MultipleOf metadata."""
        multiple_of = annotated_types.MultipleOf(10)
        result = extract_constraint_text(multiple_of)
        assert result == "multiple of 10"

    def test_extract_constraint_from_predicate(self):
        """Test extracting constraints from Predicate metadata."""

        def is_even(x: int) -> bool:
            return x % 2 == 0

        predicate = annotated_types.Predicate(is_even)
        result = extract_constraint_text(predicate)
        assert result == "predicate: is_even"

    def test_extract_constraint_from_grouped_metadata(self):
        """Test extracting constraints from GroupedMetadata."""
        # GroupedMetadata is a Protocol, not instantiable
        # Test with individual constraints instead
        ge_constraint = annotated_types.Ge(0)
        le_constraint = annotated_types.Le(100)
        mult_constraint = annotated_types.MultipleOf(5)

        # Test each individually
        assert extract_constraint_text(ge_constraint) == ">= 0"
        assert extract_constraint_text(le_constraint) == "<= 100"
        assert extract_constraint_text(mult_constraint) == "multiple of 5"

    def test_field_constraints_with_format_constraint_text(self):
        """Test formatting constraints extracted from Field()."""
        from wry.core.field_utils import extract_field_constraints

        class Model(BaseModel):
            # Field with multiple constraints
            value: int = Field(ge=0, le=100, multiple_of=5)

        field = Model.model_fields["value"]
        constraints = extract_field_constraints(field)
        result = format_constraint_text(constraints)

        # Should format all constraints
        assert ">= 0" in result
        assert "<= 100" in result
        assert "multiple of 5" in result
