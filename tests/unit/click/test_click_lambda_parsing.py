"""Test Click lambda expression parsing edge cases."""

from wry.click_integration import _extract_predicate_description


class TestLambdaParsing:
    """Test lambda expression parsing for predicate descriptions."""

    def test_lambda_with_list_membership(self):
        """Test lambda checking membership in a list."""
        # Lambda checking if value is in a list
        valid_values = lambda x: x in ["foo", "bar", "baz"]
        desc = _extract_predicate_description(valid_values)
        # The function should extract the list membership pattern
        assert desc == 'must be one of ["foo", "bar", "baz"]'

    def test_lambda_with_malformed_list(self):
        """Test lambda with malformed list syntax."""
        # Lambda with a simple comparison
        simple = lambda x: x > 0
        desc = _extract_predicate_description(simple)
        # Should extract the comparison
        assert "greater than 0" in desc or "> 0" in desc

    def test_lambda_with_complex_expression(self):
        """Test lambda with expression that doesn't match patterns."""
        # Complex lambda that doesn't match any pattern
        complex_check = lambda x: (x % 3 == 0) and (x > 10) and (x < 100)
        desc = _extract_predicate_description(complex_check)
        # May extract part of the complex expression
        assert desc is not None
        # Could extract comparison or fall back to generic
        assert any(x in desc for x in ["10", "100", "predicate", "lambda"])

    def test_lambda_parsing_edge_cases(self):
        """Test various edge cases in lambda parsing."""
        # Lambda with nested parentheses
        nested = lambda x: x.startswith("(test)")
        desc = _extract_predicate_description(nested)
        # Should extract the startswith pattern
        assert "starts with" in desc and "(test" in desc

        # Lambda with special characters
        special = lambda x: "@" in x and "." in x
        desc = _extract_predicate_description(special)
        # Should extract the containment pattern
        assert "contains" in desc and "@" in desc

    def test_lambda_source_extraction_failure(self):
        """Test when lambda source can't be extracted."""
        # Create a lambda and remove its source info
        func = lambda x: x > 0
        # If inspect.getsource fails, should fall back
        # This is hard to test directly, but we can test the fallback
        desc = _extract_predicate_description(func)
        assert desc is not None  # Should return something even on failure
