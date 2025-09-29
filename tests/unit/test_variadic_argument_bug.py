"""Tests for the variadic argument bug in wry.

This module tests the bug where variadic Click arguments (nargs=-1) are
incorrectly converted to strings when used with generate_click_parameters.
"""

import click
from pydantic import Field

from wry import AutoWryModel, generate_click_parameters
from wry.core import WryModel


class TestVariadicArgumentBug:
    """Test cases for the variadic argument bug."""

    def test_variadic_argument_bug_reproduction(self):
        """Reproduce the variadic argument bug as described in the issue."""
        from typing import Annotated

        class TestArgs(AutoWryModel):
            """Test model with variadic nodes."""

            nodes: Annotated[tuple[str, ...], click.argument("nodes", nargs=-1)] = Field(
                default=(),
                description="Test nodes",
            )
            other_option: str = Field(
                default="default",
                description="Another option",
            )

        @click.command()
        @generate_click_parameters(TestArgs, strict=False)
        @click.pass_context
        def test_command(ctx: click.Context, nodes: tuple[str, ...], **kwargs):
            """Test command to demonstrate wry bug."""
            kwargs["nodes"] = nodes

            print(f"Raw nodes from Click: {nodes!r}")
            print(f"Type: {type(nodes)}")

            config = TestArgs.from_click_context(ctx, **kwargs)
            print(f"Config nodes: {config.nodes!r}")
            print(f"Type: {type(config.nodes)}")

            return config

        # Test the bug by running the command with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with no arguments - should show the bug
        result = runner.invoke(test_command, [])
        print("No arguments result:")
        print(result.output)

        # Test with arguments - should work correctly now
        result = runner.invoke(test_command, ["node1", "node2"])
        print("With arguments result:")
        print(result.output)

        # The bug is now fixed - nodes are correctly passed as tuples
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw nodes from Click: ('node1', 'node2')" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config nodes: ('node1', 'node2')" in result.output

    def test_click_without_wry_works_correctly(self):
        """Test that Click without wry works correctly (baseline test)."""

        @click.command()
        @click.argument("nodes", nargs=-1)
        def test_click_only(nodes):
            """Click without wry works correctly."""
            print(f"Nodes: {nodes!r}")
            print(f"Type: {type(nodes)}")
            assert isinstance(nodes, tuple), f"Expected tuple, got {type(nodes)}: {nodes!r}"
            return nodes

        # Test with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with no arguments
        result = runner.invoke(test_click_only, [])
        assert result.exit_code == 0
        assert "Nodes: ()" in result.output
        assert "Type: <class 'tuple'>" in result.output

        # Test with arguments
        result = runner.invoke(test_click_only, ["node1", "node2"])
        assert result.exit_code == 0
        assert "Nodes: ('node1', 'node2')" in result.output
        assert "Type: <class 'tuple'>" in result.output

    def test_variadic_argument_with_wrymodel(self):
        """Test that variadic arguments work correctly with WryModel."""
        from typing import Annotated

        from wry.click_integration import AutoClickParameter

        class TestArgs(WryModel):
            """Test model with variadic nodes."""

            nodes: Annotated[tuple[str, ...], click.argument("nodes", nargs=-1)] = Field(
                default=(),
                description="Test nodes",
            )
            other_option: Annotated[str, AutoClickParameter.OPTION] = Field(
                default="default",
                description="Another option",
            )

        @click.command()
        @generate_click_parameters(TestArgs, strict=False)
        @click.pass_context
        def test_command(ctx: click.Context, nodes: tuple[str, ...], **kwargs):
            """Test command to demonstrate wry bug."""
            kwargs["nodes"] = nodes

            print(f"Raw nodes from Click: {nodes!r}")
            print(f"Type: {type(nodes)}")

            config = TestArgs.from_click_context(ctx, **kwargs)
            print(f"Config nodes: {config.nodes!r}")
            print(f"Type: {type(config.nodes)}")

            return config

        # Test the bug by running the command with Click's invoke
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with no arguments - should show the bug
        result = runner.invoke(test_command, [])
        print("No arguments result:")
        print(result.output)

        # Test with arguments - should work correctly now
        result = runner.invoke(test_command, ["node1", "node2"])
        print("With arguments result:")
        print(result.output)

        # The bug is now fixed - nodes are correctly passed as tuples
        assert result.exit_code == 0  # Should work correctly now
        # Check that the output shows the correct types and values
        assert "Raw nodes from Click: ('node1', 'node2')" in result.output
        assert "Type: <class 'tuple'>" in result.output
        assert "Config nodes: ('node1', 'node2')" in result.output
