"""Tests to cover remaining gaps in core module coverage."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from wry import TrackedValue, ValueSource, WryModel
from wry.core.env_utils import get_env_values
from wry.core.field_utils import get_field_minimum


class TestAccessorsCoverage:
    """Test remaining accessor edge cases."""

    def test_source_accessor_repr(self):
        """Test SourceAccessor __repr__ method."""

        class Config(WryModel):
            value: int = 42

        config = Config()
        accessor = config.source

        repr_str = repr(accessor)
        assert "SourceAccessor" in repr_str

    def test_accessor_getattr_error_messages(self):
        """Test error messages for all accessor types."""

        class Config(WryModel):
            value: int = 42

        config = Config()

        # Test each accessor type
        # SourceAccessor returns DEFAULT for missing fields
        assert config.source.missing == ValueSource.DEFAULT

        with pytest.raises(AttributeError, match="Config has no field 'missing'"):
            _ = config.minimum.missing

        with pytest.raises(AttributeError, match="Config has no field 'missing'"):
            _ = config.maximum.missing

        with pytest.raises(AttributeError, match="Config has no field 'missing'"):
            _ = config.constraints.missing

        with pytest.raises(AttributeError, match="Config has no field 'missing'"):
            _ = config.defaults.missing


class TestEnvUtilsCoverage:
    """Test remaining env_utils edge cases."""

    def test_get_env_values_with_list_type(self):
        """Test get_env_values with unsupported list type."""

        class Config(WryModel):
            env_prefix = "TEST_"
            items: list[str] = Field(default_factory=list)

        # Set env var that can't be converted to list
        os.environ["TEST_ITEMS"] = "[1, 2, 3]"

        try:
            env_values = get_env_values(Config)
            # Should store as string when conversion fails
            assert env_values["items"] == "[1, 2, 3]"
        finally:
            del os.environ["TEST_ITEMS"]

    def test_get_env_values_complex_type_error(self):
        """Test get_env_values with complex type that raises TypeError."""

        class CustomType:
            def __init__(self, value):
                if not isinstance(value, dict):
                    raise TypeError("Expected dict")
                self.value = value

        class Config(WryModel):
            env_prefix = "TEST_"
            custom: CustomType = Field(default_factory=lambda: CustomType({}))

        os.environ["TEST_CUSTOM"] = "not-a-dict"

        try:
            env_values = get_env_values(Config)
            # Should store original string when type conversion fails
            assert env_values["custom"] == "not-a-dict"
        finally:
            del os.environ["TEST_CUSTOM"]


class TestFieldUtilsCoverage:
    """Test remaining field_utils edge cases."""

    def test_get_field_minimum_with_constraints(self):
        """Test get_field_minimum with annotated constraints."""
        from typing import Annotated

        from annotated_types import Ge

        class Config(WryModel):
            # Field with annotated constraint
            value: Annotated[int, Ge(10)] = Field(default=20)

        field_info = Config.model_fields["value"]
        min_val = get_field_minimum(field_info)
        assert min_val == 10


class TestModelCoverage:
    """Test remaining model.py edge cases."""

    def test_from_json_file_not_found(self):
        """Test from_json_file with non-existent file."""

        class Config(WryModel):
            value: int = 42

        with pytest.raises(FileNotFoundError):
            Config.from_json_file(Path("/non/existent/file.json"))

    def test_from_json_file_invalid_json(self):
        """Test from_json_file with invalid JSON."""

        class Config(WryModel):
            value: int = 42

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{")
            temp_file = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                Config.from_json_file(temp_file)
        finally:
            temp_file.unlink()

    def test_to_json_file_with_path_object(self):
        """Test to_json_file with Path object."""

        class Config(WryModel):
            name: str = "test"
            value: int = 42

        config = Config()

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "config.json"
            config.to_json_file(json_path)

            # Verify file was created
            assert json_path.exists()

            # Verify contents
            with open(json_path) as f:
                data = json.load(f)
            assert data["name"] == "test"
            assert data["value"] == 42

    def test_extract_subset_from_with_model_instance(self):
        """Test extract_subset_from with model instance source."""

        class Source(BaseModel):
            name: str = "source"
            value: int = 100
            extra: str = "extra"

        class Target(BaseModel):
            name: str
            value: int

        source = Source()
        result = WryModel.extract_subset_from(source, Target)

        assert result == {"name": "source", "value": 100}
        assert "extra" not in result

    def test_extract_subset_from_dict_with_none(self):
        """Test extract_subset_from with None values in dict."""

        class Target(BaseModel):
            name: str
            optional: int | None = None

        source_dict = {"name": "test", "optional": None, "extra": "ignored"}
        result = WryModel.extract_subset_from(source_dict, Target)

        assert result == {"name": "test", "optional": None}

    def test_extract_subset_from_plain_object(self):
        """Test extract_subset_from with plain object (not dict/model)."""

        class PlainObject:
            def __init__(self):
                self.name = "plain"
                self.value = 42
                self._private = "hidden"

        class Target(BaseModel):
            name: str
            value: int

        source = PlainObject()
        result = WryModel.extract_subset_from(source, Target)

        assert result == {"name": "plain", "value": 42}

    def test_from_click_context_param_source_error(self):
        """Test from_click_context when get_parameter_source raises RuntimeError."""
        import click

        class Config(WryModel):
            value: int = Field(default=42)

        # Create a mock context that raises RuntimeError
        ctx = click.Context(click.Command("test"))
        ctx.params = {"value": 100}

        # Mock get_parameter_source to raise RuntimeError
        def mock_get_source(name):
            raise RuntimeError("No parameter source available")

        ctx.get_parameter_source = mock_get_source

        # Should still work, falling back to CLI assumption
        config = Config.from_click_context(ctx, value=100)
        assert config.value == 100
        assert config.source.value.value == "cli"

    def test_model_dump_with_sources_exclude(self):
        """Test model_dump_with_sources with exclude parameter."""

        class Config(WryModel):
            name: str = "test"
            value: int = 42
            secret: str = "hidden"

        config = Config()
        result = config.model_dump_with_sources(exclude={"secret"})

        assert "name" in result["values"]
        assert "value" in result["values"]
        assert "secret" not in result["values"]
        # The exclude parameter only excludes from values, not sources
        assert "secret" not in result["values"]
        assert "secret" in result["sources"]  # Sources are always included

    def test_get_field_with_source_missing_field(self):
        """Test get_field_with_source with non-existent field."""

        class Config(WryModel):
            value: int = 42

        config = Config()

        with pytest.raises(AttributeError, match="no attribute 'missing'"):
            config.get_field_with_source("missing")


class TestSourcesCoverage:
    """Test remaining sources.py edge cases."""

    def test_config_value_equality(self):
        """Test TrackedValue equality comparison."""
        cv1 = TrackedValue(42, ValueSource.CLI)
        cv2 = TrackedValue(42, ValueSource.CLI)
        cv3 = TrackedValue(42, ValueSource.ENV)
        cv4 = TrackedValue(43, ValueSource.CLI)

        assert cv1 == cv2  # Same value and source
        assert cv1 != cv3  # Different source
        assert cv1 != cv4  # Different value
        assert cv1 != 42  # Different type

    def test_field_with_source_repr(self):
        """Test FieldWithSource __repr__ method."""
        from wry.core.sources import FieldWithSource

        fws = FieldWithSource(123, ValueSource.JSON)
        repr_str = repr(fws)

        assert "FieldWithSource" in repr_str
        assert "123" in repr_str
        assert "json" in repr_str
