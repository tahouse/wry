"""Test Click predicate handling and lambda introspection."""

from wry.click_integration import _extract_predicate_description


class TestPredicateHandling:
    """Test predicate description extraction for various function types."""

    def test_extract_from_builtin_string_methods(self):
        """Test extraction from built-in string methods."""
        assert _extract_predicate_description(str.islower) == "lowercase"
        assert _extract_predicate_description(str.isupper) == "uppercase"
        assert _extract_predicate_description(str.isdigit) == "digits only"
        assert _extract_predicate_description(str.isascii) == "ASCII only"
        assert _extract_predicate_description(str.isalnum) == "alphanumeric only"
        assert _extract_predicate_description(str.isalpha) == "alphabetic only"

    def test_extract_from_lambda_with_string_operations(self):
        """Test extraction from lambdas with string operations."""
        # Lambda checking for specific strings
        check_foo = lambda x: "foo" in x
        desc = _extract_predicate_description(check_foo)
        assert "contains" in desc and "foo" in desc

        # Lambda checking string start
        check_prefix = lambda x: x.startswith("prefix")
        desc = _extract_predicate_description(check_prefix)
        assert "starts with" in desc and "prefix" in desc

        # Lambda checking string end
        check_suffix = lambda x: x.endswith(".txt")
        desc = _extract_predicate_description(check_suffix)
        assert "ends with" in desc and ".txt" in desc

    def test_extract_from_lambda_with_numeric_comparisons(self):
        """Test extraction from lambdas with numeric comparisons."""
        # Greater than
        gt_zero = lambda x: x > 0
        desc = _extract_predicate_description(gt_zero)
        assert "greater than 0" in desc or "> 0" in desc

        # Less than
        lt_hundred = lambda x: x < 100
        desc = _extract_predicate_description(lt_hundred)
        assert "less than 100" in desc or "< 100" in desc

        # Equality
        eq_five = lambda x: x == 5
        desc = _extract_predicate_description(eq_five)
        assert "equals 5" in desc or "== 5" in desc

    def test_extract_from_generic_lambda(self):
        """Test extraction from lambda without recognizable pattern."""
        # Complex lambda that doesn't match patterns
        complex_check = lambda x: (x * 2 + 1) % 7 == 0
        desc = _extract_predicate_description(complex_check)
        # Should return something describing it's a predicate/lambda
        assert desc is not None
        # Should extract the actual lambda expression
        assert "must satisfy" in desc or "predicate" in desc.lower() or "lambda" in desc.lower()

    def test_extract_from_regular_function(self):
        """Test extraction from named function."""

        def validate_email(email: str) -> bool:
            return "@" in email and "." in email

        desc = _extract_predicate_description(validate_email)
        assert desc == "predicate: validate_email"
