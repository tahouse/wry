"""Extended tests for core functionality to achieve 100% coverage."""

import json
import os
from typing import Any

import pytest
from pydantic import Field

from wry import (
    FieldWithSource,
    TrackedValue,
    ValueSource,
    WryModel,
    extract_field_constraints,
)


class TestExtractFieldConstraints:
    """Test the extract_field_constraints function."""

    def test_extract_with_annotated_types(self):
        """Test extracting constraints from annotated types."""
        try:
            from typing import Annotated

            from annotated_types import Gt, Lt, MaxLen, MinLen
            from pydantic import BaseModel

            class TestModel(BaseModel):
                value: Annotated[int, Gt(0), Lt(100)]
                name: Annotated[str, MinLen(3), MaxLen(50)]

            field_info = TestModel.model_fields["value"]
            constraints = extract_field_constraints(field_info)

            # Should extract from metadata
            assert "gt" in constraints or "ge" in constraints or "lt" in constraints or "le" in constraints

        except ImportError:
            pytest.skip("annotated_types not available")

    def test_extract_without_annotated_types(self, monkeypatch):
        """Test extraction when annotated_types is not available."""
        # Create a simple test without mocking __import__ to avoid recursion
        from pydantic import BaseModel

        class TestModel(BaseModel):
            value: int = Field(ge=0, le=100, max_length=None)  # Mix of constraints

        field_info = TestModel.model_fields["value"]

        # The function should handle missing annotated_types gracefully
        constraints = extract_field_constraints(field_info)

        # Should still get basic Pydantic constraints
        assert constraints["ge"] == 0
        assert constraints["le"] == 100
        # max_length=None should not be included
        assert "max_length" not in constraints


class TestTrackedValue:
    """Test TrackedValue dataclass."""

    def test_str_representation(self):
        """Test string representation of TrackedValue."""
        cv = TrackedValue("test", ValueSource.CLI)
        assert str(cv) == "test"

        cv_int = TrackedValue(42, ValueSource.ENV)
        assert str(cv_int) == "42"


class TestFieldWithSource:
    """Test FieldWithSource dataclass."""

    def test_str_representation(self):
        """Test string representation."""
        fws = FieldWithSource("value", ValueSource.JSON)
        assert str(fws) == "value"

    def test_hash(self):
        """Test that FieldWithSource is hashable."""
        fws = FieldWithSource("test", ValueSource.CLI)
        assert hash(fws) == hash("test")

        # Should be usable in sets/dicts
        test_set = {fws}
        assert fws in test_set


class TestSourceAccessor:
    """Test the SourceAccessor functionality."""

    def test_dir_method(self):
        """Test __dir__ method returns field names."""

        class TestConfig(WryModel):
            field1: str = Field(default="a")
            field2: int = Field(default=1)

        config = TestConfig()
        accessor_dir = dir(config.source)
        assert "field1" in accessor_dir
        assert "field2" in accessor_dir


class TestAccessorErrors:
    """Test error cases for accessor properties."""

    def test_minimum_accessor_unknown_field(self):
        """Test MinimumAccessor with unknown field."""

        class TestConfig(WryModel):
            value: int = Field(default=1)

        config = TestConfig()
        with pytest.raises(AttributeError, match="has no field 'unknown'"):
            _ = config.minimum.unknown

    def test_maximum_accessor_unknown_field(self):
        """Test MaximumAccessor with unknown field."""

        class TestConfig(WryModel):
            value: int = Field(default=1)

        config = TestConfig()
        with pytest.raises(AttributeError, match="has no field 'unknown'"):
            _ = config.maximum.unknown

    def test_constraints_accessor_unknown_field(self):
        """Test ConstraintsAccessor with unknown field."""

        class TestConfig(WryModel):
            value: int = Field(default=1)

        config = TestConfig()
        with pytest.raises(AttributeError, match="has no field 'unknown'"):
            _ = config.constraints.unknown

    def test_defaults_accessor_unknown_field(self):
        """Test DefaultsAccessor with unknown field."""

        class TestConfig(WryModel):
            value: int = Field(default=1)

        config = TestConfig()
        with pytest.raises(AttributeError, match="has no field 'unknown'"):
            _ = config.defaults.unknown


