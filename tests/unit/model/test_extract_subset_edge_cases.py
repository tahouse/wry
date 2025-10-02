"""Test extract_subset_from edge cases for improved coverage."""

from wry import WryModel


class TestExtractSubsetEdgeCases:
    """Test edge cases in extract_subset_from method."""

    def test_extract_subset_from_custom_object(self):
        """Test extract_subset_from with a custom object (not dict or BaseModel)."""

        class TargetModel(WryModel):
            name: str = "default"
            count: int = 0

        class CustomObject:
            """A custom object with attributes."""

            def __init__(self):
                self.name = "custom"
                self.count = 42
                self.extra_attr = "should be ignored"

            def some_method(self):
                return "method"

        source_obj = CustomObject()
        result = TargetModel.extract_subset_from(source_obj, TargetModel)

        assert result == {"name": "custom", "count": 42}
        assert "extra_attr" not in result
        assert "some_method" not in result

    def test_extract_subset_from_object_with_empty_dict(self):
        """Test extract_subset_from with object that has empty __dict__."""

        class TargetModel(WryModel):
            name: str = "default"
            count: int = 0

        # Create an object with class attributes instead of instance attributes
        class SourceClass:
            name = "class_attr"
            count = 100

            def method(self):
                pass

        source_obj = SourceClass()
        result = TargetModel.extract_subset_from(source_obj, TargetModel)

        # Should extract class attributes when instance dict is empty
        assert result["name"] == "class_attr"
        assert result["count"] == 100

    def test_extract_subset_from_object_with_inaccessible_attributes(self):
        """Test extract_subset_from handles AttributeError gracefully."""

        class TargetModel(WryModel):
            name: str = "default"
            count: int = 0

        class ProblematicObject:
            """Object with properties that raise errors."""

            name = "accessible"

            @property
            def count(self):
                raise AttributeError("Cannot access count")

            @property
            def other(self):
                raise TypeError("Type error")

        source_obj = ProblematicObject()
        result = TargetModel.extract_subset_from(source_obj, TargetModel)

        # Should extract accessible attributes
        assert result["name"] == "accessible"
        # count falls back to default when inaccessible
        assert result["count"] == 0
