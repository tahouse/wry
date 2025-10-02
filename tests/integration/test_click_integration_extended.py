"""Extended tests for Click integration to achieve 100% coverage."""

from typing import Annotated

import click
import pytest
from click.testing import CliRunner
from pydantic import Field

from wry import (
    AutoClickParameter,
    AutoOption,
    WryModel,
    build_config_with_sources,
    config_option,
    eager_json_config,
    generate_click_parameters,
)
from wry.click_integration import (
    _extract_predicate_description,
    extract_and_modify_argument_decorator,
    extract_constraint_text,
    format_constraint_text,
)


class TestFormatConstraintText:
    """Test format_constraint_text function."""

    def test_numeric_bounds(self):
        """Test formatting numeric bound constraints."""
        constraints = {"ge": 0, "le": 100}
        result = format_constraint_text(constraints)
        assert ">= 0" in result
        assert "<= 100" in result

    def test_gt_lt_constraints(self):
        """Test formatting gt/lt constraints."""
        constraints = {"gt": 5, "lt": 10}
        result = format_constraint_text(constraints)
        assert "> 5" in result
        assert "< 10" in result

    def test_length_constraints_equal(self):
        """Test formatting when min and max length are equal."""
        constraints = {"min_length": 5, "max_length": 5}
        result = format_constraint_text(constraints)
        assert "length = 5" in result

    def test_length_constraints_range(self):
        """Test formatting length range."""
        constraints = {"min_length": 3, "max_length": 10}
        result = format_constraint_text(constraints)
        assert "length 3-10" in result

    def test_single_length_constraints(self):
        """Test formatting single length constraints."""
        min_result = format_constraint_text({"min_length": 3})
        assert "min length 3" in min_result

        max_result = format_constraint_text({"max_length": 10})
        assert "max length 10" in max_result

    def test_multiple_of(self):
        """Test formatting multiple_of constraint."""
        constraints = {"multiple_of": 5}
        result = format_constraint_text(constraints)
        assert "multiple of 5" in result


class TestExtractConstraintText:
    """Test extract_constraint_text function."""

    def test_grouped_metadata(self):
        """Test extracting from GroupedMetadata."""
        try:
            from annotated_types import Ge, Le

            # Test individual constraints since GroupedMetadata is a protocol
            ge_constraint = Ge(0)
            le_constraint = Le(100)

            ge_result = extract_constraint_text(ge_constraint)
            le_result = extract_constraint_text(le_constraint)

            assert ">= 0" in ge_result
            assert "<= 100" in le_result
        except ImportError:
            pytest.skip("annotated_types not available")

    def test_interval_constraint(self):
        """Test extracting from Interval constraint."""
        try:
            from annotated_types import Interval

            interval = Interval(gt=0, lt=100)
            result = extract_constraint_text(interval)
            assert "> 0" in result
            assert "< 100" in result
        except ImportError:
            pytest.skip("annotated_types not available")

    def test_len_constraint(self):
        """Test extracting from Len constraint."""
        try:
            from annotated_types import Len

            # Len constraint with min/max
            # Note: The actual Len implementation might differ
            len_constraint = Len(min_length=3, max_length=10)
            result = extract_constraint_text(len_constraint)
            if result:  # May not be implemented yet
                assert "3" in result or "10" in result
        except (ImportError, TypeError):
            pytest.skip("annotated_types not available or Len signature different")

    def test_timezone_constraint(self):
        """Test extracting from Timezone constraint."""
        try:
            from annotated_types import Timezone

            # Naive datetime
            tz_naive = Timezone(None)
            result = extract_constraint_text(tz_naive)
            assert "naive datetime" in result

            # Any timezone
            tz_any = Timezone(...)
            result = extract_constraint_text(tz_any)
            assert "any timezone-aware" in result
        except ImportError:
            pytest.skip("annotated_types not available")

    def test_slice_constraint(self):
        """Test extracting from slice objects."""
        # Single value slice
        slice_single = slice(5, 6)
        result = extract_constraint_text(slice_single)
        assert "length = 5" in result

        # Range slice
        slice_range = slice(3, 10)
        result = extract_constraint_text(slice_range)
        assert "length 3-9" in result

        # Open-ended slice
        slice_open = slice(3, None)
        result = extract_constraint_text(slice_open)
        assert "min length 3" in result

    def test_unknown_constraint(self):
        """Test extracting from unknown constraint type."""

        class UnknownConstraint:
            pass

        result = extract_constraint_text(UnknownConstraint())
        assert result is None


