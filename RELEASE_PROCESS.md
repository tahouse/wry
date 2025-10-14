# Release Process for Wry

This document outlines the correct process for creating a new release.

## Development Workflow

### During Development (Between Releases)

As you make commits, **ALWAYS update CHANGELOG.md** under `[Unreleased]`:

```markdown
## [Unreleased]

### Added
- New feature X

### Fixed
- Bug Y
```

**Every commit** should add its changes to the `[Unreleased]` section. This keeps the changelog up-to-date continuously.

### When Ready to Release

Follow these steps IN ORDER:

1. **Verify all changes are in [Unreleased]**
   - Check that CHANGELOG.md `[Unreleased]` section has all changes since last release
   - Check TODO.md - all planned release items should be completed
   - Ensure all tests pass (`pytest`)
   - Fix any linting issues

2. **Update CHANGELOG.md for release**
   - Change `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`
   - Add a new empty `## [Unreleased]` section above it
   - Update comparison links at bottom if present

   **Example**:
   ```markdown
   ## [Unreleased]

   ## [0.5.0] - 2025-10-14

   ### Added
   - Feature from unreleased section (now part of 0.5.0)
   ```

3. **Update documentation**
   - Update README.md if needed
   - Update AI_KNOWLEDGE_BASE.md version numbers
   - Update any affected documentation

4. **Commit the release preparation**
   ```bash
   git add -A
   git commit -m "chore: prepare for vX.Y.Z release"
   ```

5. **Create signed tag on the release commit**
   ```bash
   git tag -s vX.Y.Z -m "Release vX.Y.Z: brief description"
   ```

6. **Push changes and tag**
   ```bash
   git push origin main
   git push origin vX.Y.Z
   ```

### After the Release

Continue development by:
1. Adding new changes to the (now empty) `[Unreleased]` section in CHANGELOG.md
2. Updating TODO.md:
   - Archive or remove completed items from the released version
   - Add new tasks or features planned for next release
   - Update roadmap and priorities
3. Update version numbers in AI_KNOWLEDGE_BASE.md if not already done

## Example

For v0.1.8 release:

```bash
# 1. Make code changes
# ... implement type annotation improvements ...

# 2. Update CHANGELOG.md
# Add new section:
## [0.1.8] - 2025-09-10

### Fixed
- Improved type annotations for `generate_click_parameters` decorator

# 3. Commit everything
git add -A
git commit -m "chore: prepare for v0.1.8 release"

# 4. Create tag
git tag -s v0.1.8 -m "Release v0.1.8: improve type annotations"

# 5. Push
git push origin main
git push origin v0.1.8
```

## Common Mistakes to Avoid

- ❌ Creating the tag before updating CHANGELOG.md
- ❌ Forgetting to update comparison links in CHANGELOG.md
- ❌ Not running `./check.sh` before tagging
- ❌ Creating unsigned tags (always use `-s` for signed tags)

## CI/CD Pipeline

Once a tag is pushed, the GitHub Actions workflow will:
1. Run all tests across Python 3.10, 3.11, and 3.12
2. Build the distribution packages
3. Publish to PyPI (for tags) or TestPyPI (for main branch)
4. Create a GitHub release with notes from CHANGELOG.md
