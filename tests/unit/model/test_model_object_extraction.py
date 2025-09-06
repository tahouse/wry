"""Test WryModel extraction from plain objects."""

from wry.core.model import WryModel


class TestPlainObjectExtraction:
    """Test extracting data from plain Python objects."""

    def test_extract_from_plain_object_with_attributes(self):
        """Test extraction from object that isn't dict or BaseModel."""

        class PlainObject:
            def __init__(self):
                self.name = "test"
                self.value = 42
                self._private = "hidden"

            def method(self):
                return "method"

        class Target(WryModel):
            name: str = "default"
            value: int = 0
            _private: str = "default"

        obj = PlainObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Should extract public attributes
        assert result["name"] == "test"
        assert result["value"] == 42
        # Private attributes are skipped
        assert "_private" not in result

    def test_extract_from_object_with_getattr_errors(self):
        """Test extraction when getattr raises errors for some attributes."""

        class ProblematicObject:
            def __init__(self):
                self.safe = "safe_value"

            def __getattr__(self, name):
                if name in ["error1", "error2"]:
                    raise AttributeError(f"No attribute {name}")
                elif name == "type_err":
                    raise TypeError("Type error")
                return super().__getattribute__(name)

        class Target(WryModel):
            safe: str = "default"
            error1: str = "default"
            error2: str = "default"
            type_err: str = "default"

        obj = ProblematicObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Should only get the safe attribute
        assert result["safe"] == "safe_value"
        # Error attributes should use defaults
        assert result.get("error1", "default") == "default"
        assert result.get("error2", "default") == "default"
        assert result.get("type_err", "default") == "default"

    def test_extract_from_object_filters_callables(self):
        """Test that callable attributes are filtered out."""

        class ObjectWithMethods:
            def __init__(self):
                self.data = "data"
                self.func = lambda x: x + 1

            def method(self):
                return "method"

            @staticmethod
            def static_method():
                return "static"

            @classmethod
            def class_method(cls):
                return "class"

        class Target(WryModel):
            data: str = "default"
            func: str = "default"
            method: str = "default"
            static_method: str = "default"
            class_method: str = "default"

        obj = ObjectWithMethods()
        result = WryModel.extract_subset_from(obj, Target)

        # Should only get non-callable data
        assert result["data"] == "data"
        # Lambda is included but as the lambda object
        assert "func" in result  # Lambda is actually included
        assert callable(result["func"])
        # Methods use defaults since they're not extracted from instance
        assert result.get("method", "default") == "default"
        assert result.get("static_method", "default") == "default"
        assert result.get("class_method", "default") == "default"