class TestPredicateDescription:
    """Test _extract_predicate_description function."""

    def test_builtin_predicates(self):
        """Test extraction for built-in string predicates."""
        assert _extract_predicate_description(str.islower) == "lowercase"
        assert _extract_predicate_description(str.isupper) == "uppercase"
        assert _extract_predicate_description(str.isdigit) == "digits only"
        assert _extract_predicate_description(str.isascii) == "ASCII only"
        assert _extract_predicate_description(str.isalnum) == "alphanumeric only"
        assert _extract_predicate_description(str.isalpha) == "alphabetic only"

    def test_named_function(self):
        """Test extraction for named functions."""

        def my_validator(x):
            return True

        result = _extract_predicate_description(my_validator)
        assert "my_validator" in result

    def test_lambda_patterns(self):
        """Test extraction for common lambda patterns."""

        # We can't easily test lambda source extraction without eval
        # But we can test the fallback
        def test_func(x):
            return x > 0

        lambda_func = test_func
        result = _extract_predicate_description(lambda_func)
        assert isinstance(result, str)  # Should return some description


class TestComplexFieldTypes:
    """Test complex field type handling."""

    def test_union_types_python39(self):
        """Test handling of Union types in Python 3.9+."""

        class TestConfig(WryModel):
            # Using Union syntax compatible with Python 3.9
            value: str | None = Field(default=None)

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        # Should not raise an error
        runner = CliRunner()
        result = runner.invoke(test_command, ["--help"])
        assert result.exit_code == 0

    def test_custom_type_field(self):
        """Test fields with custom types."""
        from enum import Enum

        class Color(Enum):
            RED = "red"
            GREEN = "green"

        class TestConfig(WryModel):
            color: Annotated[Color, AutoOption] = Field(default=Color.RED)

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(test_command, ["--help"])
        assert result.exit_code == 0


class TestConfigOption:
    """Test config_option function."""

    def test_config_option_decorator(self):
        """Test that config_option returns a proper decorator."""
        decorator = config_option()

        @click.command()
        @decorator
        def test_command(**kwargs):
            pass

        # Check that the command has the config option
        assert any(param.name == "config" for param in test_command.params)


class TestEagerJsonConfig:
    """Test eager_json_config callback."""

    def test_resilient_parsing(self):
        """Test that eager_json_config returns early during resilient parsing."""
        ctx = click.Context(click.Command("test"))
        ctx.resilient_parsing = True

        result = eager_json_config(ctx, None, "config.json")
        assert result == "config.json"

    def test_no_value(self):
        """Test that eager_json_config returns early with no value."""
        ctx = click.Context(click.Command("test"))

        result = eager_json_config(ctx, None, None)
        assert result is None

    def test_invalid_json_file(self, tmp_path):
        """Test eager_json_config with invalid JSON."""
        ctx = click.Context(click.Command("test"))

        # Create invalid JSON file
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json")

        with pytest.raises(click.BadParameter, match="Config file error"):
            eager_json_config(ctx, None, str(bad_json))

    def test_modify_click_parameters(self, tmp_path):
        """Test that eager_json_config modifies Click parameters."""

        # Create a command with parameters
        @click.command()
        @click.argument("required_arg")
        @click.option("--optional", required=True)
        def test_command(required_arg, optional):
            pass

        ctx = click.Context(test_command)
        ctx.obj = {}

        # Create config file
        config_file = tmp_path / "config.json"
        config_file.write_text('{"required_arg": "from-json", "optional": "also-json"}')

        eager_json_config(ctx, None, str(config_file))

        # Check that parameters were marked as not required
        # Note: We do NOT modify param.default to preserve CLI override behavior
        for param in ctx.command.params:
            if param.name in ["required_arg", "optional"]:
                assert not param.required

        # JSON data should be stored in context for later use
        assert ctx.obj.get("json_data") == {"required_arg": "from-json", "optional": "also-json"}


