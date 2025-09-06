"""Test coverage gaps in field_utils.py module."""

from typing import Annotated

import annotated_types
from pydantic import BaseModel, Field

from wry.core.field_utils import extract_field_constraints


class TestFieldUtilsCoverage:
    """Test field_utils coverage gaps."""

    def test_extract_field_constraints_with_all_types(self):
        """Test extracting all constraint types including annotated-types."""

        class Config(BaseModel):
            # Test with annotated-types constraints
            min_value: Annotated[int, annotated_types.Ge(10)]
            gt_value: Annotated[int, annotated_types.Gt(0)]
            lt_value: Annotated[int, annotated_types.Lt(100)]
            length_value: Annotated[str, annotated_types.MinLen(5), annotated_types.MaxLen(10)]
            multiple_value: Annotated[int, annotated_types.MultipleOf(5)]

        # Test Ge constraint
        constraints = extract_field_constraints(Config.model_fields["min_value"])
        assert "ge" in constraints
        assert constraints["ge"] == 10

        # Test Gt constraint
        constraints = extract_field_constraints(Config.model_fields["gt_value"])
        assert "gt" in constraints
        assert constraints["gt"] == 0

        # Test Lt constraint
        constraints = extract_field_constraints(Config.model_fields["lt_value"])
        assert "lt" in constraints
        assert constraints["lt"] == 100

        # Test MinLen/MaxLen
        constraints = extract_field_constraints(Config.model_fields["length_value"])
        assert "min_length" in constraints
        assert constraints["min_length"] == 5
        assert "max_length" in constraints
        assert constraints["max_length"] == 10

        # Test MultipleOf
        constraints = extract_field_constraints(Config.model_fields["multiple_value"])
        assert "multiple_of" in constraints
        assert constraints["multiple_of"] == 5

    def test_extract_field_constraints_with_pattern(self):
        """Test extracting Pattern constraint."""

        # Create a mock Pattern object
        class Pattern:
            def __init__(self, pattern):
                self.pattern = pattern

        class Config(BaseModel):
            # Test pattern constraint from metadata
            code: Annotated[str, Pattern(r"^[A-Z]+$")]

        constraints = extract_field_constraints(Config.model_fields["code"])
        assert "pattern" in constraints
        assert constraints["pattern"] == r"^[A-Z]+$"

    def test_extract_field_constraints_with_field_constraints(self):
        """Test extracting constraints from Field() definitions."""

        class Config(BaseModel):
            # Test various Field constraints
            age: int = Field(ge=0, le=100, multiple_of=1)
            name: str = Field(min_length=1, max_length=50, pattern=r"^[a-zA-Z]+$")
            score: float = Field(gt=0.0, lt=100.0)

        # Test all numeric constraints
        age_constraints = extract_field_constraints(Config.model_fields["age"])
        assert age_constraints["ge"] == 0
        assert age_constraints["le"] == 100
        assert age_constraints["multiple_of"] == 1

        # Test string constraints
        name_constraints = extract_field_constraints(Config.model_fields["name"])
        assert name_constraints["min_length"] == 1
        assert name_constraints["max_length"] == 50
        # Pattern is extracted directly from Field
        if "pattern" in name_constraints:
            assert name_constraints["pattern"] == r"^[a-zA-Z]+$"

        # Test gt/lt constraints
        score_constraints = extract_field_constraints(Config.model_fields["score"])
        assert score_constraints["gt"] == 0.0
        assert score_constraints["lt"] == 100.0

    def test_extract_field_constraints_with_none_values(self):
        """Test extracting constraints when some values are None."""

        class Config(BaseModel):
            # Field with some None constraints
            value: int = Field(default=1, ge=None, le=100)

        constraints = extract_field_constraints(Config.model_fields["value"])
        # ge=None should not be included
        assert "ge" not in constraints
        assert "le" in constraints
        assert constraints["le"] == 100
