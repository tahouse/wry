"""Value source tracking for wry argument values."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValueSource(Enum):
    """Track where an argument value came from."""

    DEFAULT = "default"
    CLI = "cli"
    ENV = "env"
    JSON = "json"


@dataclass
class TrackedValue:
    """An argument value with its source."""

    value: Any
    source: ValueSource

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"TrackedValue({self.value!r}, {self.source.value})"


@dataclass
class FieldWithSource:
    """Field value with its source information."""

    value: Any
    source: ValueSource

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"FieldWithSource({self.value!r}, {self.source.value})"

    # Allow the field to behave like its value for most operations
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FieldWithSource):
            return bool(self.value == other.value)
        return bool(self.value == other)

    def __hash__(self) -> int:
        return hash(self.value)