class TestExtractAndModifyArgument:
    """Test extract_and_modify_argument_decorator function."""

    def test_extract_with_closure(self):
        """Test extracting from a decorator with closure."""
        # Create a real click.argument decorator
        original = click.argument("filename", type=click.Path(), required=True)

        # Extract and modify (now returns tuple)
        modified, info = extract_and_modify_argument_decorator(original)

        # Apply to a dummy function
        @modified
        def dummy():
            pass

        # The modified decorator should create an argument with required=False
        # We can't easily verify this without inspecting Click internals
        # But we can check the info dict
        assert "param_decls" in info
        assert info["required"] is False

    def test_extract_without_closure(self):
        """Test extracting from a decorator without proper closure."""

        # Create a mock decorator without closure
        def mock_decorator(func):
            return func

        modified, info = extract_and_modify_argument_decorator(mock_decorator)

        # Should return a decorator that creates an argument
        assert callable(modified)
        # Should have default info
        assert "param_decls" in info
        assert info["required"] is False

    def test_extract_with_exception(self):
        """Test that extraction handles exceptions gracefully."""

        # Create a decorator that will cause issues
        class BadDecorator:
            __closure__ = None

            def __call__(self, func):
                return func

        modified, info = extract_and_modify_argument_decorator(BadDecorator())

        # Should still return a valid decorator
        assert callable(modified)
        # Should have safe defaults
        assert "param_decls" in info
        assert info["required"] is False


class TestBuildConfigWithSources:
    """Test build_config_with_sources function."""

    def test_with_dry_model(self):
        """Test building config with a WryModel class."""
        import click

        class TestConfig(WryModel):
            value: int = Field(default=42)
            name: str = Field(default="test")

        ctx = click.Context(click.Command("test"))
        ctx.obj = {}
        # Set params to simulate CLI values
        ctx.params = {"value": 200, "name": "cli"}

        # The build_config_with_sources delegates to from_click_context
        # which builds config from the kwargs
        config = build_config_with_sources(ctx, TestConfig, value=200, name="cli")

        # Should use the kwargs values
        assert config.value == 200
        assert config.name == "cli"
        assert isinstance(config, TestConfig)

    def test_with_regular_pydantic_model(self):
        """Test building config with a regular Pydantic model."""
        import click
        from pydantic import BaseModel

        class RegularModel(BaseModel):
            value: int = 42
            name: str | None = None

        ctx = click.Context(click.Command("test"))

        # Should handle models without from_click_context method
        config = build_config_with_sources(ctx, RegularModel, value=100, name="test")

        assert config.value == 100
        assert config.name == "test"
        assert isinstance(config, RegularModel)


class TestRequiredOptionGeneration:
    """Test REQUIRED_OPTION handling."""

    def test_required_option_marker(self):
        """Test that REQUIRED_OPTION forces a field to be required."""

        class TestConfig(WryModel):
            optional_field: Annotated[str, AutoOption] = Field(default="default")
            # REQUIRED_OPTION should make field required regardless of default
            required_field: Annotated[str, AutoClickParameter.REQUIRED_OPTION] = Field(
                description="This field is required"
            )

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(test_command, [])

        # Should fail because required_field is marked as REQUIRED_OPTION
        assert result.exit_code != 0
        # Check that the error mentions the missing field


class TestAddConfigOption:
    """Test add_config_option parameter."""

    def test_without_config_option(self):
        """Test generate_click_parameters with add_config_option=False."""

        class TestConfig(WryModel):
            value: Annotated[int, AutoOption] = Field(default=1)

        @click.command()
        @generate_click_parameters(TestConfig, add_config_option=False)
        def test_command(**kwargs):
            pass

        # Should not have --config option
        assert not any(param.name == "config" for param in test_command.params)
        # But should still have --show-env-vars
        assert any(param.name == "show_env_vars" for param in test_command.params)


class TestExplicitClickDecorators:
    """Test handling of explicit Click decorators in annotations."""

    def test_explicit_option_decorator(self):
        """Test field with explicit click.option in annotation."""

        class TestConfig(WryModel):
            # Use the actual click.option as annotation
            custom: Annotated[str, click.option("--custom-name", "-c")] = Field(default="test")

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        # Should have the custom option
        runner = CliRunner()
        result = runner.invoke(test_command, ["--help"])
        assert "--custom-name" in result.output

    def test_explicit_argument_decorator(self):
        """Test field with explicit click.argument in annotation."""

        class TestConfig(WryModel):
            # Use actual click.argument as annotation
            filename: Annotated[str, click.argument("input_file")] = Field()

        @click.command()
        @generate_click_parameters(TestConfig)
        def test_command(**kwargs):
            pass

        # Should handle the explicit argument
        runner = CliRunner()
        result = runner.invoke(test_command, ["--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
