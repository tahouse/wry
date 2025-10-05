"""Test Pydantic field aliases with Click options.

This module tests Pydantic alias support in wry:
1. Using alias with explicit click.option() decorators
2. Using alias to auto-generate Click option names (v0.3.2+)

## Summary:

### Fully Supported (v0.3.2+):
```python
class Config(AutoWryModel):
    # No configuration needed! WryModel sets validate_by_name=True and validate_by_alias=True

    # Pattern 1: Auto-generated options (alias controls option name)
    db_url: str = Field(alias='database_url', default="...")
    # Generates: --database-url option

    # Pattern 2: Explicit options (alias bridges field name and option name)
    database_connection_string: Annotated[
        str,
        click.option("--db-url", "-d", default="...")
    ] = Field(alias='db_url', default="...")
```

**Benefits:**
- Concise Python field names, descriptive CLI options
- No configuration required (works out of the box)
- Full source tracking support
- JSON config accepts both field names and aliases

**How it works:**
- WryModel sets `validate_by_name=True` and `validate_by_alias=True` by default
- Aliases automatically control auto-generated option names and env var names
- `from_click_context()` maps aliases to field names for source tracking

## References:
- Pydantic alias docs: https://docs.pydantic.dev/latest/concepts/fields/#field-aliases
- TODO.md: Custom CLI option names section
"""

from typing import Annotated, Any

import click
from click.testing import CliRunner
from pydantic import ConfigDict, Field

from wry import AutoWryModel, WryModel


class TestFieldAliasWithExplicitClickOption:
    """Test using Pydantic alias to match Click's derived parameter name.

    This pattern works today and allows:
    - Descriptive Python field names
    - Concise CLI option names
    - Alias bridges the gap between them
    """

    def test_alias_matches_click_derived_name(self):
        """Test that alias matching Click's derived name works correctly."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            # Python field: database_connection_string (descriptive)
            # Click option: --db-url (concise)
            # Alias: db_url (matches Click's derived parameter name)
            database_connection_string: Annotated[
                str, click.option("--db-url", "-d", help="Database URL", default="sqlite:///app.db")
            ] = Field(alias="db_url", default="sqlite:///app.db")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"db={config.database_connection_string}")

        runner = CliRunner()

        # Test with CLI option
        result = runner.invoke(cmd, ["--db-url", "postgres://localhost/mydb"])
        assert result.exit_code == 0
        assert "db=postgres://localhost/mydb" in result.output

        # Test with short option
        result = runner.invoke(cmd, ["-d", "mysql://localhost/db"])
        assert result.exit_code == 0
        assert "db=mysql://localhost/db" in result.output

        # Test default value
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "db=sqlite:///app.db" in result.output

    def test_alias_with_multiple_fields(self):
        """Test multiple fields using alias pattern."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            database_connection_string: Annotated[str, click.option("--db-url", "-d")] = Field(
                alias="db_url", default="sqlite:///app.db"
            )

            maximum_connection_pool_size: Annotated[int, click.option("--pool-size", "-p")] = Field(
                alias="pool_size", default=5, ge=1, le=100
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"db={config.database_connection_string}")
            click.echo(f"pool={config.maximum_connection_pool_size}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--db-url", "postgres://db", "--pool-size", "20"])

        assert result.exit_code == 0
        assert "db=postgres://db" in result.output
        assert "pool=20" in result.output

    def test_alias_with_source_tracking(self):
        """Test that source tracking works correctly with aliases.

        This test verifies that from_click_context properly handles Pydantic
        aliases and tracks sources correctly.
        """

        class Config(WryModel):
            model_config = ConfigDict(populate_by_name=True)

            database_connection_string: Annotated[str, click.option("--db-url", default="sqlite:///app.db")] = Field(
                alias="db_url", default="sqlite:///app.db"
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"db={config.database_connection_string}")
            click.echo(f"source={config.source.database_connection_string.value}")

        runner = CliRunner()

        # Test CLI source - should now work with alias support!
        result = runner.invoke(cmd, ["--db-url", "postgres://db"])
        assert result.exit_code == 0
        assert "db=postgres://db" in result.output
        assert "source=cli" in result.output

        # Test default source
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "db=sqlite:///app.db" in result.output
        assert "source=default" in result.output

    def test_alias_does_not_break_model_dump(self):
        """Test that model_dump works correctly with aliases."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            database_connection_string: Annotated[str, click.option("--db-url")] = Field(
                alias="db_url", default="sqlite:///app.db"
            )

        config = Config(db_url="postgres://localhost/mydb")

        # Dump without alias (uses field name)
        dumped = config.model_dump()
        assert "database_connection_string" in dumped
        assert dumped["database_connection_string"] == "postgres://localhost/mydb"

        # Dump with alias (uses alias name)
        dumped_alias = config.model_dump(by_alias=True)
        assert "db_url" in dumped_alias
        assert dumped_alias["db_url"] == "postgres://localhost/mydb"

    def test_alias_with_json_serialization(self):
        """Test JSON serialization with aliases."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            database_connection_string: Annotated[str, click.option("--db-url")] = Field(
                alias="db_url", default="sqlite:///app.db"
            )

        config = Config(db_url="postgres://localhost/mydb")

        # JSON dump without alias
        import json

        json_data = json.loads(config.model_dump_json())
        assert "database_connection_string" in json_data

        # JSON dump with alias
        json_alias = json.loads(config.model_dump_json(by_alias=True))
        assert "db_url" in json_alias

    def test_alias_with_validation_error(self):
        """Test that validation errors reference the correct field."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            maximum_connection_pool_size: Annotated[int, click.option("--pool-size")] = Field(
                alias="pool_size", ge=1, le=100
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            try:
                config = Config(**kwargs)
                click.echo(f"pool={config.maximum_connection_pool_size}")
            except Exception as e:
                click.echo(f"error={str(e)}")

        runner = CliRunner()

        # Test with invalid value (out of range)
        result = runner.invoke(cmd, ["--pool-size", "200"])
        assert result.exit_code == 0
        assert "error=" in result.output  # Validation should fail

    def test_alias_with_help_text(self):
        """Test that help text displays correctly with aliased fields."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            database_connection_string: Annotated[
                str, click.option("--db-url", "-d", help="Database connection URL")
            ] = Field(alias="db_url", default="sqlite:///app.db")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        assert result.exit_code == 0
        assert "--db-url" in result.output
        assert "-d" in result.output
        assert "Database connection URL" in result.output


