"""Test WryModel extraction methods for various object types."""

from wry.core.model import WryModel


class TestObjectExtraction:
    """Test extracting data from various object types."""

    def test_extract_from_object_with_callable_attributes(self):
        """Test that callable attributes are excluded from extraction."""

        class Source:
            def __init__(self):
                self.data = "value"

            def method(self):
                return "method result"

            @property
            def computed(self):
                return f"computed: {self.data}"

        class Target(WryModel):
            data: str = "default"
            computed: str = "default"

        source = Source()
        result = WryModel.extract_subset_from(source, Target)

        # Should get data, but computed property might not be extracted
        assert result["data"] == "value"
        # Properties might be treated as callables and skipped
        assert result.get("computed", "default") == "default"

    def test_extract_from_object_skips_private_attributes(self):
        """Test that private attributes are skipped during extraction."""

        class Source:
            def __init__(self):
                self.public = "public"
                self._protected = "protected"
                self.__private = "private"

        class Target(WryModel):
            public: str = "default"
            _protected: str = "default"
            __private: str = "default"

        source = Source()
        result = WryModel.extract_subset_from(source, Target)

        # Should only get public attributes
        assert result["public"] == "public"
        assert "_protected" not in result
        assert "__private" not in result

    def test_extract_handles_complex_attribute_errors(self):
        """Test extraction when getattr raises various exceptions."""

        class Source:
            def __init__(self):
                self.safe = "safe"

            def __getattr__(self, name):
                if name == "attr_error":
                    raise AttributeError("Custom attribute error")
                elif name == "type_error":
                    raise TypeError("Custom type error")
                elif name == "value_error":
                    raise ValueError("Should not stop extraction")
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        class Target(WryModel):
            safe: str = "default"
            attr_error: str = "default"
            type_error: str = "default"
            value_error: str = "default"

        source = Source()
        # Should handle AttributeError and TypeError gracefully
        result = WryModel.extract_subset_from(source, Target)

        assert result["safe"] == "safe"
        # These should use defaults due to errors
        assert result.get("attr_error", "default") == "default"
        assert result.get("type_error", "default") == "default"
        # ValueError might also be caught and use default
        assert result.get("value_error", "default") == "default"
