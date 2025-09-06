"""Test edge cases in WryModel.extract_subset_from method."""

from collections import UserDict

from wry.core.model import WryModel


class TestExtractSubsetEdgeCases:
    """Test edge cases and error handling in extract_subset_from."""

    def test_extract_from_non_dict_non_model_object(self):
        """Test extracting from a plain object (not dict or BaseModel)."""

        class Target(WryModel):
            name: str = "default"
            value: int = 0
            hidden: str = "default"

        class PlainObject:
            def __init__(self):
                self.name = "plain"
                self.value = 42
                self._private = "private"
                self.hidden = "visible"

            def method(self):
                return "method"

            @property
            def computed(self):
                return "computed"

        source = PlainObject()
        result = WryModel.extract_subset_from(source, Target)

        # Should extract public attributes
        assert result["name"] == "plain"
        assert result["value"] == 42
        assert result["hidden"] == "visible"

        # Should not include private or callable
        assert "_private" not in result
        assert "method" not in result
        # Computed properties should work
        assert "computed" not in result  # Not a field in Target

    def test_extract_from_object_with_dir_override(self):
        """Test extracting from object with custom __dir__ method."""

        class Target(WryModel):
            exposed: str = "default"
            hidden: str = "default"

        class CustomDirObject:
            def __init__(self):
                self.exposed = "visible"
                self.hidden = "should_not_see"
                self.extra = "extra"

            def __dir__(self):
                # Only expose 'exposed' attribute
                return ["exposed"]

        source = CustomDirObject()
        result = WryModel.extract_subset_from(source, Target)

        # extract_subset_from doesn't use __dir__, it checks all attributes
        assert result["exposed"] == "visible"
        assert result["hidden"] == "should_not_see"
        assert "extra" not in result  # Not in Target

    def test_extract_from_dict_like_object(self):
        """Test extracting from dict-like objects (UserDict, etc)."""

        class Target(WryModel):
            key1: str = "default"
            key2: int = 0

        # UserDict is dict-like but not a dict - treated as object
        source = UserDict({"key1": "value1", "key2": 123, "extra": "ignored"})
        result = WryModel.extract_subset_from(source, Target)

        # Since UserDict is not a dict subclass, it's treated as an object
        # UserDict exposes the data attribute which contains the dict
        # But that's a private attribute, so values won't be extracted
        # Instead it will use defaults
        assert result.get("key1", "default") == "default"
        assert result.get("key2", 0) == 0

    def test_extract_handles_getattr_errors_gracefully(self):
        """Test that AttributeError and TypeError in getattr are handled."""

        class Target(WryModel):
            safe: str = "default"
            error_attr: str = "default"
            type_error: str = "default"

        class ProblematicObject:
            def __init__(self):
                self.safe = "safe_value"

            def __getattr__(self, name):
                if name == "error_attr":
                    raise AttributeError("Cannot access")
                elif name == "type_error":
                    raise TypeError("Wrong type")
                raise AttributeError(f"No attribute {name}")

        source = ProblematicObject()
        result = WryModel.extract_subset_from(source, Target)

        # Should get the safe attribute
        assert result["safe"] == "safe_value"
        # Attributes that raise errors use defaults
        assert result.get("error_attr") == "default"
        assert result.get("type_error") == "default"
