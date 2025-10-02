#!/usr/bin/env bash
# Update dependencies to latest compatible versions
# Dependencies are specified in pyproject.toml [project.dependencies]

set -euo pipefail

echo "📦 Updating dependencies..."
echo ""

# Ensure venv is activated
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "⚠️  No virtual environment detected. Activate one first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    exit 1
fi

# Show current outdated packages
echo "Current outdated packages:"
pip list --outdated || echo "  (all up to date)"
echo ""

# Update all dependencies to latest compatible versions
echo "Upgrading all dependencies..."
pip install -e ".[dev]" --upgrade

echo ""
echo "✅ Dependencies updated successfully!"
echo ""

# Show installed versions
echo "📝 Currently installed versions:"
pip list | grep -E "click|pydantic|pytest|ruff|mypy" || true

echo ""
echo "Next steps:"
echo "  1. Test the changes: pytest"
echo "  2. Run checks: pre-commit run --all-files"
echo "  3. Commit if tests pass"
echo ""
