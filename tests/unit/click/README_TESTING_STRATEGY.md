# Testing Strategy for Click Integration

## Problem with Current Tests

Many of our Click integration tests are brittle because they test exact string output formats. This makes them break whenever we improve user-facing messages, creating a maintenance burden.

## Recommended Approach

### 1. Test Behavior, Not Format

Instead of:

```python
assert result == "length >= 5"
```

Test that:

- The constraint is recognized (not None)
- Key information is preserved (the value "5")
- The semantic meaning is correct (it's about minimum length)

### 2. Use Behavioral Test Patterns

See `test_constraint_behavior.py` and `test_lambda_behavior.py` for examples of better patterns:

```python
# Test that values are present
assert "5" in result

# Test semantic meaning with multiple acceptable formats
assert any(word in result.lower() for word in ["minimum", "min", "at least", ">="])
```

### 3. Benefits

- Tests don't break when we improve message clarity
- Can evolve user-facing strings without updating tests
- Focus on what matters: correct behavior, not exact format
- Easier to maintain and understand

### 4. When Exact Format Matters

Only test exact format when:

- It's part of a public API contract
- It's machine-readable output (JSON, etc.)
- Backward compatibility is required

For user-facing messages, prefer behavioral tests.
