"""Test WryModel edge cases for improved coverage."""

import os
from pathlib import Path

from pydantic import Field

from wry import ValueSource, WryModel


class TestModelEdgeCases:
    """Test edge cases in WryModel."""

    def test_model_with_default_factory(self):
        """Test field with default_factory."""

        class Config(WryModel):
            items: list[str] = Field(default_factory=list)

        config = Config()
        assert config.items == []
        assert config.source.items == ValueSource.DEFAULT

    def test_create_with_sources_from_json_file(self):
        """Test creating model from JSON file using from_json_file."""
        import json
        import tempfile

        class Config(WryModel):
            name: str = "default"
            count: int = 0

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "test", "count": 42}, f)
            temp_path = f.name

        try:
            config = Config.from_json_file(Path(temp_path))
            assert config.name == "test"
            assert config.count == 42
            assert config.source.name == ValueSource.JSON
            assert config.source.count == ValueSource.JSON
        finally:
            os.unlink(temp_path)

    def test_from_json_file_not_found(self):
        """Test from_json_file with non-existent file."""
        import pytest

        class Config(WryModel):
            name: str = "default"

        with pytest.raises(FileNotFoundError):
            Config.from_json_file(Path("/nonexistent/file.json"))

    def test_to_json_file(self):
        """Test saving model to JSON file."""
        import json
        import tempfile

        class Config(WryModel):
            name: str = "test"
            count: int = 42

        config = Config()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "config.json"
            config.to_json_file(file_path)

            # Verify file was created
            assert file_path.exists()

            # Verify content
            with open(file_path) as f:
                data = json.load(f)
            assert data["name"] == "test"
            assert data["count"] == 42

    def test_get_sources_summary(self):
        """Test get_sources_summary method."""
        from wry import TrackedValue

        class Config(WryModel):
            name: str = "default"
            count: int = 0
            enabled: bool = False

        # Create with mixed sources
        config = Config.create_with_sources(
            {
                "name": TrackedValue("test", ValueSource.CLI),
                "count": TrackedValue(42, ValueSource.ENV),
                "enabled": TrackedValue(True, ValueSource.DEFAULT),
            }
        )

        summary = config.get_sources_summary()
        assert ValueSource.CLI in summary
        assert "name" in summary[ValueSource.CLI]
        assert ValueSource.ENV in summary
        assert "count" in summary[ValueSource.ENV]
        assert ValueSource.DEFAULT in summary
        assert "enabled" in summary[ValueSource.DEFAULT]

    def test_get_value_source(self):
        """Test get_value_source method."""
        from wry import TrackedValue

        class Config(WryModel):
            name: str = "default"

        config = Config.create_with_sources(
            {
                "name": TrackedValue("test", ValueSource.CLI),
            }
        )

        assert config.get_value_source("name") == ValueSource.CLI

    def test_field_constraints_methods(self):
        """Test constraint getter methods."""

        class Config(WryModel):
            count: int = Field(default=50, ge=0, le=100)

        config = Config()

        # Test get_field_constraints
        constraints = config.get_field_constraints("count")
        assert "ge" in constraints
        assert constraints["ge"] == 0
        assert "le" in constraints
        assert constraints["le"] == 100

        # Test get_field_minimum
        minimum = config.get_field_minimum("count")
        assert minimum == 0

        # Test get_field_maximum
        maximum = config.get_field_maximum("count")
        assert maximum == 100

        # Test get_field_range
        min_val, max_val = config.get_field_range("count")
        assert min_val == 0
        assert max_val == 100

    def test_get_field_default(self):
        """Test get_field_default method."""

        class Config(WryModel):
            name: str = "default_name"
            count: int = Field(default=42)

        config = Config()

        assert config.get_field_default("name") == "default_name"
        assert config.get_field_default("count") == 42

    def test_field_methods_with_invalid_field(self):
        """Test that field methods raise AttributeError for invalid fields."""
        import pytest

        class Config(WryModel):
            name: str = "default"

        config = Config()

        with pytest.raises(AttributeError, match="Field 'nonexistent' not found"):
            config.get_field_constraints("nonexistent")

        with pytest.raises(AttributeError, match="Field 'nonexistent' not found"):
            config.get_field_minimum("nonexistent")

        with pytest.raises(AttributeError, match="Field 'nonexistent' not found"):
            config.get_field_maximum("nonexistent")

        with pytest.raises(AttributeError, match="Field 'nonexistent' not found"):
            config.get_field_default("nonexistent")

    def test_extract_subset_with_missing_field_has_default(self):
        """Test extract_subset when field is missing but has default."""

        class SourceModel(WryModel):
            name: str = "source"

        class TargetModel(WryModel):
            name: str = "target"
            count: int = 42  # Has default

        source = SourceModel()
        result = TargetModel.extract_subset_from(source, TargetModel)

        assert result["name"] == "source"
        assert result["count"] == 42  # Uses default
