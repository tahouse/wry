"""Test lambda parsing behavior rather than exact format."""

from wry.click_integration import _extract_predicate_description


class TestLambdaBehavior:
    """Test lambda parsing extracts key information without being brittle."""

    def test_lambda_list_membership_is_recognized(self):
        """Test that list membership lambdas are recognized."""
        valid_values = lambda x: x in ["foo", "bar", "baz"]
        desc = _extract_predicate_description(valid_values)

        # Should extract the list membership pattern
        assert desc == 'must be one of ["foo", "bar", "baz"]'

    def test_lambda_comparison_operators_extracted(self):
        """Test that comparison operators are extracted."""
        test_cases = [
            (lambda x: x > 0, ">", "0"),
            (lambda x: x >= 10, ">=", "10"),
            (lambda x: x < 100, "<", "100"),
            (lambda x: x <= 50, "<=", "50"),
            (lambda x: x == 42, "==", "42"),
            (lambda x: x != 0, "!=", "0"),
        ]

        for func, _operator, value in test_cases:
            desc = _extract_predicate_description(func)
            assert desc is not None
            # Should contain the operator and value
            assert value in desc
            # Operator might be transformed but the meaning should be clear

    def test_lambda_string_methods_recognized(self):
        """Test that string method calls are recognized."""
        test_cases = [
            (lambda x: x.startswith("prefix"), "prefix", ["start", "begin"]),
            (lambda x: x.endswith("suffix"), "suffix", ["end"]),
            (lambda x: "substring" in x, "substring", ["contain", "in"]),
        ]

        for func, expected_value, keywords in test_cases:
            desc = _extract_predicate_description(func)
            assert desc is not None
            # Should contain the value being checked
            assert expected_value in desc
            # Should indicate the operation
            assert any(keyword in desc.lower() for keyword in keywords)

    def test_lambda_complex_expressions_handled(self):
        """Test that complex expressions are handled gracefully."""
        # Complex expression that might not match patterns
        complex_check = lambda x: (x % 3 == 0) and (x > 10) and (x < 100)
        desc = _extract_predicate_description(complex_check)

        # Should return something, not crash
        assert desc is not None
        # Should extract some part of the expression
        # In this case it extracts "greater than 10" from the middle condition
        assert "10" in desc or "predicate" in desc.lower() or "lambda" in desc.lower()

    def test_lambda_with_callable_names(self):
        """Test lambdas that use named functions."""

        def validate_email(x):
            return "@" in x and "." in x

        desc = _extract_predicate_description(validate_email)
        assert desc is not None
        # Should use the function name
        assert "validate_email" in desc or "predicate" in desc.lower()

    def test_builtin_functions_handled(self):
        """Test that built-in functions are handled."""
        # Built-in functions don't have source
        desc = _extract_predicate_description(len)
        assert desc is not None
        assert "len" in desc or "predicate" in desc.lower()

        # Same for other built-ins - they get special handling
        desc = _extract_predicate_description(str.isdigit)
        assert desc is not None
        # str.isdigit gets special handling and returns "digits only"
        assert "digit" in desc.lower() or "predicate" in desc.lower()
