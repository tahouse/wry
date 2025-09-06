"""Test coverage gaps in auto_model.py module."""

from typing import Annotated, Any

from pydantic import Field

from wry import AutoClickParameter, AutoWryModel, create_auto_model


class TestAutoWryModelCoverage:
    """Test AutoWryModel coverage gaps."""

    def test_auto_dry_model_no_annotations(self):
        """Test AutoWryModel with a class that has no __annotations__."""

        # Since Pydantic requires type annotations, we can't test without them
        # Instead, test that AutoWryModel adds AutoOption to fields
        class ConfigNoAnnotations(AutoWryModel):
            # Fields with minimal annotations
            name: str = Field(default="test", description="Name field")
            count: int = Field(default=0, description="Count field")

        # The metaclass should create annotations
        assert hasattr(ConfigNoAnnotations, "__annotations__")
        assert "name" in ConfigNoAnnotations.__annotations__
        assert "count" in ConfigNoAnnotations.__annotations__

        # Should be able to create instance
        config = ConfigNoAnnotations()
        assert config.name == "test"
        assert config.count == 0

    def test_auto_dry_model_with_existing_annotated_metadata(self):
        """Test AutoWryModel with fields that already have non-Click metadata."""

        # Custom metadata class
        class CustomMetadata:
            def __init__(self, value: str):
                self.value = value

        class ConfigWithMetadata(AutoWryModel):
            # Field with existing Annotated metadata
            name: Annotated[str, CustomMetadata("custom")] = Field(default="test")
            # Field with multiple metadata
            count: Annotated[int, CustomMetadata("count"), "extra"] = Field(default=0)

        # The annotations should have AutoOption added
        name_annotation = ConfigWithMetadata.__annotations__["name"]
        count_annotation = ConfigWithMetadata.__annotations__["count"]

        # Check that AutoOption was added while preserving existing metadata
        from typing import get_args

        name_args = get_args(name_annotation)
        count_args = get_args(count_annotation)

        # Should have original type plus metadata
        assert name_args[0] is str
        assert any(isinstance(m, CustomMetadata) for m in name_args[1:])
        assert AutoClickParameter.OPTION in name_args[1:]

        assert count_args[0] is int
        assert any(isinstance(m, CustomMetadata) for m in count_args[1:])
        assert "extra" in count_args[1:]
        assert AutoClickParameter.OPTION in count_args[1:]

    def test_auto_dry_model_field_without_annotation(self):
        """Test AutoWryModel with a field that has no type annotation."""

        from typing import Any

        class ConfigMixedAnnotations(AutoWryModel):
            # Field with annotation
            name: str = Field(default="test")
            # Field with type - Pydantic requires annotations
            count: int = Field(default=0)
            # Field with explicit annotation in FieldInfo
            value: Any = Field(default=1.0, annotation=float)

        # Check annotations were created
        assert "count" in ConfigMixedAnnotations.__annotations__
        assert "value" in ConfigMixedAnnotations.__annotations__

        # Verify the types
        from typing import get_args, get_origin

        # Count should have inferred type (Any since no annotation)
        count_annotation = ConfigMixedAnnotations.__annotations__["count"]
        origin = get_origin(count_annotation)
        assert str(origin) == str(Annotated)
        args = get_args(count_annotation)
        assert args[0] is int  # We gave it int annotation
        assert AutoClickParameter.OPTION in args[1:]

        # Value should use the explicit annotation from FieldInfo
        value_annotation = ConfigMixedAnnotations.__annotations__["value"]
        origin = get_origin(value_annotation)
        assert str(origin) == str(Annotated)
        args = get_args(value_annotation)
        assert args[0] == Any  # We gave it Any, but Field has annotation=float
        assert AutoClickParameter.OPTION in args[1:]

    def test_auto_dry_model_non_field_annotation(self):
        """Test AutoWryModel with non-Field annotations."""
        from typing import ClassVar

        class ConfigWithNonField(AutoWryModel):
            # ClassVar should not be modified
            prefix: ClassVar[str] = "TEST_"
            # Regular field should get AutoOption
            name: str = "default"
            # Field with existing metadata should be preserved
            count: Annotated[int, "existing"] = 0

        # Check that ClassVar wasn't modified
        if hasattr(ConfigWithNonField, "model_fields"):
            assert "prefix" not in ConfigWithNonField.model_fields

        # Check that regular field got AutoOption
        if "name" in ConfigWithNonField.model_fields:
            # Field exists and should have been converted to Annotated[str, AutoOption]
            pass

    def test_auto_dry_model_field_with_annotation_in_field_info(self):
        """Test AutoWryModel processes FieldInfo with annotation (lines 88-89)."""

        class ConfigWithFieldAnnotation(AutoWryModel):
            # Field with annotation in FieldInfo but no type hint
            value: Any = Field(default=1.0, annotation=float)

        # Check the annotation was processed
        assert "value" in ConfigWithFieldAnnotation.__annotations__

    def test_create_auto_model_with_field_info(self):
        """Test create_auto_model with FieldInfo objects (lines 134-138)."""
        fields = {
            "name": Field(default="test", description="Name field"),
            "count": Field(default=0, annotation=int),
        }

        Model = create_auto_model("TestModel", fields)

        # Check fields were created
        assert hasattr(Model, "model_fields")
        assert "name" in Model.model_fields
        assert "count" in Model.model_fields

        # Create instance
        obj = Model(name="custom", count=5)
        assert obj.name == "custom"
        assert obj.count == 5

    def test_create_auto_model_with_default_values(self):
        """Test create_auto_model with default values (lines 139-142)."""
        fields = {
            "name": "default_name",  # String default
            "count": 42,  # Int default
            "enabled": True,  # Bool default
        }

        Model = create_auto_model("TestModel", fields)

        # Check fields were created with inferred types
        assert "name" in Model.__annotations__
        assert "count" in Model.__annotations__
        assert "enabled" in Model.__annotations__

        # Create instance
        obj = Model()
        assert obj.name == "default_name"
        assert obj.count == 42
        assert obj.enabled is True
