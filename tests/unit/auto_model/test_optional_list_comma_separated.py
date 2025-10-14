"""Tests for comma-separated lists with Optional/Union types."""

from typing import Annotated, Any, ClassVar

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoWryModel, CommaSeparated


class TestOptionalListCommaSeparated:
    """Test comma-separated parsing with Optional list types."""

    def test_mvp_bug_optional_list_model_wide_comma_separated(self):
        """Test the exact MVP bug: list[str] | None with model-wide comma_separated_lists.

        This was the original bug report where Optional list fields with comma_separated_lists
        enabled at the model level would fail with validation errors.
        """

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            items: list[str] | None = Field(default=None, description="List of items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Raw kwargs: {kwargs}")
            click.echo(f"Parsed config: {config.items}")

        runner = CliRunner()

        # This was the failing case - passing comma-separated values
        result = runner.invoke(cmd, ["--items", "x,y,z"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Parsed config: ['x', 'y', 'z']" in result.output

        # Also test with no value
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Parsed config: None" in result.output

    def test_optional_list_with_comma_separated_model_wide(self):
        """Test that Optional[list[T]] works with model-wide comma_separated_lists."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            items: list[str] | None = Field(default=None, description="List of items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")

        runner = CliRunner()

        # Test with comma-separated values
        result = runner.invoke(cmd, ["--items", "a,b,c"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Items: ['a', 'b', 'c']" in result.output

        # Test with single value
        result = runner.invoke(cmd, ["--items", "single"])
        assert result.exit_code == 0
        assert "Items: ['single']" in result.output

        # Test with no value (should be None)
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Items: None" in result.output

    def test_optional_list_with_per_field_comma_separated(self):
        """Test that Optional[list[T]] works with per-field CommaSeparated annotation."""

        class Config(AutoWryModel):
            items: Annotated[list[str], CommaSeparated] | None = Field(default=None, description="List of items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")

        runner = CliRunner()

        # Test with comma-separated values
        result = runner.invoke(cmd, ["--items", "x,y,z"])
        assert result.exit_code == 0
        assert "Items: ['x', 'y', 'z']" in result.output

        # Test with no value (should be None)
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Items: None" in result.output

    def test_optional_list_int_with_comma_separated(self):
        """Test that Optional[list[int]] works with comma-separated parsing."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            ports: list[int] | None = Field(default=None, description="Port numbers")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Ports: {config.ports}")
            if config.ports:
                click.echo(f"Types: {[type(p).__name__ for p in config.ports]}")

        runner = CliRunner()

        # Test with comma-separated integers
        result = runner.invoke(cmd, ["--ports", "80,443,8080"])
        assert result.exit_code == 0
        assert "Ports: [80, 443, 8080]" in result.output
        assert "Types: ['int', 'int', 'int']" in result.output

        # Test with no value (should be None)
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Ports: None" in result.output

    def test_optional_list_with_default_empty_list(self):
        """Test Optional list with default=[] instead of default=None."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            tags: list[str] | None = Field(default=[], description="Tags")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")

        runner = CliRunner()

        # Test with values
        result = runner.invoke(cmd, ["--tags", "a,b"])
        assert result.exit_code == 0
        assert "Tags: ['a', 'b']" in result.output

        # Test with no value (should be empty list)
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Tags: []" in result.output

    def test_optional_list_with_default_factory(self):
        """Test Optional list with default_factory."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            items: list[str] = Field(default_factory=list, description="Items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")

        runner = CliRunner()

        # Test with values
        result = runner.invoke(cmd, ["--items", "a,b,c"])
        assert result.exit_code == 0
        assert "Items: ['a', 'b', 'c']" in result.output

        # Test with no value (should be empty list from factory)
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Items: []" in result.output

    def test_optional_list_old_syntax(self):
        """Test Optional[list[T]] using old Optional[] syntax instead of | None."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            items: list[str] | None = Field(default=None, description="Items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")

        runner = CliRunner()

        # Test with values
        result = runner.invoke(cmd, ["--items", "x,y"])
        assert result.exit_code == 0
        assert "Items: ['x', 'y']" in result.output

        # Test with no value
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Items: None" in result.output

    def test_optional_list_float(self):
        """Test Optional[list[float]] with comma-separated parsing."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            values: list[float] | None = Field(default=None, description="Float values")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Values: {config.values}")
            if config.values:
                click.echo(f"Types: {[type(v).__name__ for v in config.values]}")

        runner = CliRunner()

        # Test with comma-separated floats
        result = runner.invoke(cmd, ["--values", "1.5,2.7,3.14"])
        assert result.exit_code == 0
        assert "Values: [1.5, 2.7, 3.14]" in result.output
        assert "Types: ['float', 'float', 'float']" in result.output

        # Test with no value
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Values: None" in result.output

    def test_mixed_optional_and_required_lists(self):
        """Test model with both optional and required list fields."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            required_items: list[str] = Field(description="Required items")
            optional_items: list[str] | None = Field(default=None, description="Optional items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Required: {config.required_items}")
            click.echo(f"Optional: {config.optional_items}")

        runner = CliRunner()

        # Test with both fields
        result = runner.invoke(cmd, ["--required-items", "a,b", "--optional-items", "x,y"])
        assert result.exit_code == 0
        assert "Required: ['a', 'b']" in result.output
        assert "Optional: ['x', 'y']" in result.output

        # Test with only required field
        result = runner.invoke(cmd, ["--required-items", "a"])
        assert result.exit_code == 0
        assert "Required: ['a']" in result.output
        assert "Optional: None" in result.output

        # Test missing required field should fail
        result = runner.invoke(cmd, [])
        assert result.exit_code != 0

    def test_optional_list_source_tracking(self):
        """Test that source tracking works correctly with optional comma-separated lists."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            items: list[str] | None = Field(default=None, description="Items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")
            click.echo(f"Source: {config.get_value_source('items').value}")

        runner = CliRunner()

        # Test CLI source
        result = runner.invoke(cmd, ["--items", "a,b,c"])
        assert result.exit_code == 0
        assert "Items: ['a', 'b', 'c']" in result.output
        assert "Source: cli" in result.output

        # Test DEFAULT source when not provided
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Items: None" in result.output
        assert "Source: default" in result.output

    def test_optional_annotated_list_non_optional(self):
        """Test non-optional Annotated list with CommaSeparated (for contrast)."""

        class Config(AutoWryModel):
            items: Annotated[list[str], CommaSeparated] = Field(description="Required items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")

        runner = CliRunner()

        # Test with values
        result = runner.invoke(cmd, ["--items", "a,b,c"])
        assert result.exit_code == 0
        assert "Items: ['a', 'b', 'c']" in result.output

        # Test without values should fail (required)
        result = runner.invoke(cmd, [])
        assert result.exit_code != 0

    def test_optional_list_with_spaces(self):
        """Test comma-separated parsing handles spaces correctly."""

        class Config(AutoWryModel):
            comma_separated_lists: ClassVar[bool] = True
            items: list[str] | None = Field(default=None, description="Items")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")

        runner = CliRunner()

        # Test with spaces after commas (should be stripped)
        result = runner.invoke(cmd, ["--items", "a, b, c"])
        assert result.exit_code == 0
        assert "Items: ['a', 'b', 'c']" in result.output

        # Test single item with spaces
        result = runner.invoke(cmd, ["--items", "  item  "])
        assert result.exit_code == 0
        assert "Items: ['item']" in result.output

    def test_double_nested_optional_annotated(self):
        """Test the specific pattern that was buggy.

        Tests: Annotated[Optional[Annotated[list, CommaSeparated]], AutoOption]
        """

        class Config(AutoWryModel):
            # This creates: Annotated[Optional[Annotated[list[str], CommaSeparated]], AutoOption]
            items: Annotated[list[str], CommaSeparated] | None = Field(default=None, description="Items")
            ports: Annotated[list[int], CommaSeparated] | None = Field(default=None, description="Ports")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Items: {config.items}")
            click.echo(f"Ports: {config.ports}")

        runner = CliRunner()

        # Test both fields
        result = runner.invoke(cmd, ["--items", "a,b,c", "--ports", "80,443"])
        assert result.exit_code == 0
        assert "Items: ['a', 'b', 'c']" in result.output
        assert "Ports: [80, 443]" in result.output

        # Test neither field
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Items: None" in result.output
        assert "Ports: None" in result.output

        # Test only one field
        result = runner.invoke(cmd, ["--items", "x"])
        assert result.exit_code == 0
        assert "Items: ['x']" in result.output
        assert "Ports: None" in result.output