class TestFieldAliasForAutoGeneratedOptions:
    """Test using alias to define auto-generated Click option names.

    IMPLEMENTED in v0.3.2+: Aliases now automatically control the generated
    CLI option names and environment variable names.
    """

    def test_alias_used_for_auto_option_name(self):
        """Test that alias is used for auto-generated option name (IMPLEMENTED v0.3.2+)."""

        # This behavior is now fully implemented!
        # wry checks for alias and uses it for auto-generated options

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            # --database-url option generated from alias
            # Python field: db_url (concise)
            # Alias: database_url (descriptive CLI option)
            db_url: str = Field(alias="database_url", default="sqlite:///app.db", description="Database connection URL")

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"db={config.db_url}")

        runner = CliRunner()

        # Now works with --database-url (uses alias)
        result = runner.invoke(cmd, ["--help"])
        assert "--database-url" in result.output

        # Test that it actually works
        result = runner.invoke(cmd, ["--database-url", "postgres://localhost/db"])
        assert result.exit_code == 0
        assert "db=postgres://localhost/db" in result.output

    def test_alias_precedence_with_env_vars(self):
        """Test how alias affects environment variable naming (IMPLEMENTED v0.3.2+)."""

        import os

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)
            env_prefix = "MYAPP_"

            db_url: str = Field(alias="database_url", default="sqlite:///app.db")

        # Now uses alias for env var: MYAPP_DATABASE_URL
        # This is consistent with CLI option naming

        try:
            os.environ["MYAPP_DATABASE_URL"] = "postgres://localhost/db"

            config = Config.load_from_env()
            assert config.db_url == "postgres://localhost/db"
        finally:
            os.environ.pop("MYAPP_DATABASE_URL", None)

    def test_alias_auto_generation_with_source_tracking(self):
        """Test that auto-generated alias-based options work with source tracking."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)
            env_prefix = "TEST_"

            db_url: str = Field(alias="database_url", default="sqlite:///app.db", description="Database URL")
            pool_size: int = Field(alias="connection_pool_size", default=5, description="Pool size")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"db={config.db_url}")
            click.echo(f"pool={config.pool_size}")
            click.echo(f"db_source={config.source.db_url.value}")
            click.echo(f"pool_source={config.source.pool_size.value}")

        runner = CliRunner()

        # Test CLI source with alias-based option names
        result = runner.invoke(cmd, ["--database-url", "postgres://db", "--connection-pool-size", "20"])
        assert result.exit_code == 0
        assert "db=postgres://db" in result.output
        assert "pool=20" in result.output
        assert "db_source=cli" in result.output
        assert "pool_source=cli" in result.output

        # Test default source
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "db=sqlite:///app.db" in result.output
        assert "pool=5" in result.output
        assert "db_source=default" in result.output
        assert "pool_source=default" in result.output

    def test_alias_auto_generation_with_env_vars_and_source_tracking(self):
        """Test that env vars work with auto-generated alias-based options and source tracking."""

        import os

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)
            env_prefix = "DBTEST_"

            db_url: str = Field(alias="database_url", default="sqlite:///app.db")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"db={config.db_url}")
            click.echo(f"source={config.source.db_url.value}")

        runner = CliRunner()

        try:
            # Set env var using alias name (consistent with CLI option)
            os.environ["DBTEST_DATABASE_URL"] = "postgres://from-env/db"

            # Test that env var is picked up
            result = runner.invoke(cmd, [])
            assert result.exit_code == 0
            assert "db=postgres://from-env/db" in result.output
            assert "source=env" in result.output

            # Test that CLI overrides env var
            result = runner.invoke(cmd, ["--database-url", "postgres://from-cli/db"])
            assert result.exit_code == 0
            assert "db=postgres://from-cli/db" in result.output
            assert "source=cli" in result.output

        finally:
            os.environ.pop("DBTEST_DATABASE_URL", None)

    def test_alias_auto_generation_with_json_and_source_tracking(self):
        """Test that JSON config works with auto-generated alias-based options and source tracking."""

        import json
        import os
        import tempfile

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            db_url: str = Field(alias="database_url", default="sqlite:///app.db")
            pool_size: int = Field(alias="connection_pool_size", default=5)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # JSON can use either field name or alias (thanks to populate_by_name=True)
            json.dump({"database_url": "postgres://from-json/db", "connection_pool_size": 10}, f)
            config_file = f.name

        try:

            @click.command()
            @Config.generate_click_parameters()
            @click.pass_context
            def cmd(ctx: click.Context, **kwargs: Any):
                config = Config.from_click_context(ctx, **kwargs)
                click.echo(f"db={config.db_url}")
                click.echo(f"pool={config.pool_size}")
                click.echo(f"db_source={config.source.db_url.value}")
                click.echo(f"pool_source={config.source.pool_size.value}")

            runner = CliRunner()

            # Test JSON source
            result = runner.invoke(cmd, ["--config", config_file])
            assert result.exit_code == 0
            assert "db=postgres://from-json/db" in result.output
            assert "pool=10" in result.output
            assert "db_source=json" in result.output
            assert "pool_source=json" in result.output

            # Test CLI overrides JSON
            result = runner.invoke(cmd, ["--config", config_file, "--database-url", "postgres://from-cli/db"])
            assert result.exit_code == 0
            assert "db=postgres://from-cli/db" in result.output
            assert "pool=10" in result.output  # Still from JSON
            assert "db_source=cli" in result.output
            assert "pool_source=json" in result.output

        finally:
            os.unlink(config_file)

    def test_alias_auto_generation_precedence_all_sources(self):
        """Test complete precedence chain: CLI > ENV > JSON > DEFAULT with alias-based options."""

        import json
        import os
        import tempfile

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)
            env_prefix = "PRECEDENCE_"

            db_url: str = Field(alias="database_url", default="sqlite:///default.db")
            pool_size: int = Field(alias="connection_pool_size", default=5)
            timeout: int = Field(alias="connection_timeout", default=30)
            debug: bool = Field(alias="debug_mode", default=False)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "database_url": "postgres://from-json/db",
                    "connection_pool_size": 10,
                    "connection_timeout": 60,
                },
                f,
            )
            config_file = f.name

        try:
            os.environ["PRECEDENCE_CONNECTION_POOL_SIZE"] = "20"
            os.environ["PRECEDENCE_CONNECTION_TIMEOUT"] = "90"

            @click.command()
            @Config.generate_click_parameters()
            @click.pass_context
            def cmd(ctx: click.Context, **kwargs: Any):
                config = Config.from_click_context(ctx, **kwargs)
                click.echo(f"db={config.db_url}|{config.source.db_url.value}")
                click.echo(f"pool={config.pool_size}|{config.source.pool_size.value}")
                click.echo(f"timeout={config.timeout}|{config.source.timeout.value}")
                click.echo(f"debug={config.debug}|{config.source.debug.value}")

            runner = CliRunner()

            # Test precedence: CLI > JSON > ENV > DEFAULT
            result = runner.invoke(cmd, ["--config", config_file, "--connection-timeout", "120"])
            assert result.exit_code == 0

            # db_url: from JSON (no CLI, no ENV)
            assert "db=postgres://from-json/db|json" in result.output
            # pool_size: from JSON (no CLI, JSON overrides ENV)
            assert "pool=10|json" in result.output
            # timeout: from CLI (overrides everything including ENV and JSON)
            assert "timeout=120|cli" in result.output
            # debug: from DEFAULT (not in CLI, ENV, or JSON)
            assert "debug=False|default" in result.output

        finally:
            os.unlink(config_file)
            os.environ.pop("PRECEDENCE_CONNECTION_POOL_SIZE", None)
            os.environ.pop("PRECEDENCE_CONNECTION_TIMEOUT", None)

    def test_alias_with_json_config_file(self):
        """Test how alias affects JSON config file field names.

        NOTE: This test shows that JSON config works with aliases when using
        the field name (not the alias) in the JSON file.
        """

        import json
        import tempfile

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            db_url: str = Field(alias="database_url", default="sqlite:///app.db")

        # JSON config should use the field name, not the alias
        # (or with populate_by_name=True, either should work)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Using field name in JSON (not alias)
            json.dump({"db_url": "postgres://localhost/db"}, f)
            config_file = f.name

        try:

            @click.command()
            @Config.generate_click_parameters()
            @click.pass_context
            def cmd(ctx: click.Context, **kwargs: Any):
                config = Config.from_click_context(ctx, **kwargs)
                click.echo(f"db={config.db_url}")

            runner = CliRunner()
            result = runner.invoke(cmd, ["--config", config_file])

            assert result.exit_code == 0
            assert "db=postgres://localhost/db" in result.output
        finally:
            import os

            os.unlink(config_file)

    def test_aliases_work_without_configuration(self):
        """Test that aliases work out of the box without any model_config needed.

        WryModel automatically sets validate_by_name=True and validate_by_alias=True,
        so aliases just work without any configuration.
        """

        # No model_config needed - WryModel provides validate_by_name and validate_by_alias
        class Config(AutoWryModel):
            db_url: str = Field(alias="database_url", default="sqlite:///app.db")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"db={config.db_url}")

        runner = CliRunner()

        # Test with alias-based CLI option
        result = runner.invoke(cmd, ["--database-url", "postgres://test/db"])
        assert result.exit_code == 0
        assert "db=postgres://test/db" in result.output

        # Test direct instantiation with field name
        config1 = Config(db_url="mysql://db1")
        assert config1.db_url == "mysql://db1"

        # Test direct instantiation with alias
        config2 = Config(database_url="mysql://db2")
        assert config2.db_url == "mysql://db2"

    def test_both_field_name_and_alias_work(self):
        """Test that both field name and alias work for instantiation."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            db_url: str = Field(alias="database_url", default="sqlite:///app.db")

        # With populate_by_name=True, both should work
        config1 = Config(db_url="postgres://db1")
        assert config1.db_url == "postgres://db1"

        config2 = Config(database_url="postgres://db2")
        assert config2.db_url == "postgres://db2"

        # Both at once - alias takes precedence (standard Pydantic behavior)
        config3 = Config(db_url="postgres://db3", database_url="postgres://db4")
        assert config3.db_url == "postgres://db4"  # Alias wins


