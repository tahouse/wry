"""Field extraction and constraint utilities."""

from typing import Any

from pydantic.fields import FieldInfo


def extract_field_constraints(field_info: FieldInfo) -> dict[str, Any]:
    """Extract all constraints from a Pydantic FieldInfo object.

    This is a standalone function that can be used without a model instance.
    Checks for both Pydantic field constraints (ge, gt, le, lt, etc.) and
    annotated-types constraints in metadata.

    Args:
        field_info: Pydantic FieldInfo object

    Returns:
        Dictionary of constraint names to values
    """
    constraints: dict[str, Any] = {}

    # Extract Pydantic field constraints
    for constraint in [
        "ge",
        "gt",
        "le",
        "lt",
        "min_length",
        "max_length",
        "pattern",
        "multiple_of",
        "allow_mutation",
        "frozen",
    ]:
        value = getattr(field_info, constraint, None)
        if value is not None:
            constraints[constraint] = value

    # Extract annotated-types constraints from metadata
    if hasattr(field_info, "metadata"):
        # Import here to avoid circular imports when used with type checking
        import annotated_types

        for metadata in field_info.metadata:
            if isinstance(metadata, annotated_types.Ge):
                constraints["ge"] = metadata.ge
            elif isinstance(metadata, annotated_types.Gt):
                constraints["gt"] = metadata.gt
            elif isinstance(metadata, annotated_types.Le):
                constraints["le"] = metadata.le
            elif isinstance(metadata, annotated_types.Lt):
                constraints["lt"] = metadata.lt
            elif isinstance(metadata, annotated_types.MinLen):
                constraints["min_length"] = metadata.min_length
            elif isinstance(metadata, annotated_types.MaxLen):
                constraints["max_length"] = metadata.max_length
            elif isinstance(metadata, annotated_types.MultipleOf):
                constraints["multiple_of"] = metadata.multiple_of
            elif hasattr(metadata, "__class__") and metadata.__class__.__name__ == "Pattern":
                constraints["pattern"] = metadata.pattern

    # Add default if present
    if field_info.default is not None:
        constraints["default"] = field_info.default

    return constraints


def get_field_minimum(field_info: FieldInfo) -> int | float | None:
    """Extract the minimum value from a field's constraints or default.

    Priority order:
    1. 'ge' (greater than or equal) constraint
    2. 'gt' (greater than) constraint
    3. Default value if numeric and positive

    Args:
        field_info: Pydantic FieldInfo object

    Returns:
        Minimum value or None if no minimum constraint
    """
    constraints = extract_field_constraints(field_info)

    # Check for 'ge' (greater than or equal)
    if "ge" in constraints:
        value = constraints["ge"]
        assert isinstance(value, int | float)
        return value
    elif "gt" in constraints:
        # For 'gt', the actual minimum is slightly above
        # but we return the constraint value for display
        value = constraints["gt"]
        assert isinstance(value, int | float)
        return value
    return None


def get_field_maximum(field_info: FieldInfo) -> int | float | None:
    """Extract the maximum value from a field's constraints.

    Priority order:
    1. 'le' (less than or equal) constraint
    2. 'lt' (less than) constraint

    Args:
        field_info: Pydantic FieldInfo object

    Returns:
        Maximum value or None if no maximum constraint
    """
    constraints = extract_field_constraints(field_info)

    # Check for 'le' (less than or equal)
    if "le" in constraints:
        value = constraints["le"]
        assert isinstance(value, int | float)
        return value
    elif "lt" in constraints:
        # For 'lt', the actual maximum is slightly below
        # but we return the constraint value for display
        value = constraints["lt"]
        assert isinstance(value, int | float)
        return value
    return None
