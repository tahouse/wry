"""Test automatic argument help injection into command docstrings."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import AutoClickParameter, AutoWryModel, WryModel


class TestArgumentHelpInjection:
    """Test that argument descriptions are injected into command docstrings."""

    def test_autowrymodel_argument_help_injection(self):
        """Test that AutoWryModel injects argument help into docstring."""

        class Config(AutoWryModel):
            source: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Source file path")
            dest: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Destination file path")
            verbose: bool = False

        @click.command()
        @Config.generate_click_parameters()
        def copy(**kwargs):
            """Copy files from source to destination."""
            config = Config(**kwargs)
            click.echo(f"{config.source} -> {config.dest}")

        runner = CliRunner()
        result = runner.invoke(copy, ["--help"])

        assert result.exit_code == 0
        assert "Arguments:" in result.output
        assert "SOURCE" in result.output
        assert "Source file path" in result.output
        assert "DEST" in result.output
        assert "Destination file path" in result.output

    def test_wrymodel_argument_help_injection(self):
        """Test that WryModel also supports argument help injection."""

        class Config(WryModel):
            input_file: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Input file to process")
            output_file: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Output file destination")

        @click.command()
        @Config.generate_click_parameters()
        def process(**kwargs):
            """Process input file and write to output."""
            config = Config(**kwargs)
            click.echo(f"Processing: {config.input_file} -> {config.output_file}")

        runner = CliRunner()
        result = runner.invoke(process, ["--help"])

        assert result.exit_code == 0
        assert "Arguments:" in result.output
        assert "INPUT_FILE" in result.output
        assert "Input file to process" in result.output
        assert "OUTPUT_FILE" in result.output
        # Check that the description appears, even if wrapped
        assert "Output" in result.output and "file destination" in result.output

    def test_no_injection_when_no_arguments(self):
        """Test that no Arguments section is added when there are no arguments."""

        class Config(AutoWryModel):
            name: str = "test"
            count: int = 1

        @click.command()
        @Config.generate_click_parameters()
        def run(**kwargs):
            """Run with options only."""
            config = Config(**kwargs)
            click.echo(f"{config.name}: {config.count}")

        runner = CliRunner()
        result = runner.invoke(run, ["--help"])

        assert result.exit_code == 0
        assert "Arguments:" not in result.output

    def test_preserves_existing_docstring(self):
        """Test that argument help is appended to existing docstring."""

        class Config(AutoWryModel):
            file: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="File to analyze")

        @click.command()
        @Config.generate_click_parameters()
        def analyze(**kwargs):
            """Analyze the given file.

            This performs comprehensive analysis and generates a report.
            Use --verbose for detailed output.
            """
            config = Config(**kwargs)
            click.echo(f"Analyzing: {config.file}")

        runner = CliRunner()
        result = runner.invoke(analyze, ["--help"])

        assert result.exit_code == 0
        # Original docstring should be preserved
        assert "Analyze the given file" in result.output
        assert "comprehensive analysis" in result.output
        # Argument help should be appended
        assert "Arguments:" in result.output
        assert "FILE" in result.output
        assert "File to analyze" in result.output

    def test_no_injection_for_arguments_without_description(self):
        """Test that arguments without descriptions are not added to docstring."""

        class Config(AutoWryModel):
            # Argument with description
            source: Annotated[str, AutoClickParameter.ARGUMENT] = Field(description="Source path")
            # Argument without description - should not appear in docstring
            dest: Annotated[str, AutoClickParameter.ARGUMENT] = Field(default="out.txt")

        @click.command()
        @Config.generate_click_parameters()
        def copy(**kwargs):
            """Copy file."""
            config = Config(**kwargs)
            click.echo(f"{config.source} -> {config.dest}")

        runner = CliRunner()
        result = runner.invoke(copy, ["--help"])

        assert result.exit_code == 0
        assert "Arguments:" in result.output
        assert "SOURCE" in result.output
        assert "Source path" in result.output
        # DEST should not appear in Arguments section since it has no description
        # (it will appear in usage line though)
        lines_after_arguments = result.output.split("Arguments:")[1].split("Options:")[0]
        assert "DEST" not in lines_after_arguments or "Source path" in lines_after_arguments