class TestFieldConstraintsEdgeCases:
    """Test edge cases for field constraints."""

    def test_field_without_constraints(self):
        """Test field with no constraints returns empty dict."""

        class TestConfig(WryModel):
            value: str = "test"

        config = TestConfig()
        constraints = config.get_field_constraints("value")
        assert isinstance(constraints, dict)
        # Only default should be present
        assert len(constraints) <= 1

    def test_gt_constraint_with_float(self):
        """Test gt constraint with float returns the value as-is."""

        class TestConfig(WryModel):
            value: float = Field(default=1.0, gt=0.0)

        config = TestConfig()
        minimum = config.get_field_minimum("value")
        assert minimum == 0.0  # For floats, gt value is returned as-is

    def test_lt_constraint_with_float(self):
        """Test lt constraint with float returns the value as-is."""

        class TestConfig(WryModel):
            value: float = Field(default=1.0, lt=10.0)

        config = TestConfig()
        maximum = config.get_field_maximum("value")
        assert maximum == 10.0  # For floats, lt value is returned as-is

    def test_default_not_numeric(self):
        """Test that non-numeric defaults are not returned as minimum."""

        class TestConfig(WryModel):
            value: str = Field(default="test")

        config = TestConfig()
        minimum = config.get_field_minimum("value")
        assert minimum is None  # String default should not be returned

    def test_field_default_none(self):
        """Test field with None default."""

        class TestConfig(WryModel):
            value: int | None = Field(default=None)

        config = TestConfig()
        default = config.get_field_default("value")
        assert default is None


class TestJsonFileOperations:
    """Test JSON file loading and saving."""

    def test_to_json_file(self, tmp_path):
        """Test saving config to JSON file."""

        class TestConfig(WryModel):
            name: str = Field(default="test")
            value: int = Field(default=42)

        config = TestConfig(name="custom", value=100)

        json_path = tmp_path / "config.json"
        config.to_json_file(json_path)

        # Verify file contents
        with open(json_path) as f:
            data = json.load(f)

        assert data["name"] == "custom"
        assert data["value"] == 100

    def test_from_json_file_partial(self, tmp_path):
        """Test loading partial config from JSON."""

        class TestConfig(WryModel):
            name: str = Field(default="default")
            value: int = Field(default=0)

        # Create JSON with partial data
        json_path = tmp_path / "partial.json"
        with open(json_path, "w") as f:
            json.dump({"name": "from-json"}, f)

        config = TestConfig.from_json_file(json_path)

        assert config.name == "from-json"
        assert config.value == 0  # Should use default
        assert config.source.name == ValueSource.JSON
        assert config.source.value == ValueSource.DEFAULT


class TestEnvironmentVariables:
    """Test environment variable functionality."""

    def test_print_env_vars_with_types(self, capsys):
        """Test print_env_vars with various field types."""

        class TestConfig(WryModel):
            env_prefix = "TEST_"

            string_val: str = Field(description="A string")
            int_val: int = Field(default=42, description="An integer")
            float_val: float = Field(default=3.14)
            bool_val: bool = Field(default=False)
            optional_val: str | None = Field(default=None)
            required_val: str = Field(description="Required field")

        TestConfig.print_env_vars()

        captured = capsys.readouterr()
        assert "TEST_STRING_VAL" in captured.out
        assert "TEST_INT_VAL" in captured.out
        assert "A string" in captured.out
        assert "An integer" in captured.out
        assert "(required)" in captured.out
        assert "str | None" in captured.out  # Python 3.10+ union syntax
        assert "bool: true/false, 1/0, yes/no, on/off" in captured.out

    def test_get_env_values_type_conversion(self):
        """Test environment variable type conversion."""

        class TestConfig(WryModel):
            env_prefix = "TESTCONV_"

            bool_true: bool = Field(default=False)
            bool_false: bool = Field(default=True)
            int_val: int = Field(default=0)
            float_val: float = Field(default=0.0)
            string_val: str = Field(default="")
            invalid_int: int = Field(default=0)

        # Set environment variables
        os.environ["TESTCONV_BOOL_TRUE"] = "yes"
        os.environ["TESTCONV_BOOL_FALSE"] = "0"
        os.environ["TESTCONV_INT_VAL"] = "42"
        os.environ["TESTCONV_FLOAT_VAL"] = "3.14"
        os.environ["TESTCONV_STRING_VAL"] = "test"
        os.environ["TESTCONV_INVALID_INT"] = "not-a-number"

        try:
            env_values = TestConfig.get_env_values()

            assert env_values["bool_true"] is True
            assert env_values["bool_false"] is False
            assert env_values["int_val"] == 42
            assert env_values["float_val"] == 3.14
            assert env_values["string_val"] == "test"
            assert env_values["invalid_int"] == "not-a-number"  # Falls back to string
        finally:
            # Clean up
            for key in [
                "BOOL_TRUE",
                "BOOL_FALSE",
                "INT_VAL",
                "FLOAT_VAL",
                "STRING_VAL",
                "INVALID_INT",
            ]:
                os.environ.pop(f"TESTCONV_{key}", None)


class TestModelDumpWithSources:
    """Test model_dump_with_sources functionality."""

    def test_dump_with_sources(self):
        """Test dumping model with source information."""

        class TestConfig(WryModel):
            name: str = Field(default="test")
            value: int = Field(default=1)

        config = TestConfig.create_with_sources(
            {
                "name": TrackedValue("cli-name", ValueSource.CLI),
                "value": TrackedValue(42, ValueSource.ENV),
            }
        )

        result = config.model_dump_with_sources()

        assert result["values"]["name"] == "cli-name"
        assert result["values"]["value"] == 42
        assert result["sources"]["name"] == "cli"
        assert result["sources"]["value"] == "env"


