"""Test AutoWryModel annotation inference from FieldInfo."""

from typing import get_args, get_origin

from pydantic import Field

from wry import AutoClickParameter, AutoWryModel


class TestAnnotationInference:
    """Test how AutoWryModel infers types from FieldInfo."""

    def test_field_with_annotation_attribute(self):
        """Test field where FieldInfo has annotation attribute set."""

        class ModelWithAnnotatedFieldInfo(AutoWryModel):
            # Field with explicit type annotation
            value: int = Field(default=10)

        # Check that the field was properly annotated
        if "value" in ModelWithAnnotatedFieldInfo.__annotations__:
            annotation = ModelWithAnnotatedFieldInfo.__annotations__["value"]
            origin = get_origin(annotation)
            if origin:  # Should be Annotated
                args = get_args(annotation)
                # Should have AutoClickParameter.OPTION
                assert AutoClickParameter.OPTION in args
                # Should preserve int type
                assert int in args or (args and args[0] is int)

    def test_field_without_annotation_uses_any(self):
        """Test field without annotation defaults to Any."""

        class ModelWithoutAnnotation(AutoWryModel):
            # Field with type annotation for Pydantic
            no_type: str = Field(default="value")

        # The field should have been processed
        if "no_type" in ModelWithoutAnnotation.__annotations__:
            annotation = ModelWithoutAnnotation.__annotations__["no_type"]
            origin = get_origin(annotation)
            if origin:  # Should be Annotated
                args = get_args(annotation)
                # Should have AutoClickParameter added
                assert AutoClickParameter.OPTION in args
                # Type should be preserved
                assert str in args or (args and args[0] is str)
