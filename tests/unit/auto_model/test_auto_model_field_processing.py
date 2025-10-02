"""Test AutoWryModel field processing edge cases."""

from typing import Any, ClassVar

from pydantic import Field

from wry import AutoWryModel


class TestAutoModelFieldProcessing:
    """Test how AutoWryModel processes various field configurations."""

    def test_field_with_annotation_in_field_info(self):
        """Test processing fields where FieldInfo has annotation attribute."""

        class ConfigWithAnnotatedField(AutoWryModel):
            # Simulate a field with annotation in FieldInfo
            value: Any = Field(default=10)

        # Manually set annotation on the field to test line 88
        if hasattr(ConfigWithAnnotatedField.model_fields["value"], "annotation"):
            ConfigWithAnnotatedField.model_fields["value"].annotation = int

        # The field should still work correctly
        config = ConfigWithAnnotatedField()
        assert config.value == 10

    def test_process_class_with_only_annotations(self):
        """Test a class that only has __annotations__ but no actual attributes."""

        class AnnotationOnlyModel(AutoWryModel):
            # These are only in __annotations__, not class attributes
            name: str
            value: int

        # Should still process correctly with defaults
        config = AnnotationOnlyModel(name="test", value=42)
        assert config.name == "test"
        assert config.value == 42

    def test_skip_class_level_non_field_attributes(self):
        """Test that non-field class attributes are skipped."""

        class ModelWithMixedAttributes(AutoWryModel):
            # Regular fields
            name: str = "default"

            # Class-level constants (should be skipped)
            CONSTANT: ClassVar[str] = "constant"

            # Methods are naturally skipped
            def method(self):
                return "method"

            @property
            def computed(self):
                return f"computed_{self.name}"

        config = ModelWithMixedAttributes()
        assert config.name == "default"
        # ClassVar should not be a field
        assert "CONSTANT" not in ModelWithMixedAttributes.model_fields
        assert hasattr(config, "method")  # methods are accessible on instances
        assert callable(config.method)  # and remain callable
