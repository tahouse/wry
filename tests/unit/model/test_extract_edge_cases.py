"""Test edge cases in WryModel.extract_subset_from."""

from wry.core.model import WryModel


class TestExtractEdgeCases:
    """Test edge cases in extract_subset_from method."""

    def test_extract_from_object_without_mapping_protocol(self):
        """Test extraction from object that's not Mapping but has items()."""

        class FakeDict:
            """Object with items() but not a Mapping."""

            def items(self):
                return [("key1", "value1"), ("key2", "value2")]

            def __dir__(self):
                return ["key1", "key2", "items"]

        class Target(WryModel):
            key1: str = "default1"
            key2: str = "default2"
            key3: str = "default3"

        obj = FakeDict()
        result = WryModel.extract_subset_from(obj, Target)

        # Should try object attribute extraction
        # Since it has items() but isn't a Mapping, it goes to else branch
        assert "key1" in result
        assert "key2" in result

    def test_extract_from_object_with_only_callable_attributes(self):
        """Test extraction from object with only methods."""

        class MethodOnlyObject:
            def method1(self):
                return "m1"

            def method2(self):
                return "m2"

            @property
            def prop(self):
                return "prop_value"

        class Target(WryModel):
            method1: str = "default"
            method2: str = "default"
            prop: str = "default"

        obj = MethodOnlyObject()
        result = WryModel.extract_subset_from(obj, Target)

        # Methods should be filtered out
        assert result.get("method1") == "default"
        assert result.get("method2") == "default"
        # Properties should work
        assert result.get("prop") == "prop_value"

    def test_extract_handles_both_attribute_and_type_errors(self):
        """Test handling of both AttributeError and TypeError in getattr."""

        class ProblematicAttributes:
            def __init__(self):
                self.normal = "normal_value"

            def __getattr__(self, name):
                if name == "raises_attribute_error":
                    raise AttributeError("Attribute error")
                elif name == "raises_type_error":
                    raise TypeError("Type error")
                elif name == "raises_other":
                    raise ValueError("Other error")
                return f"dynamic_{name}"

            def __dir__(self):
                return ["normal", "raises_attribute_error", "raises_type_error", "raises_other"]

        class Target(WryModel):
            normal: str = "default"
            raises_attribute_error: str = "default_attr"
            raises_type_error: str = "default_type"
            raises_other: str = "default_other"

        obj = ProblematicAttributes()
        result = WryModel.extract_subset_from(obj, Target)

        # Normal attribute works
        assert result["normal"] == "normal_value"
        # AttributeError and TypeError are caught
        assert result.get("raises_attribute_error") == "default_attr"
        assert result.get("raises_type_error") == "default_type"
        # Other errors might propagate or be caught elsewhere

    def test_extract_with_private_attributes(self):
        """Test that private attributes are filtered."""

        class WithPrivates:
            def __init__(self):
                self.public = "public"
                self._protected = "protected"
                self.__private = "private"

        class Target(WryModel):
            public: str = "default"
            _protected: str = "default"
            __private: str = "default"

        obj = WithPrivates()
        result = WryModel.extract_subset_from(obj, Target)

        # Only public attributes extracted
        assert result["public"] == "public"
        # Protected and private filtered by startswith("_") - should use defaults
        assert "_protected" not in result or result.get("_protected") == "default"
        assert "__private" not in result or result.get("__private") == "default"
