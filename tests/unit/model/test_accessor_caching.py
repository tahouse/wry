"""Test WryModel accessor property caching."""

from wry.core.accessors import ConstraintsAccessor, DefaultsAccessor
from wry.core.model import WryModel


class TestAccessorCaching:
    """Test that accessor properties are properly cached."""

    def test_constraints_accessor_cached(self):
        """Test that constraints accessor is created once and cached."""

        class Config(WryModel):
            name: str = "default"
            value: int = 0

        config = Config()

        # First access should create the accessor
        constraints1 = config.constraints
        assert isinstance(constraints1, ConstraintsAccessor)

        # Second access should return the same instance
        constraints2 = config.constraints
        assert constraints1 is constraints2

        # Check that it's in the cache
        assert "constraints" in config._accessor_instances
        assert config._accessor_instances["constraints"] is constraints1

    def test_defaults_accessor_cached(self):
        """Test that defaults accessor is created once and cached."""

        class Config(WryModel):
            host: str = "localhost"
            port: int = 8080

        config = Config()

        # First access creates it
        defaults1 = config.defaults
        assert isinstance(defaults1, DefaultsAccessor)

        # Second access returns same instance
        defaults2 = config.defaults
        assert defaults1 is defaults2

        # Check cache
        assert "defaults" in config._accessor_instances
        assert config._accessor_instances["defaults"] is defaults1

    def test_multiple_accessors_cached_separately(self):
        """Test that different accessors are cached separately."""

        class Config(WryModel):
            name: str = "test"

        config = Config()

        # Access different accessors
        _ = config.constraints
        _ = config.defaults
        _ = config.minimum
        _ = config.maximum

        # All should be cached
        assert len(config._accessor_instances) >= 4
        assert "constraints" in config._accessor_instances
        assert "defaults" in config._accessor_instances
        assert "minimum" in config._accessor_instances
        assert "maximum" in config._accessor_instances

        # Each should be a different instance
        accessors = list(config._accessor_instances.values())
        for i, accessor1 in enumerate(accessors):
            for j, accessor2 in enumerate(accessors):
                if i != j:
                    assert accessor1 is not accessor2
