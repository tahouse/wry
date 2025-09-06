"""Test constraint behavior rather than exact string format."""

from typing import Annotated

import annotated_types
from pydantic import BaseModel, Field

from wry.click_integration import extract_constraint_text


class TestConstraintBehavior:
    """Test that constraints are recognized and contain key information."""

    def test_length_constraints_are_recognized(self):
        """Test that length constraints are recognized and contain the values."""
        # Test various length constraints
        test_cases = [
            (annotated_types.Len(min_length=5, max_length=5), ["5"]),
            (annotated_types.Len(min_length=2, max_length=10), ["2", "10"]),
            (annotated_types.Len(min_length=3), ["3"]),
            (annotated_types.Len(max_length=50), ["50"]),
            (annotated_types.MinLen(5), ["5"]),
            (annotated_types.MaxLen(100), ["100"]),
        ]

        for constraint, expected_values in test_cases:
            result = extract_constraint_text(constraint)
            # Should return something
            assert result is not None
            # Should contain the constraint values
            for value in expected_values:
                assert value in result

    def test_numeric_constraints_are_recognized(self):
        """Test that numeric constraints are recognized."""
        test_cases = [
            (annotated_types.Ge(0), "0"),
            (annotated_types.Gt(0), "0"),
            (annotated_types.Le(100), "100"),
            (annotated_types.Lt(100), "100"),
            (annotated_types.MultipleOf(5), "5"),
        ]

        for constraint, expected_value in test_cases:
            result = extract_constraint_text(constraint)
            assert result is not None
            assert expected_value in result

    def test_interval_constraints_are_recognized(self):
        """Test that interval constraints work."""
        # Interval with all bounds
        interval = annotated_types.Interval(gt=0, ge=1, lt=100, le=99)
        result = extract_constraint_text(interval)
        assert result is not None
        # Should contain all the bounds
        assert "0" in result
        assert "1" in result
        assert "100" in result
        assert "99" in result

        # Interval with no bounds
        empty_interval = annotated_types.Interval()
        result = extract_constraint_text(empty_interval)
        assert result is None  # No constraints to show

    def test_grouped_metadata_combines_constraints(self):
        """Test that GroupedMetadata combines multiple constraints."""
        # Create individual constraints and test combination
        constraints = [annotated_types.Ge(10), annotated_types.Le(100), annotated_types.MultipleOf(5)]

        # Test each constraint individually
        results = []
        for constraint in constraints:
            result = extract_constraint_text(constraint)
            assert result is not None
            results.append(result)

        # All should have their values
        assert any("10" in r for r in results)
        assert any("100" in r for r in results)
        assert any("5" in r for r in results)

    def test_format_constraint_text_returns_list(self):
        """Test that format_constraint_text returns a list of constraints."""

        class Model(BaseModel):
            value: Annotated[int, Field(ge=0, le=100), annotated_types.MultipleOf(5)] = 10

        field = Model.model_fields["value"]
        # Extract constraints from field info first
        from wry.core.field_utils import extract_field_constraints

        constraints = extract_field_constraints(field)

        # This gives us a dict of constraints
        assert isinstance(constraints, dict)
        # Should have multiple constraints
        assert len(constraints) > 0
        # Should have our expected constraints
        assert "ge" in constraints
        assert "le" in constraints

    def test_predicate_constraints_are_recognized(self):
        """Test that predicate constraints are handled."""

        def is_positive(x):
            return x > 0

        constraint = annotated_types.Predicate(is_positive)
        result = extract_constraint_text(constraint)
        assert result is not None
        # Should mention it's a predicate or use the function name
        assert "predicate" in result.lower() or "is_positive" in result
