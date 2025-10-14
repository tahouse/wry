"""Tests for AutoWryModel and WryModel inheritance."""

from typing import Annotated, Any, ClassVar

import click
import pytest
from click.testing import CliRunner
from pydantic import Field

from wry import AutoArgument, AutoExclude, AutoOption, AutoWryModel, WryModel, create_models, multi_model


class TestAutoWryModelInheritance:
    """Test inheritance with AutoWryModel."""

    def test_basic_inheritance(self):
        """Test that child class inherits parent fields and adds new ones."""

        class BaseConfig(AutoWryModel):
            base_field: str = Field(default="base_value", description="Base field")

        class ChildConfig(BaseConfig):
            child_field: str = Field(default="child_value", description="Child field")

        # Check that both fields exist
        assert "base_field" in ChildConfig.model_fields
        assert "child_field" in ChildConfig.model_fields

        # Check that both fields work
        config = ChildConfig()
        assert config.base_field == "base_value"
        assert config.child_field == "child_value"

        # Check that child field can be set
        config = ChildConfig(child_field="custom")
        assert config.child_field == "custom"

    def test_inheritance_cli_generation(self):
        """Test that CLI options are generated for both parent and child fields."""

        class BaseConfig(AutoWryModel):
            base_field: str = Field(default="base_value", description="Base field")

        class ChildConfig(BaseConfig):
            child_field: str = Field(default="child_value", description="Child field")

        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo(f"base={config.base_field}, child={config.child_field}")

        runner = CliRunner()

        # Check help includes both fields
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0
        assert "--base-field" in result.output
        assert "--child-field" in result.output
        assert "Base field" in result.output
        assert "Child field" in result.output

        # Test setting both fields
        result = runner.invoke(cmd, ["--base-field", "custom_base", "--child-field", "custom_child"])
        assert result.exit_code == 0
        assert "base=custom_base, child=custom_child" in result.output

    def test_multiple_levels_of_inheritance(self):
        """Test inheritance across multiple levels."""

        class Level1Config(AutoWryModel):
            field1: str = Field(default="value1", description="Field 1")

        class Level2Config(Level1Config):
            field2: str = Field(default="value2", description="Field 2")

        class Level3Config(Level2Config):
            field3: str = Field(default="value3", description="Field 3")

        # Check all fields exist
        assert "field1" in Level3Config.model_fields
        assert "field2" in Level3Config.model_fields
        assert "field3" in Level3Config.model_fields

        # Test with CLI
        @click.command()
        @Level3Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Level3Config(**kwargs)
            click.echo(f"{config.field1},{config.field2},{config.field3}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--field1", "a", "--field2", "b", "--field3", "c"])
        assert result.exit_code == 0
        assert "a,b,c" in result.output

    def test_inheritance_with_env_prefix(self):
        """Test that child class can inherit env_prefix."""

        class BaseConfig(AutoWryModel):
            env_prefix: ClassVar[str] = "BASE_"
            base_field: str = Field(default="base", description="Base field")

        class ChildConfig(BaseConfig):
            child_field: str = Field(default="child", description="Child field")

        # Check that env_prefix is inherited
        assert ChildConfig.env_prefix == "BASE_"

        # Test that both fields use the prefix
        env_vars = ChildConfig.get_env_values.__func__(ChildConfig)  # Get unbound method
        # The function should recognize both BASE_BASE_FIELD and BASE_CHILD_FIELD

    def test_inheritance_with_overridden_env_prefix(self):
        """Test that child class can override env_prefix."""

        class BaseConfig(AutoWryModel):
            env_prefix: ClassVar[str] = "BASE_"
            base_field: str = Field(default="base", description="Base field")

        class ChildConfig(BaseConfig):
            env_prefix: ClassVar[str] = "CHILD_"
            child_field: str = Field(default="child", description="Child field")

        # Check that env_prefix is overridden
        assert BaseConfig.env_prefix == "BASE_"
        assert ChildConfig.env_prefix == "CHILD_"

    def test_inheritance_with_mixed_annotations(self):
        """Test inheritance with different annotation types."""

        class BaseConfig(AutoWryModel):
            base_option: str = Field(default="option", description="Base option")
            base_arg: Annotated[str, AutoArgument] = Field(description="Base arg")

        class ChildConfig(BaseConfig):
            child_option: str = Field(default="child", description="Child option")
            child_excluded: Annotated[str, AutoExclude] = Field(default="excluded")

        # Check fields
        assert "base_option" in ChildConfig.model_fields
        assert "base_arg" in ChildConfig.model_fields
        assert "child_option" in ChildConfig.model_fields
        assert "child_excluded" in ChildConfig.model_fields

        # Test CLI generation
        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo("OK")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--base-option" in result.output
        assert "--child-option" in result.output
        assert "child-excluded" not in result.output  # Should be excluded

    def test_inheritance_with_constraints(self):
        """Test that constraints are inherited and can be added."""

        class BaseConfig(AutoWryModel):
            age: int = Field(default=25, ge=0, le=120, description="Age")

        class ChildConfig(BaseConfig):
            score: int = Field(default=50, ge=0, le=100, description="Score")

        config = ChildConfig()
        assert config.age == 25
        assert config.score == 50

        # Test constraints work
        with pytest.raises(ValueError):
            ChildConfig(age=150)  # Exceeds constraint

        with pytest.raises(ValueError):
            ChildConfig(score=150)  # Exceeds constraint

    def test_inheritance_with_source_tracking(self):
        """Test that source tracking works with inherited fields."""

        class BaseConfig(AutoWryModel):
            base_field: str = Field(default="base", description="Base field")

        class ChildConfig(BaseConfig):
            child_field: str = Field(default="child", description="Child field")

        @click.command()
        @ChildConfig.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = ChildConfig.from_click_context(ctx, **kwargs)
            click.echo(f"base_source={config.source.base_field.value}")
            click.echo(f"child_source={config.source.child_field.value}")

        runner = CliRunner()

        # Test with defaults
        result = runner.invoke(cmd, [])
        assert "base_source=default" in result.output
        assert "child_source=default" in result.output

        # Test with CLI args
        result = runner.invoke(cmd, ["--base-field", "custom_base", "--child-field", "custom_child"])
        assert "base_source=cli" in result.output
        assert "child_source=cli" in result.output

    def test_override_parent_field(self):
        """Test that child can override parent field definition."""

        class BaseConfig(AutoWryModel):
            field: str = Field(default="parent", description="Parent field")

        class ChildConfig(BaseConfig):
            # Override with different default and description
            field: str = Field(default="child", description="Child field")

        config = ChildConfig()
        assert config.field == "child"

        # Test CLI uses child description
        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "Child field" in result.output


