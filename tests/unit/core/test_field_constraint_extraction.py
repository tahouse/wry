"""Test field constraint extraction edge cases."""

from pydantic import BaseModel, Field

from wry.core.field_utils import extract_field_constraints


class TestFieldConstraintExtraction:
    """Test extracting constraints from field information."""

    def test_constraints_with_none_values_ignored(self):
        """Test that constraints with None values are not included."""

        class Model(BaseModel):
            # Field with mix of None and non-None constraints
            value: int = Field(
                default=0,
                ge=None,  # Should be ignored
                le=100,  # Should be included
                gt=None,  # Should be ignored
                lt=50,  # Should be included
                multiple_of=None,  # Should be ignored
            )

        field = Model.model_fields["value"]
        constraints = extract_field_constraints(field)

        # Only non-None constraints should be included
        assert "ge" not in constraints
        assert "le" in constraints and constraints["le"] == 100
        assert "gt" not in constraints
        assert "lt" in constraints and constraints["lt"] == 50
        assert "multiple_of" not in constraints

    def test_all_constraints_none(self):
        """Test field where all constraint values are None."""

        class Model(BaseModel):
            value: str = Field(default="text", min_length=None, max_length=None, pattern=None)

        field = Model.model_fields["value"]
        constraints = extract_field_constraints(field)

        # Should have no constraints (except maybe default)
        constraint_keys = [k for k in constraints.keys() if k != "default"]
        assert len(constraint_keys) == 0

    def test_explicit_zero_constraints(self):
        """Test that zero values are kept (not None)."""

        class Model(BaseModel):
            value: int = Field(
                default=10,
                ge=0,  # Zero should be kept
                multiple_of=1,  # Must be integer for int field
            )

        field = Model.model_fields["value"]
        constraints = extract_field_constraints(field)

        # Zero is a valid constraint value
        assert "ge" in constraints
        assert constraints["ge"] == 0
        assert "multiple_of" in constraints
        assert constraints["multiple_of"] == 1