class TestAliasEdgeCases:
    """Test edge cases and potential issues with alias usage."""

    def test_alias_conflict_with_another_field(self):
        """Test that alias doesn't conflict with another field name."""

        # This should raise an error or be handled gracefully
        try:

            class Config(AutoWryModel):
                model_config = ConfigDict(populate_by_name=True)

                field_a: str = Field(alias="field_b", default="a")
                field_b: str = Field(default="b")  # Conflict!

            # If Pydantic allows this, test the behavior
            config = Config()
            # Document what happens
        except Exception:
            # Expected: Pydantic should catch this conflict
            pass

    def test_alias_with_underscore_to_hyphen_conversion(self):
        """Test alias with underscores and Click's hyphen conversion."""

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            # Alias has underscores, Click will convert to hyphens
            db: Annotated[str, click.option("--database-connection-url")] = Field(
                alias="database_connection_url", default="sqlite:///app.db"
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            config = Config(**kwargs)
            click.echo(f"db={config.db}")

        runner = CliRunner()
        result = runner.invoke(cmd, ["--database-connection-url", "postgres://db"])

        assert result.exit_code == 0
        assert "db=postgres://db" in result.output

    def test_alias_empty_string(self):
        """Test behavior with empty string alias."""

        try:

            class Config(AutoWryModel):
                field: str = Field(alias="", default="test")

            # Document behavior if Pydantic allows it
            config = Config()
        except Exception:
            # Expected: Pydantic should reject empty alias
            pass

    def test_alias_with_special_characters(self):
        """Test alias with special characters."""

        # Pydantic allows various characters in aliases
        # But Click option names have restrictions

        class Config(AutoWryModel):
            model_config = ConfigDict(populate_by_name=True)

            db: Annotated[
                str, click.option("--db-url")  # Click handles hyphens
            ] = Field(alias="db_url", default="sqlite:///app.db")

        config = Config(db_url="postgres://db")
        assert config.db == "postgres://db"