class TestWryModelInheritance:
    """Test inheritance with base WryModel (not Auto)."""

    def test_wrymodel_inheritance_with_explicit_annotations(self):
        """Test WryModel inheritance with explicit AutoOption/AutoArgument."""

        class BaseConfig(WryModel):
            base_option: Annotated[str, AutoOption] = Field(default="base", description="Base")

        class ChildConfig(BaseConfig):
            child_option: Annotated[str, AutoOption] = Field(default="child", description="Child")

        # Test CLI generation
        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo(f"base={config.base_option}, child={config.child_option}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--base-option", "b", "--child-option", "c"])
        assert result.exit_code == 0
        assert "base=b, child=c" in result.output

    def test_wrymodel_inheritance_multiple_levels(self):
        """Test WryModel inheritance across multiple levels."""

        class Level1(WryModel):
            field1: Annotated[str, AutoOption] = Field(default="v1", description="Field 1")

        class Level2(Level1):
            field2: Annotated[str, AutoOption] = Field(default="v2", description="Field 2")

        class Level3(Level2):
            field3: Annotated[str, AutoOption] = Field(default="v3", description="Field 3")

        # All fields should be present
        assert "field1" in Level3.model_fields
        assert "field2" in Level3.model_fields
        assert "field3" in Level3.model_fields

        # Test instance creation
        config = Level3(field1="a", field2="b", field3="c")
        assert config.field1 == "a"
        assert config.field2 == "b"
        assert config.field3 == "c"

    def test_wrymodel_inheritance_with_source_tracking(self):
        """Test that WryModel inheritance works with source tracking."""

        class BaseConfig(WryModel):
            base_field: Annotated[str, AutoOption] = Field(default="base", description="Base")

        class ChildConfig(BaseConfig):
            child_field: Annotated[str, AutoOption] = Field(default="child", description="Child")

        @click.command()
        @ChildConfig.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = ChildConfig.from_click_context(ctx, **kwargs)
            click.echo(f"base={config.base_field}[{config.source.base_field.value}]")
            click.echo(f"child={config.child_field}[{config.source.child_field.value}]")

        runner = CliRunner()

        # Test with CLI args
        result = runner.invoke(cmd, ["--base-field", "b", "--child-field", "c"])
        assert "base=b[cli]" in result.output
        assert "child=c[cli]" in result.output

        # Test with defaults
        result = runner.invoke(cmd, [])
        assert "base=base[default]" in result.output
        assert "child=child[default]" in result.output

    def test_wrymodel_inheritance_with_arguments_and_options(self):
        """Test WryModel inheritance mixing arguments and options."""

        class BaseConfig(WryModel):
            base_arg: Annotated[str, AutoArgument] = Field(description="Base argument")
            base_opt: Annotated[str, AutoOption] = Field(default="opt", description="Base option")

        class ChildConfig(BaseConfig):
            child_arg: Annotated[str, AutoArgument] = Field(description="Child argument")
            child_opt: Annotated[str, AutoOption] = Field(default="child", description="Child option")

        # All fields should be present
        assert "base_arg" in ChildConfig.model_fields
        assert "base_opt" in ChildConfig.model_fields
        assert "child_arg" in ChildConfig.model_fields
        assert "child_opt" in ChildConfig.model_fields

        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo(f"{config.base_arg},{config.child_arg},{config.base_opt},{config.child_opt}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["base_val", "child_val", "--base-opt", "b", "--child-opt", "c"])
        assert result.exit_code == 0
        assert "base_val,child_val,b,c" in result.output

    def test_mixed_autowry_and_wrymodel_inheritance(self):
        """Test inheriting from AutoWryModel to add manual annotations."""

        class BaseConfig(AutoWryModel):
            auto_field: str = Field(default="auto", description="Auto field")

        class ChildConfig(BaseConfig):
            # This should still become an option (AutoWryModel processing)
            child_auto: str = Field(default="child", description="Child auto")
            # Explicit annotation should be preserved
            child_arg: Annotated[str, AutoArgument] = Field(description="Child arg")

        # Test both work
        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo("OK")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--auto-field" in result.output
        assert "--child-auto" in result.output
        # Arguments show in usage line
        assert result.exit_code == 0

    def test_wrymodel_to_autowrymodel_inheritance(self):
        """Test inheriting AutoWryModel from a base WryModel."""

        class BaseConfig(WryModel):
            # Explicit annotation
            base_field: Annotated[str, AutoOption] = Field(default="base", description="Base")

        class ChildConfig(BaseConfig, AutoWryModel):
            # Should automatically get AutoOption
            child_field: str = Field(default="child", description="Child")

        # Check both fields exist
        assert "base_field" in ChildConfig.model_fields
        assert "child_field" in ChildConfig.model_fields

        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo(f"{config.base_field},{config.child_field}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--base-field", "b", "--child-field", "c"])
        assert result.exit_code == 0
        assert "b,c" in result.output


