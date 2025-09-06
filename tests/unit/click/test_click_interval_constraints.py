"""Test Click interval constraint extraction and formatting."""

import annotated_types

from wry.click_integration import extract_constraint_text


class TestIntervalConstraints:
    """Test interval constraint handling."""

    def test_interval_with_all_bounds(self):
        """Test interval with gt, ge, lt, le bounds."""
        # Interval with all bounds set
        interval = annotated_types.Interval(gt=0, ge=1, lt=100, le=99)
        result = extract_constraint_text(interval)

        # Should format all bounds
        assert "> 0" in result
        assert ">= 1" in result
        assert "< 100" in result
        assert "<= 99" in result

    def test_interval_with_partial_bounds(self):
        """Test interval with only some bounds set."""
        # Only lower bounds
        interval = annotated_types.Interval(ge=0)
        result = extract_constraint_text(interval)
        assert result == ">= 0"

        # Only upper bounds
        interval = annotated_types.Interval(le=100)
        result = extract_constraint_text(interval)
        assert result == "<= 100"

        # Mixed bounds
        interval = annotated_types.Interval(gt=0, lt=100)
        result = extract_constraint_text(interval)
        assert "> 0" in result
        assert "< 100" in result

    def test_interval_with_no_bounds(self):
        """Test interval with no bounds returns None."""
        interval = annotated_types.Interval()
        result = extract_constraint_text(interval)
        assert result is None
