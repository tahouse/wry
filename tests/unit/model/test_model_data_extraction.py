"""Test WryModel data extraction and subset functionality."""

import pytest
from pydantic import ValidationError

from wry.core.model import WryModel


class TestDataExtraction:
    """Test extracting data subsets from various sources."""

    def test_extract_subset_from_dict(self):
        """Test extracting matching fields from a dictionary."""

        class Config(WryModel):
            name: str = "default"
            value: int = 0

        source = {"name": "test", "value": 42, "extra": "ignored"}
        result = WryModel.extract_subset_from(source, Config)

        assert result == {"name": "test", "value": 42}
        assert "extra" not in result

    def test_extract_subset_from_without_target_uses_calling_class(self):
        """Test that None target_model defaults to the calling class."""

        class Config(WryModel):
            name: str = "default"
            value: int = 0

        source = {"name": "test", "value": 42, "extra": "ignored"}
        result = Config.extract_subset_from(source, None)

        assert result == {"name": "test", "value": 42}

    def test_extract_subset_from_object_with_attribute_errors(self):
        """Test extraction when source object has problematic attributes."""

        class Target(WryModel):
            name: str = "default"
            value: int = 0
            prop: str = "default"

        class ProblematicSource:
            def __init__(self):
                self.name = "test"
                self._internal = "hidden"

            @property
            def value(self):
                raise AttributeError("Cannot access value")

            @property
            def prop(self):
                raise TypeError("Type error on prop")

            def method(self):
                return "callable"

        source = ProblematicSource()
        result = WryModel.extract_subset_from(source, Target)

        # Should get accessible attributes only
        assert result["name"] == "test"
        assert "_internal" not in result
        assert "method" not in result

    def test_extract_subset_from_model_instance(self):
        """Test extracting from another model instance."""

        class Source(WryModel):
            name: str = "source"
            value: int = 100
            extra: str = "extra"

        class Target(WryModel):
            name: str = "default"
            value: int = 0

        source = Source()
        result = WryModel.extract_subset_from(source, Target)

        assert result == {"name": "source", "value": 100}
        assert "extra" not in result

    def test_validation_error_for_missing_required_field(self):
        """Test that missing required fields raise validation errors."""

        class Config(WryModel):
            required_field: str  # No default
            optional_field: str = "default"

        # Should raise validation error
        with pytest.raises(ValidationError):
            Config(optional_field="set")