class TestInheritanceEdgeCases:
    """Test edge cases with inheritance."""

    def test_empty_child_class(self):
        """Test child class with no additional fields."""

        class BaseConfig(AutoWryModel):
            field: str = Field(default="value", description="Field")

        class ChildConfig(BaseConfig):
            pass  # No new fields

        # Should still work
        config = ChildConfig()
        assert config.field == "value"

        # CLI should work
        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = ChildConfig(**kwargs)
            click.echo(config.field)

        runner = CliRunner()
        result = runner.invoke(cmd, ["--field", "custom"])
        assert "custom" in result.output

    def test_multiple_inheritance(self):
        """Test multiple inheritance with AutoWryModel."""

        class Mixin1(AutoWryModel):
            field1: str = Field(default="value1", description="Field 1")

        class Mixin2(AutoWryModel):
            field2: str = Field(default="value2", description="Field 2")

        class CombinedConfig(Mixin1, Mixin2):
            field3: str = Field(default="value3", description="Field 3")

        # All fields should be present
        assert "field1" in CombinedConfig.model_fields
        assert "field2" in CombinedConfig.model_fields
        assert "field3" in CombinedConfig.model_fields

        config = CombinedConfig()
        assert config.field1 == "value1"
        assert config.field2 == "value2"
        assert config.field3 == "value3"

    def test_inheritance_with_excluded_fields(self):
        """Test that excluded fields are handled correctly in inheritance."""

        class BaseConfig(AutoWryModel):
            public: str = Field(default="public", description="Public")
            excluded_base: Annotated[str, AutoExclude] = Field(default="excluded")

        class ChildConfig(BaseConfig):
            child_public: str = Field(default="child", description="Child public")
            excluded_child: Annotated[str, AutoExclude] = Field(default="also_excluded")

        # Excluded fields should not generate CLI options
        @click.command()
        @ChildConfig.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert "--public" in result.output
        assert "--child-public" in result.output
        assert "excluded-base" not in result.output
        assert "excluded-child" not in result.output

    def test_reprocessing_prevention(self):
        """Test that the same class is not processed multiple times."""

        class BaseConfig(AutoWryModel):
            field: str = Field(default="value")

        # Access the class multiple times
        assert hasattr(BaseConfig, "_autowrymodel_processed")
        assert BaseConfig._autowrymodel_processed is True

        # Try to trigger reprocessing (shouldn't happen)
        class ChildConfig(BaseConfig):
            child_field: str = Field(default="child")

        # Both should be marked as processed
        assert BaseConfig._autowrymodel_processed is True
        assert ChildConfig._autowrymodel_processed is True

        # Both should only have been processed once
        # (We can verify by checking that fields are correct)
        assert len(BaseConfig.model_fields) == 1
        assert len(ChildConfig.model_fields) == 2


