"""Test strict mode error handling in generate_click_parameters."""

import warnings
from typing import Annotated

import pytest
from pydantic import BaseModel

from wry import AutoOption, generate_click_parameters


class TestStrictModeErrors:
    """Test strict mode behavior in generate_click_parameters."""

    def test_duplicate_decorator_strict_mode_error(self):
        """Test that strict mode raises error on duplicate decorators."""

        class Config1(BaseModel):
            name: Annotated[str, AutoOption] = "default"

        class Config2(BaseModel):
            value: Annotated[int, AutoOption] = 0

        # Create a function and apply first decorator
        def base_func(**kwargs):
            pass

        # Apply first decorator - this should work
        decorated = generate_click_parameters(Config1, strict=True)(base_func)

        # Now decorated function has _wry_models attribute
        assert hasattr(decorated, "_wry_models")

        # Applying second decorator in strict mode should raise
        with pytest.raises(ValueError) as exc_info:
            generate_click_parameters(Config2, strict=True)(decorated)

        assert "already decorated" in str(exc_info.value)
        assert "strict=False" in str(exc_info.value)

    def test_duplicate_decorator_non_strict_warning(self):
        """Test that non-strict mode warns on duplicate decorators."""

        class Config1(BaseModel):
            name: Annotated[str, AutoOption] = "default"

        class Config2(BaseModel):
            value: Annotated[int, AutoOption] = 0

        def base_func(**kwargs):
            pass

        # Apply first decorator
        decorated = generate_click_parameters(Config1, strict=False)(base_func)

        # Second decorator should warn
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generate_click_parameters(Config2, strict=False)(decorated)

            assert len(w) == 1
            assert "already decorated" in str(w[0].message)

    def test_strict_mode_with_function_name(self):
        """Test that error message includes function name."""

        class Config(BaseModel):
            field: Annotated[str, AutoOption] = "value"

        def my_special_function(**kwargs):
            pass

        # Apply first decorator
        decorated = generate_click_parameters(Config, strict=True)(my_special_function)

        with pytest.raises(ValueError) as exc_info:
            generate_click_parameters(Config, strict=True)(decorated)

        # Should mention the function name in the error
        error_msg = str(exc_info.value)
        assert "my_special_function" in error_msg or "already decorated" in error_msg
