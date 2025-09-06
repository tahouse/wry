"""Test edge cases for Click integration that aren't covered in main tests."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import BaseModel, Field

from wry import AutoOption, WryModel, generate_click_parameters


class TestFormatConstraintTextEdgeCases:
    """Test edge cases for format_constraint_text."""

    def test_empty_constraints(self):
        """Test formatting with no constraints."""
        from wry.click_integration import format_constraint_text

        result = format_constraint_text({})
        assert result == []

    def test_unknown_constraint_type(self):
        """Test formatting with unknown constraint."""
        from wry.click_integration import format_constraint_text

        result = format_constraint_text({"unknown_constraint": "value"})
        assert result == []

    def test_mixed_constraints(self):
        """Test formatting with various constraint types."""
        from wry.click_integration import format_constraint_text

        constraints = {"ge": 0, "le": 100, "multiple_of": 5, "min_length": 3, "max_length": 20}
        result = format_constraint_text(constraints)
        assert any("0-100" in item for item in result) or (">= 0" in result and "<= 100" in result)
        assert "multiple of 5" in result
        assert "length 3-20" in result


class TestExtractConstraintTextEdgeCases:
    """Test edge cases for extract_constraint_text."""

    def test_no_metadata(self):
        """Test extraction with no metadata."""
        from wry.click_integration import extract_constraint_text

        result = extract_constraint_text([])
        assert result is None

    def test_mixed_metadata_types(self):
        """Test extraction with various metadata types."""
        from annotated_types import Interval, Len, Predicate

        from wry.click_integration import extract_constraint_text

        def is_even(x):
            return x % 2 == 0

        # Test individual constraints
        interval_result = extract_constraint_text(Interval(ge=0, le=10))
        assert interval_result is not None and ">= 0" in interval_result and "<= 10" in interval_result

        len_result = extract_constraint_text(Len(min_length=2, max_length=5))
        assert len_result is not None and ("length 2-5" in len_result or "min length 2 AND max length 5" in len_result)

        predicate_result = extract_constraint_text(Predicate(is_even))
        assert predicate_result is not None and "is_even" in predicate_result


class TestGenerateClickParametersEdgeCases:
    """Test generate_click_parameters edge cases."""

    def test_model_without_annotated_fields(self):
        """Test model with no Annotated fields."""

        class PlainModel(BaseModel):
            name: str = Field(default="test")
            value: int = Field(default=42)

        @click.command()
        @generate_click_parameters(PlainModel)
        def cmd(**kwargs):
            click.echo(str(kwargs))

        # Should work but add no parameters
        runner = CliRunner()
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0

    def test_duplicate_application_non_strict(self):
        """Test duplicate decorator application with strict=False."""

        class Config(WryModel):
            name: Annotated[str, AutoOption] = Field(description="Name")

        # Test with strict=False - should warn but not error
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @click.command()
            @generate_click_parameters(Config, strict=False)
            @generate_click_parameters(Config, strict=False)
            def cmd(**kwargs):
                pass

            # Should have warned
            assert len(w) > 0
            assert "already decorated" in str(w[0].message)

    def test_no_command_decorator(self):
        """Test applying to non-command function."""

        class Config(WryModel):
            name: Annotated[str, AutoOption] = Field(description="Name")

        # This is technically valid - decorators stack
        @generate_click_parameters(Config)
        def not_a_command(**kwargs):
            return kwargs

        # Function should be callable
        result = not_a_command(name="test")
        assert result == {"name": "test"}

    def test_with_existing_params(self):
        """Test decorator on command with existing parameters."""

        class Config(WryModel):
            extra: Annotated[str, AutoOption] = Field(default="extra")

        @click.command()
        @click.option("--existing", default="test")
        @generate_click_parameters(Config)
        def cmd(existing, **kwargs):
            config = Config(**kwargs)
            click.echo(f"{existing} {config.extra}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--existing", "hello", "--extra", "world"])

        assert result.exit_code == 0
        assert "hello world" in result.output

    def test_field_name_conflicts(self):
        """Test handling of field names that conflict with Python keywords."""

        class Config(WryModel):
            # These are tricky field names
            class_: Annotated[str, AutoOption] = Field(default="test", description="Class name")
            for_: Annotated[int, AutoOption] = Field(default=1, description="For loop count")

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            # kwargs will have class_ and for_
            click.echo(f"class_={kwargs.get('class_')}, for_={kwargs.get('for_')}")

        runner = CliRunner()
        # Click converts underscore to hyphen in option names
        result = runner.invoke(cmd, ["--class-", "MyClass", "--for-", "10"])

        # Debug output
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")

        assert result.exit_code == 0
        assert "class_=MyClass" in result.output
        assert "for_=10" in result.output
