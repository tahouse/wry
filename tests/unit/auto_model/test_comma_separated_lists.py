"""Tests for comma-separated list input support.

This module tests the CommaSeparated marker that allows list fields
to accept comma-separated input instead of multiple invocations.
"""

from typing import Annotated, Any

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoWryModel, CommaSeparated


class TestCommaSeparatedLists:
    """Test comma-separated list parsing."""

    def test_comma_separated_strings(self):
        """Test comma-separated string lists."""

        class Config(AutoWryModel):
            """Config with comma-separated tags."""

            tags: Annotated[list[str], CommaSeparated] = Field(
                default_factory=list,
                description="Comma-separated tags",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Count: {len(config.tags)}")
            return config

        runner = CliRunner()

        # Test comma-separated input
        result = runner.invoke(cmd, ["--tags", "python,rust,go"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['python', 'rust', 'go']" in result.output
        assert "Count: 3" in result.output

        # Test single value (no commas)
        result = runner.invoke(cmd, ["--tags", "python"])
        assert result.exit_code == 0
        assert "Tags: ['python']" in result.output
        assert "Count: 1" in result.output

        # Test empty/no value
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Tags: []" in result.output
        assert "Count: 0" in result.output

        # Test with whitespace (should be stripped)
        result = runner.invoke(cmd, ["--tags", "python, rust , go"])
        assert result.exit_code == 0
        assert "Tags: ['python', 'rust', 'go']" in result.output

    def test_comma_separated_integers(self):
        """Test comma-separated integer lists."""

        class Config(AutoWryModel):
            """Config with comma-separated ports."""

            ports: Annotated[list[int], CommaSeparated] = Field(
                default_factory=list,
                description="Comma-separated port numbers",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Ports: {config.ports}")
            for port in config.ports:
                click.echo(f"Type: {type(port).__name__}")
            return config

        runner = CliRunner()

        # Test comma-separated integers
        result = runner.invoke(cmd, ["--ports", "8080,8443,9000"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Ports: [8080, 8443, 9000]" in result.output
        assert "Type: int" in result.output

        # Test with whitespace
        result = runner.invoke(cmd, ["--ports", "80, 443 , 8080"])
        assert result.exit_code == 0
        assert "Ports: [80, 443, 8080]" in result.output

        # Test invalid integer
        result = runner.invoke(cmd, ["--ports", "80,not-a-number,443"])
        assert result.exit_code != 0  # Should fail

    def test_comma_separated_floats(self):
        """Test comma-separated float lists."""

        class Config(AutoWryModel):
            """Config with comma-separated values."""

            values: Annotated[list[float], CommaSeparated] = Field(
                default_factory=list,
                description="Comma-separated float values",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Values: {config.values}")
            for val in config.values:
                click.echo(f"Type: {type(val).__name__}")
            return config

        runner = CliRunner()

        # Test comma-separated floats
        result = runner.invoke(cmd, ["--values", "1.5,2.7,3.14"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Values: [1.5, 2.7, 3.14]" in result.output
        assert "Type: float" in result.output

        # Test invalid float
        result = runner.invoke(cmd, ["--values", "1.5,invalid,3.14"])
        assert result.exit_code != 0  # Should fail

    def test_mixed_standard_and_comma_separated(self):
        """Test mixing standard multiple=True and comma-separated in same model."""

        class Config(AutoWryModel):
            """Config with both list types."""

            # Standard: requires --tags a --tags b
            standard_tags: list[str] = Field(
                default_factory=list,
                description="Standard tags (repeat option)",
            )

            # Comma-separated: --csv-tags a,b,c
            csv_tags: Annotated[list[str], CommaSeparated] = Field(
                default_factory=list,
                description="CSV tags (comma-separated)",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Standard: {config.standard_tags}")
            click.echo(f"CSV: {config.csv_tags}")
            return config

        runner = CliRunner()

        # Use both types together
        result = runner.invoke(
            cmd,
            [
                "--standard-tags",
                "a",
                "--standard-tags",
                "b",
                "--csv-tags",
                "x,y,z",
            ],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Standard: ['a', 'b']" in result.output
        assert "CSV: ['x', 'y', 'z']" in result.output

    def test_comma_separated_with_default_values(self):
        """Test comma-separated with default values."""

        class Config(AutoWryModel):
            """Config with defaults."""

            tags: Annotated[list[str], CommaSeparated] = Field(
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
            click.echo(f"Source: {config.source.tags.value}")
            return config

        runner = CliRunner()

        # No input - use default
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "Tags: ['default1', 'default2']" in result.output
        assert "Source: default" in result.output

        # Override with CLI
        result = runner.invoke(cmd, ["--tags", "new1,new2,new3"])
        assert result.exit_code == 0
        assert "Tags: ['new1', 'new2', 'new3']" in result.output
        assert "Source: cli" in result.output

    def test_comma_separated_with_json_config(self, tmp_path):
        """Test comma-separated with JSON config."""
        import json

        class Config(AutoWryModel):
            """Config with comma-separated field."""

            tags: Annotated[list[str], CommaSeparated] = Field(
                default_factory=list,
                description="Tags",
            )
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
            click.echo(f"Tags source: {config.source.tags.value}")
            return config

        runner = CliRunner()

        # Load from JSON
        result = runner.invoke(cmd, ["--config", str(config_file)])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['json1', 'json2', 'json3']" in result.output
        assert "Tags source: json" in result.output

        # CLI overrides JSON with comma-separated input
        result = runner.invoke(cmd, ["--config", str(config_file), "--tags", "cli1,cli2"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['cli1', 'cli2']" in result.output
        assert "Tags source: cli" in result.output

    def test_comma_separated_preserves_validation(self):
        """Test that Pydantic validation still works with comma-separated."""

        class Config(AutoWryModel):
            """Config with validated comma-separated field."""

            tags: Annotated[list[str], CommaSeparated] = Field(
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
        result = runner.invoke(cmd, ["--tags", "a,b,c"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['a', 'b', 'c']" in result.output

        # Invalid: empty list violates min_length=1
        result = runner.invoke(cmd, [])
        assert result.exit_code != 0, "Should fail validation"

        # Invalid: too many items (max_length=5)
        result = runner.invoke(cmd, ["--tags", "a,b,c,d,e,f"])
        assert result.exit_code != 0, "Should fail validation"

    def test_comma_separated_empty_items_filtered(self):
        """Test that empty items from commas are filtered out."""

        class Config(AutoWryModel):
            """Config."""

            tags: Annotated[list[str], CommaSeparated] = Field(
                default_factory=list,
                description="Tags",
            )

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Count: {len(config.tags)}")
            return config

        runner = CliRunner()

        # Multiple commas, trailing commas, etc.
        result = runner.invoke(cmd, ["--tags", "a,,b,,,c,"])
        assert result.exit_code == 0
        assert "Tags: ['a', 'b', 'c']" in result.output
        assert "Count: 3" in result.output

    def test_comma_separated_help_text(self):
        """Test that help text is appropriate for comma-separated fields."""

        class Config(AutoWryModel):
            """Config."""

            tags: Annotated[list[str], CommaSeparated] = Field(
                default_factory=list,
                description="Project tags (comma-separated: python,rust,go)",
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
        # Should show description mentioning comma-separated
        assert "comma-separated" in result.output.lower() or "Project tags" in result.output

    def test_model_wide_comma_separated_setting(self):
        """Test comma_separated_lists class variable for model-wide setting."""
        from typing import ClassVar

        class Config(AutoWryModel):
            """Config with model-wide comma-separated setting."""

            # Enable comma-separated for ALL list fields in this model
            comma_separated_lists: ClassVar[bool] = True

            tags: list[str] = Field(default_factory=list, description="Tags")
            ports: list[int] = Field(default_factory=list, description="Ports")
            values: list[float] = Field(default_factory=list, description="Values")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Ports: {config.ports}")
            click.echo(f"Values: {config.values}")
            return config

        runner = CliRunner()

        # All list fields should accept comma-separated input
        result = runner.invoke(
            cmd,
            [
                "--tags",
                "python,rust,go",
                "--ports",
                "8080,8443,9000",
                "--values",
                "1.5,2.7,3.14",
            ],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['python', 'rust', 'go']" in result.output
        assert "Ports: [8080, 8443, 9000]" in result.output
        assert "Values: [1.5, 2.7, 3.14]" in result.output

    def test_per_field_annotation_overrides_model_setting(self):
        """Test that per-field CommaSeparated annotation works alongside model setting."""
        from typing import ClassVar

        class Config(AutoWryModel):
            """Config with both model-wide and per-field settings."""

            # Model-wide setting (applies to fields without explicit annotation)
            comma_separated_lists: ClassVar[bool] = True

            # These get comma-separated from model setting
            tags: list[str] = Field(default_factory=list, description="Tags")

            # This explicitly uses CommaSeparated (redundant but allowed)
            ports: Annotated[list[int], CommaSeparated] = Field(default_factory=list, description="Ports")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Ports: {config.ports}")
            return config

        runner = CliRunner()

        # Both should work with comma-separated
        result = runner.invoke(cmd, ["--tags", "a,b,c", "--ports", "80,443"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['a', 'b', 'c']" in result.output
        assert "Ports: [80, 443]" in result.output

    def test_model_wide_setting_does_not_affect_non_list_fields(self):
        """Test that comma_separated_lists only affects list fields, not other types."""
        from typing import ClassVar

        class Config(AutoWryModel):
            """Config with comma-separated enabled but also non-list fields."""

            # Enable comma-separated for list fields
            comma_separated_lists: ClassVar[bool] = True

            # List field - should use comma-separated
            tags: list[str] = Field(default_factory=list, description="Tags")

            # Non-list fields - should NOT be affected
            name: str = Field(default="test", description="Name")
            count: int = Field(default=0, description="Count")
            enabled: bool = Field(default=False, description="Enabled")

            # Explicit click.option with count=True (like -vvv for verbose)
            verbose: Annotated[
                int,
                click.option(
                    "--verbose",
                    "-v",
                    count=True,
                    help="Increase verbosity (-v, -vv, -vvv)",
                ),
            ] = Field(default=0, description="Verbosity level")

        @click.command()
        @Config.generate_click_parameters()
        @click.pass_context
        def cmd(ctx: click.Context, **kwargs: Any):
            """Test command."""
            config = Config.from_click_context(ctx, **kwargs)
            click.echo(f"Tags: {config.tags}")
            click.echo(f"Name: {config.name}")
            click.echo(f"Count: {config.count}")
            click.echo(f"Enabled: {config.enabled}")
            click.echo(f"Verbose: {config.verbose}")
            return config

        runner = CliRunner()

        # Test that list field uses comma-separated
        result = runner.invoke(cmd, ["--tags", "a,b,c"])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['a', 'b', 'c']" in result.output

        # Test that non-list fields work normally
        result = runner.invoke(
            cmd,
            [
                "--tags",
                "x,y",
                "--name",
                "Alice",
                "--count",
                "42",
                "--enabled",
                "-vvv",  # Should count to 3
            ],
        )
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Tags: ['x', 'y']" in result.output
        assert "Name: Alice" in result.output
        assert "Count: 42" in result.output
        assert "Enabled: True" in result.output
        assert "Verbose: 3" in result.output  # -vvv = 3

        # Test verbose counting separately
        result = runner.invoke(cmd, ["-v"])
        assert result.exit_code == 0
        assert "Verbose: 1" in result.output

        result = runner.invoke(cmd, ["-vv"])
        assert result.exit_code == 0
        assert "Verbose: 2" in result.output
