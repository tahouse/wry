"""Test coverage gaps in accessors.py module."""

from pydantic import Field

from wry.core.model import WryModel


class TestAccessorDirMethods:
    """Test __dir__ methods on all accessors."""

    def test_minimum_accessor_dir(self):
        """Test MinimumAccessor __dir__ method."""

        class Config(WryModel):
            age: int = Field(default=25, ge=0, le=100)
            name: str = "test"

        config = Config()
        # Access the __dir__ method
        fields = dir(config.minimum)
        assert "age" in fields
        assert "name" in fields
        assert len(fields) == 2

    def test_maximum_accessor_dir(self):
        """Test MaximumAccessor __dir__ method."""

        class Config(WryModel):
            score: int = Field(default=50, ge=0, le=100)
            value: float = 1.0

        config = Config()
        # Access the __dir__ method
        fields = dir(config.maximum)
        assert "score" in fields
        assert "value" in fields
        assert len(fields) == 2

    def test_constraints_accessor_dir(self):
        """Test ConstraintsAccessor __dir__ method."""

        class Config(WryModel):
            count: int = Field(default=10, ge=0, multiple_of=5)
            name: str = Field(default="test", min_length=1)

        config = Config()
        # Access the __dir__ method
        fields = dir(config.constraints)
        assert "count" in fields
        assert "name" in fields
        assert len(fields) == 2

    def test_defaults_accessor_dir(self):
        """Test DefaultsAccessor __dir__ method."""

        class Config(WryModel):
            host: str = "localhost"
            port: int = 8080

        config = Config()
        # Access the __dir__ method
        fields = dir(config.defaults)
        assert "host" in fields
        assert "port" in fields
        assert len(fields) == 2

        # Test accessing default values (line 101)
        assert config.defaults.host == "localhost"
        assert config.defaults.port == 8080
