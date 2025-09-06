"""Test TYPE_CHECKING blocks in core modules."""

import sys


class TestTypeCheckingBlocks:
    """Test TYPE_CHECKING conditional imports in core modules."""

    def test_accessors_type_checking_import(self):
        """Test accessors module TYPE_CHECKING imports."""
        # Remove from cache
        module_name = "wry.core.accessors"
        if module_name in sys.modules:
            del sys.modules[module_name]

        # The module should work regardless of TYPE_CHECKING
        import wry.core.accessors

        # Verify key exports exist
        assert hasattr(wry.core.accessors, "SourceAccessor")
        assert hasattr(wry.core.accessors, "ConstraintsAccessor")
        assert hasattr(wry.core.accessors, "DefaultsAccessor")
        assert hasattr(wry.core.accessors, "MinimumAccessor")
        assert hasattr(wry.core.accessors, "MaximumAccessor")

    def test_env_utils_type_checking_import(self):
        """Test env_utils module TYPE_CHECKING imports."""
        # Remove from cache
        module_name = "wry.core.env_utils"
        if module_name in sys.modules:
            del sys.modules[module_name]

        import wry.core.env_utils

        # Verify functions exist
        assert hasattr(wry.core.env_utils, "get_env_values")
        assert hasattr(wry.core.env_utils, "get_env_var_names")
        assert hasattr(wry.core.env_utils, "print_env_vars")

    def test_sources_type_checking(self):
        """Test sources module with TYPE_CHECKING."""
        import wry.core.sources

        # Verify enums and classes exist
        assert hasattr(wry.core.sources, "ValueSource")
        assert hasattr(wry.core.sources, "TrackedValue")
        assert hasattr(wry.core.sources, "FieldWithSource")

    def test_field_utils_type_checking(self):
        """Test field_utils module imports."""
        import wry.core.field_utils

        # Verify functions exist
        assert hasattr(wry.core.field_utils, "extract_field_constraints")
        assert hasattr(wry.core.field_utils, "get_field_minimum")
        assert hasattr(wry.core.field_utils, "get_field_maximum")
