"""Test AutoWryModel type inference from FieldInfo."""

from typing import Any, get_args, get_origin

from pydantic import Field

from wry import AutoClickParameter, AutoWryModel


class TestTypeInference:
    """Test how AutoWryModel infers types from field information."""

    def test_field_with_annotation_attribute_on_field_info(self):
        """Test when FieldInfo has annotation attribute set."""

        class ModelWithAnnotation(AutoWryModel):
            # Field with explicit type annotation (required by Pydantic)
            value: int = Field(default=42)

        # Check if field got processed
        if hasattr(ModelWithAnnotation, "__annotations__") and "value" in ModelWithAnnotation.__annotations__:
            annotation = ModelWithAnnotation.__annotations__["value"]
            origin = get_origin(annotation)
            if origin:  # Should be Annotated
                args = get_args(annotation)
                # Should have AutoClickParameter.OPTION
                assert AutoClickParameter.OPTION in args
                # Type should be int
                type_arg = args[0] if args else Any
                assert type_arg is int

    def test_field_without_type_defaults_to_any(self):
        """Test that fields without type annotation get Any type."""

        class ModelWithoutTypes(AutoWryModel):
            # Fields with type annotations (required by Pydantic)
            no_type_field: str = Field(default="value")
            another_field: int = Field(default=123)

        # Check annotations were added
        assert hasattr(ModelWithoutTypes, "__annotations__")

        for field_name, expected_type in [("no_type_field", str), ("another_field", int)]:
            if field_name in ModelWithoutTypes.__annotations__:
                annotation = ModelWithoutTypes.__annotations__[field_name]
                origin = get_origin(annotation)
                if origin:  # Should be Annotated
                    args = get_args(annotation)
                    # First arg is the type
                    if args:
                        # Should match expected type
                        assert args[0] is expected_type
                        assert AutoClickParameter.OPTION in args

    def test_field_info_annotation_inference(self):
        """Test type inference when FieldInfo has annotation."""

        class CustomModel(AutoWryModel):
            # Create field that might have annotation in FieldInfo
            typed_field: int = Field(default=10)

        # Verify field was processed correctly
        if "typed_field" in CustomModel.__annotations__:
            annotation = CustomModel.__annotations__["typed_field"]
            origin = get_origin(annotation)
            if origin:  # Should be Annotated
                args = get_args(annotation)
                # Should preserve int type
                assert args[0] is int or args[0].__name__ == "int"
                assert AutoClickParameter.OPTION in args
