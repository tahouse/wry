"""Help system for wry package.

Provides different levels of documentation:
- Quick help (README summary)
- AI Knowledge Base (for LLMs)
- Source tracking guide
- Architecture documentation
"""

from pathlib import Path
from typing import Literal

HelpType = Literal["readme", "ai", "sources", "architecture", "examples"]


def get_help_content(help_type: HelpType = "readme") -> str:
    """Get help content of specified type.

    Args:
        help_type: Type of help to retrieve
            - "readme": Main README documentation
            - "ai": AI/LLM knowledge base
            - "sources": Source tracking documentation
            - "architecture": Architecture and design
            - "examples": List of examples

    Returns:
        Help content as string
    """
    # Get package root directory
    package_root = Path(__file__).parent.parent

    if help_type == "readme":
        readme_path = package_root / "README.md"
        if readme_path.exists():
            return readme_path.read_text()
        return "README.md not found"

    elif help_type == "ai":
        ai_kb_path = package_root / "AI_KNOWLEDGE_BASE.md"
        if ai_kb_path.exists():
            return ai_kb_path.read_text()
        return "AI_KNOWLEDGE_BASE.md not found"

    elif help_type == "sources":
        # Extract source tracking section from AI knowledge base
        ai_kb_path = package_root / "AI_KNOWLEDGE_BASE.md"
        if ai_kb_path.exists():
            content = ai_kb_path.read_text()
            # Find test coverage section
            if "## Test Coverage Summary" in content:
                start = content.index("## Test Coverage Summary")
                # Find next major section or end
                next_section = content.find("\n## Common Issues", start + 1)
                if next_section > 0:
                    return "# Source Tracking - " + content[start:next_section]
                # Try another section
                next_section = content.find("\n## ", start + 1)
                if next_section > 0:
                    return "# Source Tracking - " + content[start:next_section]
                return "# Source Tracking - " + content[start:]
        return "Source tracking documentation not found"

    elif help_type == "architecture":
        # Extract architecture section from README
        readme_path = package_root / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            # Find architecture section
            if "## Architecture" in content:
                start = content.index("## Architecture")
                # Find next major section
                next_section = content.find("\n## ", start + 1)
                if next_section > 0:
                    return content[start:next_section]
                return content[start:]
        return "Architecture documentation not found"

    elif help_type == "examples":
        examples_dir = package_root / "examples"
        if examples_dir.exists():
            examples = []
            examples.append("# wry Examples\n")
            examples.append("\nAvailable examples in examples/ directory:\n")

            for example_file in sorted(examples_dir.glob("*.py")):
                # Read first docstring
                content = example_file.read_text()
                lines = content.split("\n")
                description = ""
                if lines and lines[0].startswith('"""'):
                    # Multi-line docstring
                    for line in lines[1:]:
                        if '"""' in line:
                            break
                        description += line.strip() + " "

                examples.append(f"\n**{example_file.name}**")
                if description:
                    examples.append(f"  {description.strip()}")
                examples.append(f"  Run: `python examples/{example_file.name}`")

            return "\n".join(examples)
        return "Examples directory not found"


def print_help(help_type: HelpType = "readme", pager: bool = True) -> None:
    """Print help content, optionally using a pager.

    Args:
        help_type: Type of help to display
        pager: If True, use click's pager for long content
    """
    import click

    content = get_help_content(help_type)

    if pager and len(content.split("\n")) > 50:
        click.echo_via_pager(content)
    else:
        click.echo(content)


def show_help_index() -> None:
    """Show index of available help topics."""
    import click

    click.echo("=" * 60)
    click.echo("wry Help System")
    click.echo("=" * 60)
    click.echo()
    click.echo("Available help topics:")
    click.echo()
    click.echo("  readme       - Main README documentation (default)")
    click.echo("  ai           - AI/LLM Knowledge Base (comprehensive)")
    click.echo("  sources      - Source tracking test coverage")
    click.echo("  architecture - Architecture and design documentation")
    click.echo("  examples     - List of available examples")
    click.echo()
    click.echo("Usage:")
    click.echo("  python -m wry.help_system [topic]")
    click.echo("  python -m wry.help_system ai")
    click.echo()
    click.echo("Or in Python:")
    click.echo("  from wry.help_system import print_help")
    click.echo("  print_help('ai')")
    click.echo()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        help_type_arg = sys.argv[1]
        if help_type_arg in ["readme", "ai", "sources", "architecture", "examples"]:
            print_help(help_type_arg)  # type: ignore
        else:
            print(f"Unknown help type: {help_type_arg}")
            show_help_index()
    else:
        show_help_index()
