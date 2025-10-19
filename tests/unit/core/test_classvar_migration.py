"""Test ClassVar migration from unprefixed to wry_ prefixed names."""

import warnings
from typing import Any, ClassVar

import pytest
from pydantic import Field

from wry import AutoWryModel, WryModel


class TestClassVarMigration:
    """Test migration of ClassVars to wry_ prefixed names."""

    def test_env_prefix_migration_warning(self):
        """Test that using old env_prefix emits deprecation warning."""

        with pytest.warns(DeprecationWarning, match="'env_prefix' is deprecated, use 'wry_env_prefix'"):

            class Config(WryModel):
                env_prefix: ClassVar[str] = "MYAPP_"
                name: str = Field(default="test")

        # Should auto-migrate to wry_env_prefix
        assert hasattr(Config, "wry_env_prefix")
        assert Config.wry_env_prefix == "MYAPP_"

    def test_comma_separated_lists_migration_warning(self):
        """Test that using old comma_separated_lists emits deprecation warning."""

        with pytest.warns(
            DeprecationWarning, match="'comma_separated_lists' is deprecated, use 'wry_comma_separated_lists'"
        ):

            class Config(WryModel):
                comma_separated_lists: ClassVar[bool] = True
                tags: list[str] = Field(default_factory=list)

        # Should auto-migrate to wry_comma_separated_lists
        assert hasattr(Config, "wry_comma_separated_lists")
        assert Config.wry_comma_separated_lists is True

    def test_new_wry_prefix_no_warning(self):
        """Test that using new wry_ prefixed names doesn't emit warnings."""

        # Should not emit any warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            class Config(WryModel):
                wry_env_prefix: ClassVar[str] = "MYAPP_"
                wry_comma_separated_lists: ClassVar[bool] = True
                wry_boolean_off_prefix: ClassVar[str] = "disable"
                name: str = Field(default="test")

        assert Config.wry_env_prefix == "MYAPP_"
        assert Config.wry_comma_separated_lists is True
        assert Config.wry_boolean_off_prefix == "disable"

    def test_both_old_and_new_prefix_prefers_new(self):
        """Test that when both old and new are defined, new one is used and no warning emitted."""

        # Should NOT emit warning when both are defined (user already migrated)
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            class Config(WryModel):
                env_prefix: ClassVar[str] = "OLD_"
                wry_env_prefix: ClassVar[str] = "NEW_"
                name: str = Field(default="test")

        # Should use the new one (no migration happens if new exists)
        assert Config.wry_env_prefix == "NEW_"
        # Old one is still there but not used internally
        assert Config.env_prefix == "OLD_"

    def test_auto_wry_model_migration(self):
        """Test that AutoWryModel also migrates ClassVars."""

        with pytest.warns(DeprecationWarning, match="'env_prefix' is deprecated"):

            class Config(AutoWryModel):
                env_prefix: ClassVar[str] = "AUTO_"
                debug: bool = Field(default=False)

        assert Config.wry_env_prefix == "AUTO_"

    def test_boolean_off_prefix_new_feature(self):
        """Test the new wry_boolean_off_prefix ClassVar."""

        class Config(AutoWryModel):
            wry_boolean_off_prefix: ClassVar[str] = "disable"
            debug: bool = Field(default=False)
            enabled: bool = Field(default=True)

        # Should not emit any warnings (it's a new feature)
        import click

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        # Check that options use custom prefix
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--debug" in result.output
        assert "--disable-debug" in result.output
        assert "--enabled" in result.output
        assert "--disable-enabled" in result.output

    def test_migration_with_inheritance(self):
        """Test ClassVar migration works with inheritance."""

        with pytest.warns(DeprecationWarning, match="'env_prefix' is deprecated"):

            class BaseConfig(WryModel):
                env_prefix: ClassVar[str] = "BASE_"
                base_field: str = Field(default="base")

        # Child should inherit the migrated value
        class ChildConfig(BaseConfig):
            child_field: str = Field(default="child")

        # Child should have the migrated wry_env_prefix from parent
        assert hasattr(ChildConfig, "wry_env_prefix")
        # Note: The child gets the base class's wry_env_prefix through normal inheritance
        assert ChildConfig.wry_env_prefix == "BASE_"

    def test_no_migration_when_not_in_dict(self):
        """Test that migration only happens for ClassVars defined in the class itself."""

        class BaseConfig(WryModel):
            wry_env_prefix: ClassVar[str] = "BASE_"
            field: str = Field(default="test")

        # Child that inherits but doesn't redefine env_prefix shouldn't emit warning
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            class ChildConfig(BaseConfig):
                child_field: str = Field(default="child")

        # Should inherit from parent
        assert ChildConfig.wry_env_prefix == "BASE_"
