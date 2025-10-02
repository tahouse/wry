"""Test that explicit click.argument decorators get help text injected into docstring."""

from typing import Annotated

import click
from click.testing import CliRunner
from pydantic import Field

from wry import WryModel, generate_click_parameters


class TestExplicitArgumentHelpInjection:
    """Test help text injection for explicit click.argument decorators."""

    def test_explicit_argument_with_help_in_docstring(self):
        """Test that explicit click.argument with help text gets injected into docstring."""

        class Config(WryModel):
            # Explicit click.argument with help text
            input_file: Annotated[str, click.argument("input_file", help="Input file path")] = Field()

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            """Process the input file."""
            pass

        # Check that the docstring was modified
        assert cmd.__doc__ is not None
        assert "Arguments:" in cmd.__doc__
        assert "INPUT_FILE" in cmd.__doc__
        assert "Input file path" in cmd.__doc__

    def test_explicit_argument_without_help(self):
        """Test that explicit click.argument without help text doesn't break."""

        class Config(WryModel):
            # Explicit click.argument without help text
            input_file: Annotated[str, click.argument("input_file")] = Field()

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            """Process the input file."""
            pass

        # Should work without errors, but no Arguments section added
        assert cmd.__doc__ is not None
        # No Arguments section should be added if no help text
        if "Arguments:" in cmd.__doc__:
            # If it's there, it shouldn't have our argument
            assert "Input file" not in cmd.__doc__

    def test_mixed_auto_and_explicit_arguments(self):
        """Test mixing auto-generated and explicit arguments."""
        from wry import AutoArgument

        class Config(WryModel):
            # Auto-generated argument with Field description
            source: Annotated[str, AutoArgument] = Field(description="Source file")
            # Explicit click.argument with help
            dest: Annotated[str, click.argument("destination", help="Destination file")] = Field()

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            """Copy files."""
            pass

        # Both should be in the docstring
        assert cmd.__doc__ is not None
        assert "Arguments:" in cmd.__doc__
        assert "SOURCE" in cmd.__doc__
        assert "Source file" in cmd.__doc__
        assert "DESTINATION" in cmd.__doc__
        assert "Destination file" in cmd.__doc__

    def test_help_text_displayed_in_cli(self):
        """Test that help text is displayed when running --help."""

        class Config(WryModel):
            input_file: Annotated[str, click.argument("input", help="Input file to process")] = Field()

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            """Process files."""
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--help"])

        assert result.exit_code == 0
        # The help text should be visible in the help output
        assert "Arguments:" in result.output
        assert "INPUT" in result.output
        assert "Input file to process" in result.output
