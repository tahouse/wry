"""Test help system functionality."""

import click
from click.testing import CliRunner

from wry.help_system import get_help_content, print_help, show_help_index


class TestHelpSystem:
    """Test help system functions."""

    def test_get_help_content_readme(self):
        """Test getting README content."""
        content = get_help_content("readme")
        assert "wry" in content.lower()
        assert len(content) > 100

    def test_get_help_content_ai(self):
        """Test getting AI knowledge base."""
        content = get_help_content("ai")
        assert "AI/LLM Knowledge Base" in content
        assert "Configuration Flow" in content
        assert len(content) > 1000

    def test_get_help_content_sources(self):
        """Test getting source tracking info."""
        content = get_help_content("sources")
        # Should extract from AI KB or return not found message
        assert "Source Tracking" in content or "Test Coverage" in content or "not found" in content

    def test_get_help_content_architecture(self):
        """Test getting architecture info."""
        content = get_help_content("architecture")
        assert "Architecture" in content or "not found" in content.lower()

    def test_get_help_content_examples(self):
        """Test getting examples list."""
        content = get_help_content("examples")
        assert "Examples" in content or "examples" in content
        assert ".py" in content

    def test_print_help_no_pager(self):
        """Test print_help without pager."""

        # Redirect output by using Click's testing utilities
        @click.command()
        def test_cmd():
            print_help("readme", pager=False)

        runner = CliRunner()
        result = runner.invoke(test_cmd)
        assert result.exit_code == 0
        # Should have printed something
        assert len(result.output) > 0

    def test_print_help_with_pager(self):
        """Test print_help with pager (for long content)."""

        @click.command()
        def test_cmd():
            print_help("ai", pager=True)

        runner = CliRunner()
        result = runner.invoke(test_cmd)
        assert result.exit_code == 0

    def test_show_help_index(self):
        """Test showing help index."""

        @click.command()
        def test_cmd():
            show_help_index()

        runner = CliRunner()
        result = runner.invoke(test_cmd)
        assert result.exit_code == 0
        assert "Help System" in result.output
        assert "readme" in result.output
        assert "ai" in result.output
        assert "sources" in result.output
        assert "architecture" in result.output
        assert "examples" in result.output
