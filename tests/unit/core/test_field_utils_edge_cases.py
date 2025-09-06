"""Test edge cases in field_utils module."""

from typing import Annotated

import annotated_types
from pydantic import BaseModel, Field

from wry.core.field_utils import extract_field_constraints, get_field_maximum, get_field_minimum


class TestFieldUtilsEdgeCases:
    """Test edge cases in field utility functions."""

    def test_extract_constraints_false_values(self):
        """Test that False/0 values are included (not filtered as None)."""

        class Model(BaseModel):
            # Field with 0 and False constraints
            value: int = Field(
                default=10,
                ge=0,  # Zero should be included
                gt=False,  # False (0) should be included
                le=None,  # None should be excluded
            )

        field = Model.model_fields["value"]
        constraints = extract_field_constraints(field)

        # 0 and False are valid constraint values
        assert "ge" in constraints
        assert constraints["ge"] == 0
        assert "gt" in constraints
        assert constraints["gt"] is False
        # None should be excluded
        assert "le" not in constraints

    def test_field_with_grouped_metadata(self):
        """Test field with GroupedMetadata in annotations."""

        class Model(BaseModel):
            # Use multiple constraints
            value: Annotated[int, annotated_types.Ge(10), annotated_types.Le(100), Field(default=50)]

        field = Model.model_fields["value"]
        constraints = extract_field_constraints(field)

        # Should extract constraints from grouped metadata
        assert "default" in constraints
        assert constraints["default"] == 50
        # GroupedMetadata constraints should be found
        assert any(c.ge == 10 for c in field.metadata if hasattr(c, "ge"))

    def test_get_minimum_maximum_with_no_constraints(self):
        """Test get_field_minimum/maximum when field has no constraints."""

        class Model(BaseModel):
            # Field with no min/max constraints
            unconstrained_field: str = "test"

        field = Model.model_fields["unconstrained_field"]
        minimum = get_field_minimum(field)
        maximum = get_field_maximum(field)

        # Should return None for both
        assert minimum is None
        assert maximum is None
