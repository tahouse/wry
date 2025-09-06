"""Test predicate description extraction with source errors."""

from wry.click_integration import _extract_predicate_description


class TestPredicateSourceErrors:
    """Test handling of errors when extracting predicate source."""

    def test_builtin_function_no_source(self):
        """Test predicate description for built-in functions."""
        # Built-in functions don't have source code
        result = _extract_predicate_description(len)
        assert result is not None
        assert "len" in result or "predicate" in result

    def test_dynamically_created_function(self):
        """Test predicate description for dynamically created functions."""
        # Create a function dynamically
        func_code = compile("def dynamic(x): return x > 0", "<string>", "exec")
        namespace = {}
        exec(func_code, namespace)
        dynamic_func = namespace["dynamic"]

        result = _extract_predicate_description(dynamic_func)
        assert result is not None
        assert "dynamic" in result or "predicate" in result

    def test_c_extension_function(self):
        """Test predicate description for C extension functions."""
        # Use a C extension function
        import math

        result = _extract_predicate_description(math.isnan)
        assert result is not None
        assert "isnan" in result or "predicate" in result

    def test_lambda_in_unusual_context(self):
        """Test lambda that might cause OSError in inspect."""
        # Lambda defined in a way that might be hard to inspect
        import types

        # Create a lambda through types
        lambda_func = types.LambdaType((lambda x: x > 0).__code__, {"__builtins__": __builtins__})

        result = _extract_predicate_description(lambda_func)
        assert result is not None
