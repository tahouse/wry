"""Accessor classes for WryModel field metadata."""

from typing import TYPE_CHECKING, Any

from .field_utils import extract_field_constraints, get_field_maximum, get_field_minimum
from .sources import ValueSource

if TYPE_CHECKING:
    from .model import WryModel


class SourceAccessor:
    """Accessor for field source information."""

    def __init__(self, config_instance: "WryModel") -> None:
        self._config = config_instance

    def __getattr__(self, name: str) -> ValueSource:
        sources: dict[str, ValueSource] = getattr(self._config, "_value_sources", {})
        return sources.get(name, ValueSource.DEFAULT)

    def __dir__(self) -> list[str]:
        sources = getattr(self._config, "_value_sources", {})
        return list(sources.keys())


class MinimumAccessor:
    """Accessor for field minimum values via attribute notation.

    Examples:
        >>> config.minimum.age  # Returns minimum age constraint
        >>> config.minimum.score  # Returns minimum score constraint
    """

    def __init__(self, config_instance: "WryModel") -> None:
        self._config = config_instance

    def __getattr__(self, name: str) -> int | float | None:
        if name not in self._config.__class__.model_fields:
            raise AttributeError(f"{self._config.__class__.__name__} has no field '{name}'")
        return get_field_minimum(self._config.__class__.model_fields[name])

    def __dir__(self) -> list[str]:
        return list(self._config.__class__.model_fields.keys())


class MaximumAccessor:
    """Accessor for field maximum values via attribute notation.

    Examples:
        >>> config.maximum.age  # Returns maximum age constraint
        >>> config.maximum.score  # Returns maximum score constraint
    """

    def __init__(self, config_instance: "WryModel") -> None:
        self._config = config_instance

    def __getattr__(self, name: str) -> int | float | None:
        if name not in self._config.__class__.model_fields:
            raise AttributeError(f"{self._config.__class__.__name__} has no field '{name}'")
        return get_field_maximum(self._config.__class__.model_fields[name])

    def __dir__(self) -> list[str]:
        return list(self._config.__class__.model_fields.keys())


class ConstraintsAccessor:
    """Accessor for field constraints via attribute notation.

    Examples:
        >>> config.constraints.age  # Returns all age constraints
        >>> config.constraints.name  # Returns all name constraints
    """

    def __init__(self, config_instance: "WryModel") -> None:
        self._config = config_instance

    def __getattr__(self, name: str) -> dict[str, Any]:
        if name not in self._config.__class__.model_fields:
            raise AttributeError(f"{self._config.__class__.__name__} has no field '{name}'")
        return extract_field_constraints(self._config.__class__.model_fields[name])

    def __dir__(self) -> list[str]:
        return list(self._config.__class__.model_fields.keys())


class DefaultsAccessor:
    """Accessor for field default values via attribute notation.

    Examples:
        >>> config.defaults.timeout  # Returns default timeout value
        >>> config.defaults.retries  # Returns default retries value
    """

    def __init__(self, config_instance: "WryModel") -> None:
        self._config = config_instance

    def __getattr__(self, name: str) -> Any:
        if name not in self._config.__class__.model_fields:
            raise AttributeError(f"{self._config.__class__.__name__} has no field '{name}'")
        return self._config.__class__.model_fields[name].default

    def __dir__(self) -> list[str]:
        return list(self._config.__class__.model_fields.keys())