@pytest.mark.filterwarnings("ignore:Function.*already decorated:UserWarning")
@pytest.mark.filterwarnings("ignore:The parameter.*is used more than once:UserWarning")
class TestMultiModelInheritance:
    """Test inheritance scenarios with multi-model commands."""

    def test_multi_model_with_inherited_models(self):
        """Test multi_model decorator with models that use inheritance."""

        class BaseServerConfig(AutoWryModel):
            host: str = Field(default="localhost", description="Server host")

        class ExtendedServerConfig(BaseServerConfig):
            port: int = Field(default=8080, description="Server port")

        class BaseDatabaseConfig(AutoWryModel):
            db_url: str = Field(default="sqlite:///app.db", description="Database URL")

        class ExtendedDatabaseConfig(BaseDatabaseConfig):
            pool_size: int = Field(default=5, description="Pool size")

        @click.command()
        @multi_model(ExtendedServerConfig, ExtendedDatabaseConfig)
        @click.pass_context
        def serve(ctx: click.Context, **kwargs: Any):
            configs = create_models(ctx, kwargs, ExtendedServerConfig, ExtendedDatabaseConfig)
            server = configs[ExtendedServerConfig]
            db = configs[ExtendedDatabaseConfig]
            click.echo(f"server={server.host}:{server.port}")
            click.echo(f"db={db.db_url}[{db.pool_size}]")

        runner = CliRunner()

        # Test with all inherited fields
        result = runner.invoke(
            serve, ["--host", "api.com", "--port", "3000", "--db-url", "postgres://db", "--pool-size", "10"]
        )
        assert result.exit_code == 0
        assert "server=api.com:3000" in result.output
        assert "db=postgres://db[10]" in result.output

        # Test help shows all fields
        result = runner.invoke(serve, ["--help"])
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--db-url" in result.output
        assert "--pool-size" in result.output

    def test_multi_model_with_shared_base_class(self):
        """Test multi_model when multiple models inherit from same base."""

        class CommonConfig(AutoWryModel):
            env_prefix: ClassVar[str] = "APP_"
            enabled: bool = Field(default=True, description="Enabled")

        class FeatureAConfig(CommonConfig):
            feature_a_value: str = Field(default="a", description="Feature A value")

        class FeatureBConfig(CommonConfig):
            feature_b_value: str = Field(default="b", description="Feature B value")

        # Both inherit 'enabled' field
        assert "enabled" in FeatureAConfig.model_fields
        assert "enabled" in FeatureBConfig.model_fields

        @click.command()
        @multi_model(FeatureAConfig, FeatureBConfig)
        @click.pass_context
        def main(ctx: click.Context, **kwargs: Any):
            configs = create_models(ctx, kwargs, FeatureAConfig, FeatureBConfig)
            a = configs[FeatureAConfig]
            b = configs[FeatureBConfig]
            click.echo(f"a={a.feature_a_value}[{a.enabled}]")
            click.echo(f"b={b.feature_b_value}[{b.enabled}]")

        runner = CliRunner()
        result = runner.invoke(main, ["--feature-a-value", "custom_a", "--feature-b-value", "custom_b"])
        assert result.exit_code == 0
        assert "a=custom_a[True]" in result.output
        assert "b=custom_b[True]" in result.output

    def test_multi_model_with_three_level_inheritance(self):
        """Test multi_model with deep inheritance hierarchies."""

        class Level1(AutoWryModel):
            field1: str = Field(default="v1", description="Level 1")

        class Level2(Level1):
            field2: str = Field(default="v2", description="Level 2")

        class Level3(Level2):
            field3: str = Field(default="v3", description="Level 3")

        class OtherConfig(AutoWryModel):
            other: str = Field(default="other", description="Other field")

        @click.command()
        @multi_model(Level3, OtherConfig)
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            configs = create_models(ctx, kwargs, Level3, OtherConfig)
            l3 = configs[Level3]
            other = configs[OtherConfig]
            click.echo(f"level3={l3.field1},{l3.field2},{l3.field3}")
            click.echo(f"other={other.other}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--field1", "a", "--field2", "b", "--field3", "c", "--other", "d"])
        assert result.exit_code == 0
        assert "level3=a,b,c" in result.output
        assert "other=d" in result.output

    def test_multi_model_inheritance_with_source_tracking(self):
        """Test that source tracking works with inherited multi-models."""

        class BaseConfig(AutoWryModel):
            base_field: str = Field(default="base", description="Base")

        class ExtendedConfig(BaseConfig):
            extended_field: str = Field(default="extended", description="Extended")

        class OtherConfig(AutoWryModel):
            other_field: str = Field(default="other", description="Other")

        @click.command()
        @multi_model(ExtendedConfig, OtherConfig)
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            configs = create_models(ctx, kwargs, ExtendedConfig, OtherConfig)
            ext = configs[ExtendedConfig]
            other = configs[OtherConfig]
            click.echo(f"base={ext.base_field}[{ext.source.base_field.value}]")
            click.echo(f"extended={ext.extended_field}[{ext.source.extended_field.value}]")
            click.echo(f"other={other.other_field}[{other.source.other_field.value}]")

        runner = CliRunner()

        # Test with defaults
        result = runner.invoke(cmd, [])
        assert "base=base[default]" in result.output
        assert "extended=extended[default]" in result.output
        assert "other=other[default]" in result.output

        # Test with CLI args
        result = runner.invoke(cmd, ["--base-field", "b", "--extended-field", "e", "--other-field", "o"])
        assert "base=b[cli]" in result.output
        assert "extended=e[cli]" in result.output
        assert "other=o[cli]" in result.output

    def test_multi_model_mixed_wrymodel_types(self):
        """Test multi_model with both WryModel and AutoWryModel inherited classes."""

        class BaseWry(WryModel):
            wry_field: Annotated[str, AutoOption] = Field(default="wry", description="WryModel field")

        class ExtendedWry(BaseWry):
            ext_wry: Annotated[str, AutoOption] = Field(default="ext", description="Extended WryModel")

        class BaseAuto(AutoWryModel):
            auto_field: str = Field(default="auto", description="AutoWryModel field")

        class ExtendedAuto(BaseAuto):
            ext_auto: str = Field(default="ext_auto", description="Extended AutoWryModel")

        @click.command()
        @multi_model(ExtendedWry, ExtendedAuto)
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            configs = create_models(ctx, kwargs, ExtendedWry, ExtendedAuto)
            wry = configs[ExtendedWry]
            auto = configs[ExtendedAuto]
            click.echo(f"wry={wry.wry_field},{wry.ext_wry}")
            click.echo(f"auto={auto.auto_field},{auto.ext_auto}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--wry-field", "w", "--ext-wry", "ew", "--auto-field", "a", "--ext-auto", "ea"])
        assert result.exit_code == 0
        assert "wry=w,ew" in result.output
        assert "auto=a,ea" in result.output
