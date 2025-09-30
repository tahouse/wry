"""Tests for the multiple option bug in wry.

This module tests the bug where Click options with multiple=True are
incorrectly converted to strings when used with generate_click_parameters.
"""

import click
from pydantic import Field

from wry import AutoWryModel, generate_click_parameters
from wry.core import WryModel


class TestMultipleOptionBug:
    """Test cases for the multiple option bug."""

    def test_multiple_option_with_autowrymodel(self):
        """Test that multiple options work correctly with AutoWryModel."""

        class TestArgs(AutoWryModel):
            """Test model with multiple option."""

            files: list[str] = Field(
                default=[],
                description="Files to process",
            )
            other_option: str = Field(
                default="default",
                description="Another option",
            )

        @click.command()
        @click.option("--files", multiple=True)
        @generate_click_parameters(TestArgs, strict=False)
        @click.pass_context
        def test_command(ctx: click.Context, files: tuple[str, ...], **kwargs):
            """Test command with multiple option."""
            kwargs["files"] = files

            print(f"Raw files from Click: {files!r}")
            print(f"Type: {type(files)}")

            config = TestArgs.from_click_context(ctx, **kwargs)
            print(f"Config files: {config.files!r}")
            print(f"Type: {type(config.files)}")

            return config

        # Test the bug by running the command with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with no arguments - should work correctly now
        result = runner.invoke(test_command, [])
        print("No arguments result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ()" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: []" in result.output
        assert "Type: <class 'list'>" in result.output

        # Test with arguments - should work correctly now
        result = runner.invoke(test_command, ["--files", "file1.txt", "--files", "file2.txt"])
        print("With arguments result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ('file1.txt', 'file2.txt')" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: ['file1.txt', 'file2.txt']" in result.output
        assert "Type: <class 'list'>" in result.output

    def test_multiple_option_with_wrymodel(self):
        """Test that multiple options work correctly with WryModel."""
        from typing import Annotated

        from wry.click_integration import AutoClickParameter

        class TestArgs(WryModel):
            """Test model with multiple option."""

            files: Annotated[list[str], AutoClickParameter.OPTION] = Field(
                default=[],
                description="Files to process",
            )
            other_option: Annotated[str, AutoClickParameter.OPTION] = Field(
                default="default",
                description="Another option",
            )

        @click.command()
        @click.option("--files", multiple=True)
        @generate_click_parameters(TestArgs, strict=False)
        @click.pass_context
        def test_command(ctx: click.Context, files: tuple[str, ...], **kwargs):
            """Test command with multiple option."""
            kwargs["files"] = files

            print(f"Raw files from Click: {files!r}")
            print(f"Type: {type(files)}")

            config = TestArgs.from_click_context(ctx, **kwargs)
            print(f"Config files: {config.files!r}")
            print(f"Type: {type(config.files)}")

            return config

        # Test the bug by running the command with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with no arguments - should work correctly now
        result = runner.invoke(test_command, [])
        print("No arguments result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ()" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: []" in result.output
        assert "Type: <class 'list'>" in result.output

        # Test with arguments - should work correctly now
        result = runner.invoke(test_command, ["--files", "file1.txt", "--files", "file2.txt"])
        print("With arguments result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ('file1.txt', 'file2.txt')" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: ['file1.txt', 'file2.txt']" in result.output
        assert "Type: <class 'list'>" in result.output

    def test_click_multiple_option_without_wry_works_correctly(self):
        """Test that Click multiple options without wry work correctly (baseline test)."""

        @click.command()
        @click.option("--files", multiple=True)
        def test_click_only(files):
            """Click without wry works correctly."""
            print(f"Files: {files!r}")
            print(f"Type: {type(files)}")
            assert isinstance(files, tuple), f"Expected tuple, got {type(files)}: {files!r}"
            return files

        # Test with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with no arguments
        result = runner.invoke(test_click_only, [])
        assert result.exit_code == 0
        assert "Files: ()" in result.output
        assert "Type: <class 'tuple'>" in result.output

        # Test with arguments
        result = runner.invoke(test_click_only, ["--files", "file1.txt", "--files", "file2.txt"])
        assert result.exit_code == 0
        assert "Files: ('file1.txt', 'file2.txt')" in result.output
        assert "Type: <class 'tuple'>" in result.output

    def test_multiple_option_edge_cases(self):
        """Test edge cases for multiple options."""

        class TestArgs(AutoWryModel):
            """Test model with multiple option."""

            files: list[str] = Field(default=[], description="Files to process")

        @click.command()
        @click.option("--files", multiple=True)
        @generate_click_parameters(TestArgs, strict=False)
        @click.pass_context
        def test_command(ctx: click.Context, files: tuple[str, ...], **kwargs):
            """Test command with edge cases."""
            kwargs["files"] = files

            print(f"Raw files from Click: {files!r}")
            print(f"Type: {type(files)}")

            config = TestArgs.from_click_context(ctx, **kwargs)

            print(f"Config files: {config.files!r}")
            print(f"Type: {type(config.files)}")

            # Test that files is always a list
            assert isinstance(config.files, list), f"Expected list, got {type(config.files)}: {config.files!r}"

            return config

        # Test with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test empty tuple - should work correctly now
        result = runner.invoke(test_command, [])
        print("Empty files result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Type: <class 'tuple'>" in result.output
        assert "Type: <class 'list'>" in result.output

        # Test single item - should work correctly now
        result = runner.invoke(test_command, ["--files", "single.txt"])
        print("Single file result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ('single.txt',)" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: ['single.txt']" in result.output
        assert "Type: <class 'list'>" in result.output

        # Test many items - should work correctly now
        result = runner.invoke(test_command, ["--files", "a.txt", "--files", "b.txt", "--files", "c.txt"])
        print("Multiple files result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ('a.txt', 'b.txt', 'c.txt')" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: ['a.txt', 'b.txt', 'c.txt']" in result.output
        assert "Type: <class 'list'>" in result.output

    def test_multiple_option_type_validation(self):
        """Test that multiple options maintain proper type validation."""

        class TestArgs(AutoWryModel):
            """Test model with multiple option."""

            files: list[str] = Field(default=[], description="Files to process")

        @click.command()
        @click.option("--files", multiple=True)
        @generate_click_parameters(TestArgs, strict=False)
        @click.pass_context
        def test_command(ctx: click.Context, files: tuple[str, ...], **kwargs):
            """Test command with type validation."""
            kwargs["files"] = files

            print(f"Raw files from Click: {files!r}")
            print(f"Type: {type(files)}")

            config = TestArgs.from_click_context(ctx, **kwargs)

            print(f"Config files: {config.files!r}")
            print(f"Type: {type(config.files)}")

            # Test that we can iterate over the list
            for file in config.files:
                assert isinstance(file, str), f"Expected string, got {type(file)}: {file!r}"

            return config

        # Test with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with string files - should work correctly now
        result = runner.invoke(test_command, ["--files", "file1.txt", "--files", "file2.txt"])
        print("Type validation result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw files from Click: ('file1.txt', 'file2.txt')" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config files: ['file1.txt', 'file2.txt']" in result.output
        assert "Type: <class 'list'>" in result.output

    def test_multiple_option_with_other_types(self):
        """Test multiple options with different list types."""

        class TestArgs(AutoWryModel):
            """Test model with multiple option of different types."""

            int_values: list[int] = Field(default=[], description="Integer values")
            str_values: list[str] = Field(default=[], description="String values")

        @click.command()
        @generate_click_parameters(TestArgs, strict=False)
        @click.option("--int-values", multiple=True, type=int)
        @click.option("--str-values", multiple=True)
        @click.pass_context
        def test_command(ctx: click.Context, int_values: tuple[int, ...], str_values: tuple[str, ...], **kwargs):
            """Test command with different list types."""
            kwargs["int_values"] = int_values
            kwargs["str_values"] = str_values

            print(f"Raw int_values from Click: {int_values!r}")
            print(f"Raw str_values from Click: {str_values!r}")
            print(f"Type: {type(int_values)}")

            config = TestArgs.from_click_context(ctx, **kwargs)

            print(f"Config int_values: {config.int_values!r}")
            print(f"Config str_values: {config.str_values!r}")
            print(f"Type: {type(config.int_values)}")

            # Test that both are lists
            assert isinstance(
                config.int_values, list
            ), f"Expected list, got {type(config.int_values)}: {config.int_values!r}"
            assert isinstance(
                config.str_values, list
            ), f"Expected list, got {type(config.str_values)}: {config.str_values!r}"

            return config

        # Test with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with mixed types - should work correctly now
        result = runner.invoke(
            test_command, ["--int-values", "1", "--int-values", "2", "--str-values", "a", "--str-values", "b"]
        )
        print("Mixed types result:")
        print(result.output)
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Type: <class 'tuple'>" in result.output
        assert "Type: <class 'list'>" in result.output
        # Check that both int and string values are handled correctly
        # Note: Click behavior varies by version - older versions don't convert types
        assert (
            "Raw int_values from Click: (1, 2)" in result.output
            or "Raw int_values from Click: ('1', '2')" in result.output
        )
        assert "Raw str_values from Click: ('a', 'b')" in result.output
        assert "Config int_values: [1, 2]" in result.output
        assert "Config str_values: ['a', 'b']" in result.output
