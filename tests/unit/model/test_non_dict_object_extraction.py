"""Test WryModel extraction from non-dict objects."""

from wry.core.model import WryModel


class TestNonDictObjectExtraction:
    """Test extraction from objects that are neither dicts nor have items()."""

    def test_extract_from_plain_object(self):
        """Test extraction from a plain object without items() method."""

        class PlainObject:
            def __init__(self):
                self.name = "test"
                self.value = 42
                self.flag = True
                self._private = "hidden"

        class Target(WryModel):
            name: str = "default"
            value: int = 0
            flag: bool = False
            _private: str = "default"

        obj = PlainObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Public attributes should be extracted
        assert result["name"] == "test"
        assert result["value"] == 42
        assert result["flag"] is True
        # Private attribute filtered by startswith("_")
        assert "_private" not in result

    def test_extract_from_object_all_methods(self):
        """Test extraction from object with only methods."""

        class MethodObject:
            def method1(self):
                return "m1"

            def method2(self):
                return "m2"

        class Target(WryModel):
            method1: str = "default1"
            method2: str = "default2"

        obj = MethodObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Methods are callable, should be filtered
        assert result["method1"] == "default1"
        assert result["method2"] == "default2"

    def test_extract_handles_exceptions_in_dir(self):
        """Test extraction when dir() behaves unusually."""

        class WeirdDirObject:
            def __init__(self):
                self.normal = "value"

            def __dir__(self):
                # Return attributes that might not exist
                return ["normal", "does_not_exist", "raises_error"]

            def __getattr__(self, name):
                if name == "raises_error":
                    raise TypeError("Error accessing attribute")
                raise AttributeError(f"No attribute {name}")

        class Target(WryModel):
            normal: str = "default"
            does_not_exist: str = "default"
            raises_error: str = "default"

        obj = WeirdDirObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Normal attribute works
        assert result["normal"] == "value"
        # Non-existent attributes use defaults
        assert result["does_not_exist"] == "default"
        assert result["raises_error"] == "default"
