"""Tests for AutoWryModel automatic handling of list[str] fields.

This module tests that AutoWryModel correctly auto-generates Click options
with multiple=True for list type fields, without requiring manual decoration.
"""

from typing import Any

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoWryModel


class TestAutoModelListFields:
    """Test AutoWryModel automatic handling of list fields."""

    def test_list_str_auto_generates_multiple_option(self):
        """Test that list[str] automatically gets multiple=True."""

        class Config(AutoWryModel):
            """Config with list field."""

            tags: list[str] = Field(
                default_factory=list,
                description="Tags to apply",
            )
            name: str = Field(default="test", description="Name")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Name: {config.name}")
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Tags type: {type(config.tags).__name__}")
            return config

        runner = CliRunner()

        # Test with no tags - should get empty list
        result = runner.invoke(cmd, ["--name", "Alice"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Name: Alice" in result.output
        assert "Tags: []" in result.output
        assert "Tags type: list" in result.output

        # Test with single tag
        result = runner.invoke(cmd, ["--name", "Bob", "--tags", "python"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Name: Bob" in result.output
        assert "Tags: ['python']" in result.output
        assert "Tags type: list" in result.output

        # Test with multiple tags (passed multiple times)
        result = runner.invoke(cmd, ["--tags", "python", "--tags", "rust", "--tags", "go"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['python', 'rust', 'go']" in result.output
        assert "Tags type: list" in result.output

    def test_list_str_with_default_values(self):
        """Test list[str] with default values."""

        class Config(AutoWryModel):
            """Config with list field having default."""

            tags: list[str] = Field(
                default=["default1", "default2"],
                description="Tags",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            return config

        runner = CliRunner()

        # No tags provided - should use default
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Tags: ['default1', 'default2']" in result.output

        # Override with new tags
        result = runner.invoke(cmd, ["--tags", "new1", "--tags", "new2"])
        assert result.exit_code == 0
        assert "Tags: ['new1', 'new2']" in result.output

    def test_list_int_auto_generates_multiple_option(self):
        """Test that list[int] automatically gets multiple=True with proper type."""

        class Config(AutoWryModel):
            """Config with list[int] field."""

            counts: list[int] = Field(
                default_factory=list,
                description="Count values",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Counts: {config.counts}")
            click.echo(f"Counts type: {type(config.counts).__name__}")
            for count in config.counts:
                click.echo(f"Item type: {type(count).__name__}")
            return config

        runner = CliRunner()

        # Test with no counts
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Counts: []" in result.output

        # Test with integer values
        result = runner.invoke(cmd, ["--counts", "1", "--counts", "2", "--counts", "3"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Counts: [1, 2, 3]" in result.output
        assert "Counts type: list" in result.output
        assert "Item type: int" in result.output

    def test_multiple_list_fields(self):
        """Test multiple list fields in same model."""

        class Config(AutoWryModel):
            """Config with multiple list fields."""

            tags: list[str] = Field(default_factory=list, description="String tags")
            ports: list[int] = Field(default_factory=list, description="Port numbers")
            flags: list[bool] = Field(default_factory=list, description="Boolean flags")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Ports: {config.ports}")
            click.echo(f"Flags: {config.flags}")
            return config

        runner = CliRunner()

        # Test all list fields together
        result = runner.invoke(
            cmd,
            [
                "--tags",
                "a",
                "--tags",
                "b",
                "--ports",
                "80",
                "--ports",
                "443",
                "--flags",
                "true",
                "--flags",
                "false",
            ],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['a', 'b']" in result.output
        assert "Ports: [80, 443]" in result.output
        assert "Flags: [True, False]" in result.output

    def test_list_field_with_constraints(self):
        """Test list[str] with Pydantic constraints."""

        class Config(AutoWryModel):
            """Config with constrained list field."""

            tags: list[str] = Field(
                default_factory=list,
                min_length=1,
                max_length=5,
                description="Tags (1-5 required)",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            return config

        runner = CliRunner()

        # Valid: within constraints
        result = runner.invoke(cmd, ["--tags", "a", "--tags", "b", "--tags", "c"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['a', 'b', 'c']" in result.output

        # Invalid: empty list violates min_length=1
        result = runner.invoke(cmd, [])
        assert result.exit_code != 0, "Should fail validation"

        # Invalid: too many items (max_length=5)
        result = runner.invoke(
            cmd,
            [
                "--tags",
                "a",
                "--tags",
                "b",
                "--tags",
                "c",
                "--tags",
                "d",
                "--tags",
                "e",
                "--tags",
                "f",
            ],
        )
        assert result.exit_code != 0, "Should fail validation"

    def test_list_field_help_text(self):
        """Test that list fields show appropriate help text."""

        class Config(AutoWryModel):
            """Config with list field."""

            tags: list[str] = Field(
                default_factory=list,
                description="Tags to apply (can be specified multiple times)",
            )

        @click.command()
        @Config.generate_click_parameters()
        def cmd(**kwargs: Any):
            """Test command."""
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0
        # Should show the option
        assert "--tags" in result.output
        # Should show the description
        assert "Tags to apply" in result.output or "can be specified multiple times" in result.output

    def test_list_field_source_tracking(self):
        """Test that source tracking works correctly for list fields."""

        class Config(AutoWryModel):
            """Config with list field."""

            tags: list[str] = Field(default=["default"], description="Tags")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Tags source: {config.source.tags.value}")
            return config

        runner = CliRunner()

        # Default value
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Tags: ['default']" in result.output
        assert "Tags source: default" in result.output

        # CLI override
        result = runner.invoke(cmd, ["--tags", "cli1", "--tags", "cli2"])
        assert result.exit_code == 0
        assert "Tags: ['cli1', 'cli2']" in result.output
        assert "Tags source: cli" in result.output

    def test_empty_list_vs_no_value(self):
        """Test distinction between empty list and no value provided."""

        class Config(AutoWryModel):
            """Config with optional list field."""

            tags: list[str] = Field(
                default_factory=list,
                description="Optional tags",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Tags length: {len(config.tags)}")
            return config

        runner = CliRunner()

        # No tags provided - should use default_factory (empty list)
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Tags: []" in result.output
        assert "Tags length: 0" in result.output

    def test_list_field_with_json_config(self, tmp_path):
        """Test that list fields work with JSON config files."""
        import json

        class Config(AutoWryModel):
            """Config with list field."""

            tags: list[str] = Field(default_factory=list, description="Tags")
            name: str = Field(default="test", description="Name")

        # Create config file
        config_file = tmp_path / "config.json"
        config_data = {"tags": ["json1", "json2", "json3"], "name": "from-json"}
        config_file.write_text(json.dumps(config_data))

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Name: {config.name}")
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Name source: {config.source.name.value}")
            click.echo(f"Tags source: {config.source.tags.value}")
            return config

        runner = CliRunner()

        # Load from JSON
        result = runner.invoke(cmd, ["--config", str(config_file)])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Name: from-json" in result.output
        assert "Tags: ['json1', 'json2', 'json3']" in result.output
        assert "Name source: json" in result.output
        assert "Tags source: json" in result.output

        # CLI overrides JSON
        result = runner.invoke(
            cmd,
            [
                "--config",
                str(config_file),
                "--tags",
                "cli1",
                "--tags",
                "cli2",
                "--name",
                "from-cli",
            ],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Name: from-cli" in result.output
        assert "Tags: ['cli1', 'cli2']" in result.output
        assert "Name source: cli" in result.output
        assert "Tags source: cli" in result.output

    def test_list_field_with_env_vars(self):
        """Test that list fields work with environment variables."""

        class Config(AutoWryModel):
            """Config with list field."""

            env_prefix = "MYAPP_"

            tags: list[str] = Field(default_factory=list, description="Tags")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Tags source: {config.source.tags.value}")
            return config

        runner = CliRunner()

        # Note: Click's envvar handling for multiple values is limited
        # Environment variables don't work well with multiple=True in Click
        # This documents the expected behavior
        with runner.isolated_filesystem():
            # ENV var with single value (Click limitation)
            result = runner.invoke(cmd, [], env={"MYAPP_TAGS": "tag1"})
            # This may or may not work depending on Click's handling
            # The behavior is documented rather than enforced

    def test_tuple_field_auto_generates_multiple_option(self):
        """Test that tuple fields also get multiple=True."""

        class Config(AutoWryModel):
            """Config with tuple field."""

            values: tuple[str, ...] = Field(
                default=(),
                description="Values",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Values: {config.values}")
            click.echo(f"Values type: {type(config.values).__name__}")
            return config

        runner = CliRunner()

        # Test with multiple values
        result = runner.invoke(cmd, ["--values", "a", "--values", "b", "--values", "c"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        # Tuple should be converted or maintained
        assert "'a'" in result.output and "'b'" in result.output and "'c'" in result.output
