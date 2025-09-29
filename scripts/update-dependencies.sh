#!/usr/bin/env bash
# Update poetry.lock with latest compatible versions
# This ensures all dependencies are up-to-date within version constraints

set -euo pipefail

echo "📦 Updating Poetry dependencies..."
echo ""

# Show current outdated packages
echo "Current outdated packages:"
poetry show --outdated || echo "  (none found or poetry show --outdated not available)"
echo ""

# Update all dependencies to latest compatible versions
echo "Running poetry update..."
poetry update

echo ""
echo "✅ Dependencies updated successfully!"
echo ""

# Show what changed
if git diff --quiet poetry.lock; then
    echo "ℹ️  No changes to dependencies."
else
    echo "📝 Summary of changes:"
    echo ""
    # Show a summary of what changed
    git diff --stat poetry.lock
    echo ""
    echo "For detailed changes, run: git diff poetry.lock"
fi

echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff poetry.lock"
echo "  2. Test the changes: poetry run pytest"
echo "  3. Commit if tests pass: git add poetry.lock && git commit -m 'chore: update dependencies'"
echo ""