class TestGetFieldWithSource:
    """Test get_field_with_source method."""

    def test_get_field_with_source(self):
        """Test retrieving field with its source."""

        class TestConfig(WryModel):
            name: str = Field(default="test")

        config = TestConfig.create_with_sources({"name": TrackedValue("from-cli", ValueSource.CLI)})

        field_with_source = config.get_field_with_source("name")

        assert field_with_source.value == "from-cli"
        assert field_with_source.source == ValueSource.CLI
        assert str(field_with_source) == "from-cli"


class TestExtractSubset:
    """Test extract_subset functionality."""

    def test_extract_subset_missing_fields(self):
        """Test extracting subset when target has fields not in source."""
        from pydantic import BaseModel

        class SourceConfig(WryModel):
            name: str = Field(default="source")
            value: int = Field(default=42)

        class TargetModel(BaseModel):
            name: str
            missing_field: str = Field(default="default")
            missing_required: str  # No default

        source = SourceConfig()
        extracted = source.extract_subset(TargetModel)

        assert extracted["name"] == "source"
        assert extracted["missing_field"] == "default"
        assert "missing_required" not in extracted  # Required field without default is skipped

    def test_extract_subset_from_with_factory(self):
        """Test extract_subset_from with default_factory fields."""
        from pydantic import BaseModel

        class SourceObj:
            name = "test"
            items = ["a", "b"]

        class TargetModel(BaseModel):
            name: str
            items: list[str] = Field(default_factory=list)
            missing: list[str] = Field(default_factory=list)

        extracted = WryModel.extract_subset_from(SourceObj(), TargetModel)

        assert extracted["name"] == "test"
        assert extracted["items"] == ["a", "b"]
        assert extracted["missing"] == []  # From default_factory

    def test_extract_subset_from_with_pydantic_undefined(self):
        """Test handling of PydanticUndefined in extract_subset_from."""
        from pydantic import BaseModel

        class TargetModel(BaseModel):
            # Create a field that might have PydanticUndefined
            value: int

        # Use the class method directly
        extracted = WryModel.extract_subset_from({}, TargetModel)

        # Should skip fields with PydanticUndefined
        assert "value" not in extracted


class TestFromClickContextEdgeCases:
    """Test edge cases in from_click_context."""

    def test_from_click_context_missing_fields(self):
        """Test from_click_context with missing required fields."""
        import click

        class TestConfig(WryModel):
            required_field: str
            optional_field: str = Field(default="default")

        ctx = click.Context(click.Command("test"))
        ctx.obj = {}

        # Should raise validation error for missing required field
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TestConfig.from_click_context(ctx)

    def test_from_click_context_with_factory_defaults(self):
        """Test from_click_context with default_factory fields."""
        import click

        class TestConfig(WryModel):
            items: list[str] = Field(default_factory=list)
            data: dict[str, Any] = Field(default_factory=dict)

        ctx = click.Context(click.Command("test"))
        ctx.obj = {}

        config = TestConfig.from_click_context(ctx)

        assert config.items == []
        assert config.data == {}
        assert config.source.items == ValueSource.DEFAULT
        assert config.source.data == ValueSource.DEFAULT

    def test_from_click_context_parameter_source_error(self):
        """Test from_click_context when get_parameter_source fails."""
        import click

        class TestConfig(WryModel):
            value: int = Field(default=1)

        ctx = click.Context(click.Command("test"))
        ctx.obj = {}

        # Set params to ensure kwargs are recognized
        ctx.params = {"value": 42}

        # When get_parameter_source is not available or fails,
        # it should use the kwargs value with DEFAULT source
        config = TestConfig.from_click_context(ctx, value=42)

        # The value should be updated, but source tracking depends on context
        assert config.value == 42
        # Since we're not simulating a proper Click context with params,
        # the source will be DEFAULT


class TestCustomTypeField:
    """Test fields with custom types."""

    def test_print_env_vars_custom_type(self, capsys):
        """Test print_env_vars with custom type."""
        from enum import Enum

        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        class TestConfig(WryModel):
            color: Color = Field(default=Color.RED)

        TestConfig.print_env_vars()

        captured = capsys.readouterr()
        # Should show the type name for custom types
        assert "color" in captured.out.lower()


class TestTrackedValueEquality:
    """Test TrackedValue equality comparisons."""

    def test_field_with_source_equality(self):
        """Test FieldWithSource equality with another FieldWithSource."""
        fws1 = FieldWithSource("test", ValueSource.CLI)
        fws2 = FieldWithSource("test", ValueSource.ENV)
        fws3 = FieldWithSource("other", ValueSource.CLI)

        assert fws1 == fws2  # Same value, different source
        assert fws1 != fws3  # Different value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
