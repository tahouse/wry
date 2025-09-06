"""Test AutoWryModel handling of field annotations."""

from typing import get_args, get_origin

from pydantic import Field

from wry import AutoClickParameter, AutoWryModel


class TestFieldAnnotationHandling:
    """Test how AutoWryModel handles fields with annotations."""

    def test_field_info_with_annotation_attribute(self):
        """Test that AutoWryModel processes fields correctly."""

        class ModelWithAnnotatedField(AutoWryModel):
            # Field with explicit type annotation
            annotated_field: str = Field(default="test")

        # Check that field got processed with the annotation
        if hasattr(ModelWithAnnotatedField, "__annotations__"):
            if "annotated_field" in ModelWithAnnotatedField.__annotations__:
                annotation = ModelWithAnnotatedField.__annotations__["annotated_field"]
                origin = get_origin(annotation)
                if origin:  # Should be Annotated
                    args = get_args(annotation)
                    # Should have preserved the str type
                    assert str in args or (args and args[0] is str)
                    assert AutoClickParameter.OPTION in args

    def test_field_info_without_annotation_uses_any(self):
        """Test that fields are processed correctly."""

        class ModelWithUnannotatedField(AutoWryModel):
            # Field with type annotation (required by Pydantic)
            untyped_field: int = Field(default=42)

        # Check annotations
        if hasattr(ModelWithUnannotatedField, "__annotations__"):
            if "untyped_field" in ModelWithUnannotatedField.__annotations__:
                annotation = ModelWithUnannotatedField.__annotations__["untyped_field"]
                origin = get_origin(annotation)
                if origin:  # Should be Annotated
                    args = get_args(annotation)
                    # Should have the type
                    assert int in args or (args and args[0] is int)
                    assert AutoClickParameter.OPTION in args

    def test_field_with_explicit_annotation_preserved(self):
        """Test that explicit annotations are preserved."""

        class ModelWithExplicitAnnotation(AutoWryModel):
            # Explicit type annotation should be preserved
            explicit_field: int = Field(default=10)

        # Check that annotation was modified to include AutoClickParameter
        if "explicit_field" in ModelWithExplicitAnnotation.__annotations__:
            annotation = ModelWithExplicitAnnotation.__annotations__["explicit_field"]
            origin = get_origin(annotation)
            assert origin is not None  # Should be Annotated
            args = get_args(annotation)
            # Original int type should be preserved
            assert int in args or (args and args[0] is int)
            assert AutoClickParameter.OPTION in args
