#!/usr/bin/env python3
"""Extract release notes from CHANGELOG.md for a specific version."""

import re
import sys
from pathlib import Path


def extract_version_notes(version: str) -> str:
    """Extract the changelog entry for a specific version."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("Error: CHANGELOG.md not found!", file=sys.stderr)
        sys.exit(1)

    content = changelog_path.read_text()

    # Normalize version (remove 'v' prefix if present)
    version = version.lstrip("v")

    # Pattern to match the version section
    # Matches: ## [0.1.0] - 2024-12-19
    version_pattern = rf"## \[{re.escape(version)}\][^\n]*\n"

    # Find the start of this version's section
    match = re.search(version_pattern, content)
    if not match:
        print(f"Error: Version {version} not found in CHANGELOG.md", file=sys.stderr)
        sys.exit(1)

    start = match.end()

    # Find the next version section (to know where this one ends)
    next_version_pattern = r"\n## \[[^\]]+\][^\n]*\n"
    next_match = re.search(next_version_pattern, content[start:])

    if next_match:
        # Extract content up to the next version
        end = start + next_match.start()
        notes = content[start:end].strip()
    else:
        # This is the last version, extract until end or until link references
        # Look for the link references section at the bottom
        link_pattern = r"\n\[[^\]]+\]:\s*https?://"
        link_match = re.search(link_pattern, content[start:])
        if link_match:
            end = start + link_match.start()
            notes = content[start:end].strip()
        else:
            # No link section, take everything until the end
            notes = content[start:].strip()

    # Clean up the notes
    # Remove multiple consecutive newlines
    notes = re.sub(r"\n{3,}", "\n\n", notes)

    return notes


def format_for_github(notes: str, version: str) -> str:
    """Format the release notes for GitHub."""
    # Normalize version for display
    version_display = version if version.startswith("v") else f"v{version}"
    version_number = version.lstrip("v")

    # Add installation instructions
    install_section = f"""## Installation

Install from PyPI:
```bash
pip install wry=={version_number}
```

Install latest dev version:
```bash
pip install --pre wry
```

View on PyPI: https://pypi.org/project/wry/

## What's Changed

{notes}

---

**Full Changelog**: https://github.com/tahouse/wry/compare/v0.0.3...{version_display}"""

    return install_section


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python extract_release_notes.py <version>")
        print("Example: python extract_release_notes.py 0.1.0")
        print("         python extract_release_notes.py v0.1.0")
        sys.exit(1)

    version = sys.argv[1]

    try:
        notes = extract_version_notes(version)
        formatted = format_for_github(notes, version)
        print(formatted)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
