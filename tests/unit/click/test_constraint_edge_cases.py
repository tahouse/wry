"""Test edge cases in constraint formatting."""

from typing import Annotated

import annotated_types
from pydantic import BaseModel, Field

from wry import AutoOption
from wry.click_integration import extract_constraint_text, format_constraint_text


class TestConstraintEdgeCases:
    """Test edge cases in constraint text extraction and formatting."""

    def test_interval_with_all_bounds(self):
        """Test interval constraint with all bounds specified."""
        # Create interval with all bounds
        constraint = annotated_types.Interval(gt=0, ge=1, lt=100, le=99)
        result = extract_constraint_text(constraint)

        # Should format all bounds
        assert result is not None
        assert "> 0" in result
        assert ">= 1" in result
        assert "< 100" in result
        assert "<= 99" in result

    def test_interval_with_no_bounds(self):
        """Test interval constraint with no bounds."""
        # Create interval with no bounds
        constraint = annotated_types.Interval()
        result = extract_constraint_text(constraint)

        # Should return None when no bounds
        assert result is None

    def test_len_constraint_equal_min_max(self):
        """Test Len constraint where min equals max."""
        # Exact length constraint
        constraint = annotated_types.Len(min_length=10, max_length=10)
        result = extract_constraint_text(constraint)

        assert result == "min length 10 AND max length 10"

    def test_len_constraint_range(self):
        """Test Len constraint with different min and max."""
        constraint = annotated_types.Len(min_length=5, max_length=20)
        result = extract_constraint_text(constraint)

        assert result == "min length 5 AND max length 20"

    def test_len_constraint_min_only(self):
        """Test Len constraint with only minimum."""
        constraint = annotated_types.Len(min_length=3)
        result = extract_constraint_text(constraint)

        assert result == "min length 3"

    def test_len_constraint_max_only(self):
        """Test Len constraint with only maximum."""
        constraint = annotated_types.Len(max_length=50)
        result = extract_constraint_text(constraint)

        assert result == "max length 50"

    def test_format_constraint_text_with_mixed_constraints(self):
        """Test format_constraint_text with various constraint types."""

        class Model(BaseModel):
            # Multiple constraints
            value: Annotated[int, Field(ge=0, le=100), annotated_types.MultipleOf(5), AutoOption] = 10

        field = Model.model_fields["value"]
        # Extract constraints from field
        from wry.core.field_utils import extract_field_constraints

        constraints_dict = extract_field_constraints(field)
        # Format constraint text
        constraints = format_constraint_text(constraints_dict)

        # Should format all constraints
        assert isinstance(constraints, list)
        assert any("0" in c and "100" in c for c in constraints)
        assert any("multiple of 5" in c for c in constraints)
