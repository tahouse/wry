"""Test AutoClickParameter.EXCLUDE functionality."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoClickParameter, AutoWryModel, WryModel
from wry.click_integration import generate_click_parameters


class TestExcludeEnum:
    """Test that EXCLUDE enum properly excludes fields from Click parameter generation."""

    def test_exclude_with_autowrymodel(self):
        """Test EXCLUDE works with AutoWryModel."""

        class ConfigExcludeAuto(AutoWryModel):
            # Regular fields become options
            name: str = Field(default="test", description="Your name")
            count: int = Field(default=1, description="Number of items")

            # Excluded fields
            polymorphic_input: Annotated[str, AutoClickParameter.EXCLUDE] = "raw"
            computed_result: Annotated[str, AutoClickParameter.EXCLUDE] = Field(
                default="", description="Computed from polymorphic_input"
            )
            internal_state: Annotated[dict, AutoClickParameter.EXCLUDE] = Field(default_factory=dict)

        @click.command()
        @ConfigExcludeAuto.generate_click_parameters()
        def cli(**kwargs):
            config = ConfigExcludeAuto(**kwargs)
            # Echo string representation for testing
            click.echo(f"name={config.name},count={config.count},polymorphic={config.polymorphic_input}")

        runner = CliRunner()

        # Test default values
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "name=test,count=1,polymorphic=raw" in result.output

        # Test that excluded fields are not available as CLI options
        result = runner.invoke(cli, ["--polymorphic-input", "changed"])
        assert result.exit_code != 0
        assert "no such option: --polymorphic-input" in result.output.lower()

        result = runner.invoke(cli, ["--computed-result", "changed"])
        assert result.exit_code != 0
        assert "no such option: --computed-result" in result.output.lower()

        # Test that regular fields work
        result = runner.invoke(cli, ["--name", "Alice", "--count", "5"])
        assert result.exit_code == 0
        assert "name=Alice,count=5,polymorphic=raw" in result.output

    def test_exclude_with_wrymodel(self):
        """Test EXCLUDE works with WryModel."""

        class ConfigExcludeWry(WryModel):
            # Only annotated fields become options
            name: Annotated[str, AutoClickParameter.OPTION] = "test"
            count: Annotated[int, AutoClickParameter.OPTION] = 1

            # This is excluded explicitly
            excluded_field: Annotated[str, AutoClickParameter.EXCLUDE] = "excluded"

            # This is excluded by not having any AutoClickParameter annotation
            not_annotated: str = "not_annotated"

        @click.command()
        @generate_click_parameters(ConfigExcludeWry)
        def cli(**kwargs):
            config = ConfigExcludeWry(**kwargs)
            click.echo(f"name={config.name},excluded={config.excluded_field}")

        runner = CliRunner()

        # Test that excluded field is not available
        result = runner.invoke(cli, ["--excluded-field", "changed"])
        assert result.exit_code != 0
        assert "no such option: --excluded-field" in result.output.lower()

        # Test that regular fields work
        result = runner.invoke(cli, ["--name", "Bob"])
        assert result.exit_code == 0
        assert "name=Bob,excluded=excluded" in result.output

    def test_exclude_precedence(self):
        """Test that EXCLUDE takes precedence when multiple markers are present."""

        class ConfigExcludePrecedence(AutoWryModel):
            # If both OPTION and EXCLUDE are present, EXCLUDE should win
            conflicted: Annotated[str, AutoClickParameter.OPTION, AutoClickParameter.EXCLUDE] = "default"
            normal: str = "normal"

        @click.command()
        @ConfigExcludePrecedence.generate_click_parameters()
        def cli(**kwargs):
            config = ConfigExcludePrecedence(**kwargs)
            click.echo(f"conflicted={config.conflicted},normal={config.normal}")

        runner = CliRunner()

        # Test that conflicted field is excluded
        result = runner.invoke(cli, ["--conflicted", "changed"])
        assert result.exit_code != 0
        assert "no such option: --conflicted" in result.output.lower()

        # Normal field should work
        result = runner.invoke(cli, ["--normal", "changed"])
        assert result.exit_code == 0
        assert "conflicted=default,normal=changed" in result.output

    def test_exclude_with_source_tracking(self):
        """Test that excluded fields still work with source tracking."""

        class ConfigExcludeTracking(AutoWryModel):
            name: str = "default"
            excluded: Annotated[str, AutoClickParameter.EXCLUDE] = "excluded_default"

        @click.command()
        @ConfigExcludeTracking.generate_click_parameters()
        @click.pass_context
        def cli(ctx, **kwargs):
            config = ConfigExcludeTracking.from_click_context(ctx, **kwargs)
            # Excluded fields should have DEFAULT source since they can't come from CLI
            click.echo(f"name_source={config.source.name},excluded_source={config.source.excluded}")

        runner = CliRunner()

        # Test source tracking
        result = runner.invoke(cli, ["--name", "from_cli"])
        assert result.exit_code == 0
        assert "name_source=ValueSource.CLI" in result.output
        assert "excluded_source=ValueSource.DEFAULT" in result.output
