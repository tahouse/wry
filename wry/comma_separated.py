"""Support for comma-separated list inputs in Click options.

This module provides custom Click parameter types that parse comma-separated
strings into lists, offering an alternative to Click's default multiple=True behavior.

Two approaches are supported:

Approach 1: Per-field annotation (fine-grained control):
    ```python
    from wry import AutoWryModel, CommaSeparated
    from typing import Annotated

    class Config(AutoWryModel):
        # Standard behavior: --tags a --tags b --tags c
        standard_tags: list[str] = Field(default_factory=list)

        # Comma-separated: --csv-tags a,b,c
        csv_tags: Annotated[list[str], CommaSeparated] = Field(default_factory=list)
    ```

Approach 2: Model-wide ClassVar (all list fields):
    ```python
    from wry import AutoWryModel
    from typing import ClassVar

    class Config(AutoWryModel):
        # Enable comma-separated for ALL list fields
        comma_separated_lists: ClassVar[bool] = True

        # All accept comma-separated input
        tags: list[str] = Field(default_factory=list)    # --tags a,b,c
        ports: list[int] = Field(default_factory=list)   # --ports 80,443
    ```
"""

from typing import Any

import click


class CommaSeparatedStrings(click.ParamType):
    """Click parameter type for comma-separated string lists.

    Parses input like "python,rust,go" into ["python", "rust", "go"].
    Strips whitespace from each item.
    """

    name = "comma-separated strings"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> list[str]:
        """Convert comma-separated string to list of strings.

        Args:
            value: Input value (string or already a list)
            param: Click parameter
            ctx: Click context

        Returns:
            List of strings

        Raises:
            click.BadParameter: If value cannot be parsed
        """
        # Already a list (e.g., from default_factory)
        if isinstance(value, list):
            return value

        # Empty or None
        if not value:
            return []

        # Parse comma-separated string
        try:
            return [item.strip() for item in str(value).split(",") if item.strip()]
        except Exception as e:
            self.fail(f"{value!r} is not a valid comma-separated list: {e}", param, ctx)


class CommaSeparatedInts(click.ParamType):
    """Click parameter type for comma-separated integer lists.

    Parses input like "1,2,3" into [1, 2, 3].
    """

    name = "comma-separated integers"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> list[int]:
        """Convert comma-separated string to list of integers.

        Args:
            value: Input value (string or already a list)
            param: Click parameter
            ctx: Click context

        Returns:
            List of integers

        Raises:
            click.BadParameter: If value cannot be parsed
        """
        # Already a list (e.g., from default_factory)
        if isinstance(value, list):
            return value

        # Empty or None
        if not value:
            return []

        # Parse comma-separated string
        try:
            items = [item.strip() for item in str(value).split(",") if item.strip()]
            return [int(item) for item in items]
        except ValueError as e:
            self.fail(f"{value!r} contains invalid integer: {e}", param, ctx)
        except Exception as e:
            self.fail(f"{value!r} is not a valid comma-separated list: {e}", param, ctx)


class CommaSeparatedFloats(click.ParamType):
    """Click parameter type for comma-separated float lists.

    Parses input like "1.5,2.7,3.14" into [1.5, 2.7, 3.14].
    """

    name = "comma-separated floats"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> list[float]:
        """Convert comma-separated string to list of floats.

        Args:
            value: Input value (string or already a list)
            param: Click parameter
            ctx: Click context

        Returns:
            List of floats

        Raises:
            click.BadParameter: If value cannot be parsed
        """
        # Already a list (e.g., from default_factory)
        if isinstance(value, list):
            return value

        # Empty or None
        if not value:
            return []

        # Parse comma-separated string
        try:
            items = [item.strip() for item in str(value).split(",") if item.strip()]
            return [float(item) for item in items]
        except ValueError as e:
            self.fail(f"{value!r} contains invalid float: {e}", param, ctx)
        except Exception as e:
            self.fail(f"{value!r} is not a valid comma-separated list: {e}", param, ctx)


# Marker class for Annotated metadata
class CommaSeparated:
    """Marker to indicate a list field should accept comma-separated input.

    Usage:
        ```python
        from typing import Annotated
        from wry import AutoWryModel, CommaSeparated

        class Config(AutoWryModel):
            # Accepts: --tags python,rust,go
            tags: Annotated[list[str], CommaSeparated] = Field(default_factory=list)

            # Accepts: --ports 8080,8443,9000
            ports: Annotated[list[int], CommaSeparated] = Field(default_factory=list)
        ```

    Note:
        - This disables Click's multiple=True behavior
        - User must provide comma-separated values in a single string
        - Cannot combine with multiple invocations (--tags a --tags b won't work)
    """

    pass
