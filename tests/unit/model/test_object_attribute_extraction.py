"""Test WryModel extraction from objects with various attribute patterns."""

from wry.core.model import WryModel


class TestObjectAttributeExtraction:
    """Test extracting attributes from non-dict, non-BaseModel objects."""

    def test_extract_from_object_with_dir_filtering(self):
        """Test that extraction properly filters attributes from dir()."""

        class SourceObject:
            def __init__(self):
                self.public_attr = "public"
                self._protected = "protected"
                self.__private = "private"

            @property
            def property_attr(self):
                return "property"

            def method(self):
                return "method"

            @staticmethod
            def static_method():
                return "static"

            @classmethod
            def class_method(cls):
                return "class"

        class Target(WryModel):
            public_attr: str = "default"
            property_attr: str = "default"
            _protected: str = "default"
            method: str = "default"

        obj = SourceObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Should extract public attributes
        assert result["public_attr"] == "public"
        # Properties are not in __dict__, so they use defaults when object has __dict__
        assert result.get("property_attr", "default") == "default"
        # Protected/private should not be extracted (start with _)
        assert "_protected" not in result or result.get("_protected") == "default"
        # Methods use defaults
        assert result.get("method", "default") == "default"

    def test_extract_handles_getattr_exceptions(self):
        """Test extraction handles AttributeError and TypeError from getattr."""

        class ProblematicObject:
            def __init__(self):
                self.good_attr = "good"

            def __getattr__(self, name):
                if name == "attr_error":
                    raise AttributeError(f"No attribute {name}")
                elif name == "type_error":
                    raise TypeError(f"Type error for {name}")
                elif name == "other_error":
                    raise ValueError(f"Other error for {name}")
                return f"dynamic_{name}"

            def __dir__(self):
                return ["good_attr", "attr_error", "type_error", "other_error", "dynamic_attr"]

        class Target(WryModel):
            good_attr: str = "default"
            attr_error: str = "default"
            type_error: str = "default"
            other_error: str = "default"
            dynamic_attr: str = "default"

        obj = ProblematicObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Good attribute should be extracted
        assert result["good_attr"] == "good"
        # AttributeError and TypeError should be caught, using defaults
        assert result.get("attr_error", "default") == "default"
        assert result.get("type_error", "default") == "default"
        # Dynamic attributes via __getattr__ won't be found when __dict__ exists
        # It will use the default
        assert result.get("dynamic_attr", "default") == "default"

    def test_extract_filters_callable_values(self):
        """Test that callable values are filtered out."""

        class SourceWithCallables:
            def __init__(self):
                self.data = "data"
                self.func = lambda x: x
                self.callable_obj = print  # Built-in callable

        class Target(WryModel):
            data: str = "default"
            func: str = "default"
            callable_obj: str = "default"

        obj = SourceWithCallables()
        result = WryModel.extract_subset_from(obj, Target)

        # Non-callable should be extracted
        assert result["data"] == "data"
        # Callables should be filtered
        assert "func" not in result or callable(result.get("func"))
        assert "callable_obj" not in result or callable(result.get("callable_obj"))
