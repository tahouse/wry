"""Test lambda parsing error handling."""

from wry.click_integration import _extract_predicate_description


class TestLambdaErrorHandling:
    """Test error handling in lambda expression parsing."""

    def test_lambda_with_indexerror_in_method_parsing(self):
        """Test handling of IndexError during method call parsing."""
        # Create lambda that will cause IndexError when parsing
        # This happens when split doesn't produce expected parts
        malformed_lambda = lambda x: x.startswith()  # Missing argument

        # Should handle gracefully - may extract partial pattern
        result = _extract_predicate_description(malformed_lambda)
        assert result is not None
        assert "starts" in result.lower()

    def test_lambda_with_valueerror_in_list_parsing(self):
        """Test handling of ValueError during list membership parsing."""
        # Lambda with complex list expression
        complex_list_lambda = lambda x: x in ["a", "b", "c"]

        # This should be handled gracefully
        result = _extract_predicate_description(complex_list_lambda)
        assert result == 'must be one of ["a", "b", "c"]'

    def test_lambda_with_complex_nested_expression(self):
        """Test lambda with complex nested expressions that might fail parsing."""
        # Complex lambda that might cause parsing issues
        complex_lambda = lambda x: (x.strip().lower().startswith("test") and len(x) > 5 and x not in ["test1", "test2"])

        result = _extract_predicate_description(complex_lambda)
        assert result is not None
        # Could extract something from the complex expression
        assert any(x in result.lower() for x in ["test", "5", "predicate", "lambda", "starts"])

    def test_lambda_with_missing_operator_value(self):
        """Test lambda where operator value extraction fails."""
        # Lambda where value after operator is complex
        lambda_with_complex_value = lambda x: x > (10 if True else 20)

        result = _extract_predicate_description(lambda_with_complex_value)
        assert result is not None
        # Should extract the comparison even with complex value
        assert "greater than" in result.lower() or ">" in result

    def test_lambda_string_containment_edge_case(self):
        """Test string containment pattern edge cases."""
        # Test " in x" pattern
        contains_lambda = lambda x: "test" in x
        result = _extract_predicate_description(contains_lambda)
        assert "contains" in result or "in" in result

    def test_lambda_with_empty_string_after_split(self):
        """Test lambda that produces empty string after splitting."""
        # Lambda that might produce empty parts
        edge_lambda = lambda x: x == ""

        result = _extract_predicate_description(edge_lambda)
        assert "==" in result or "equal" in result
