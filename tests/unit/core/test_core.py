"""Test core functionality of wry."""

from pydantic import Field

from wry import TrackedValue, ValueSource, WryModel


class TestWryModel:
    """Test the WryModel base class."""

    def test_basic_model_creation(self):
        """Test creating a basic model."""

        class SimpleConfig(WryModel):
            name: str = Field(default="test")
            count: int = Field(default=10)

        config = SimpleConfig()
        assert config.name == "test"
        assert config.count == 10

        # Check source tracking
        assert config.source.name == ValueSource.DEFAULT
        assert config.source.count == ValueSource.DEFAULT

    def test_create_with_sources(self):
        """Test creating a model with explicit source tracking."""

        class SimpleConfig(WryModel):
            name: str
            count: int = Field(default=10)

        config = SimpleConfig.create_with_sources(
            {
                "name": TrackedValue("cli-value", ValueSource.CLI),
                "count": TrackedValue(20, ValueSource.JSON),
            }
        )

        assert config.name == "cli-value"
        assert config.count == 20
        assert config.source.name == ValueSource.CLI
        assert config.source.count == ValueSource.JSON

    def test_field_constraints(self):
        """Test field constraint extraction."""

        class ConstrainedConfig(WryModel):
            age: int = Field(default=25, ge=0, le=120)
            score: float = Field(default=0.0, ge=0.0, le=100.0)
            name: str = Field(default="", min_length=1, max_length=50)

        config = ConstrainedConfig()

        # Test minimum accessor
        assert config.minimum.age == 0
        assert config.minimum.score == 0.0

        # Test maximum accessor
        assert config.maximum.age == 120
        assert config.maximum.score == 100.0

        # Test constraints accessor
        age_constraints = config.constraints.age
        assert age_constraints["ge"] == 0
        assert age_constraints["le"] == 120
        assert age_constraints["default"] == 25

    def test_env_var_loading(self):
        """Test loading configuration from environment variables."""
        import os

        class EnvConfig(WryModel):
            env_prefix = "DRYCLI_"
            debug: bool = Field(default=False)
            timeout: int = Field(default=30)

        # Set environment variables
        os.environ["DRYCLI_DEBUG"] = "true"
        os.environ["DRYCLI_TIMEOUT"] = "60"

        try:
            config = EnvConfig.load_from_env()
            assert config.debug is True
            assert config.timeout == 60
            assert config.source.debug == ValueSource.ENV
            assert config.source.timeout == ValueSource.ENV
        finally:
            # Clean up
            os.environ.pop("DRYCLI_DEBUG", None)
            os.environ.pop("DRYCLI_TIMEOUT", None)

    def test_env_var_names(self):
        """Test environment variable name generation."""

        class TestConfig(WryModel):
            env_prefix = "DRYCLI_"
            debug_mode: bool = Field(default=False)
            max_retries: int = Field(default=3)

        env_names = TestConfig.get_env_var_names()
        assert env_names["debug_mode"] == "DRYCLI_DEBUG_MODE"
        assert env_names["max_retries"] == "DRYCLI_MAX_RETRIES"

    def test_sources_summary(self):
        """Test getting a summary of value sources."""

        class TestConfig(WryModel):
            a: str = Field(default="default")
            b: int = Field(default=1)
            c: bool = Field(default=False)
            d: float = Field(default=1.0)

        config = TestConfig.create_with_sources(
            {
                "a": TrackedValue("cli", ValueSource.CLI),
                "b": TrackedValue(2, ValueSource.JSON),
                "c": TrackedValue(True, ValueSource.ENV),
                "d": TrackedValue(2.0, ValueSource.DEFAULT),
            }
        )

        summary = config.get_sources_summary()
        assert "a" in summary[ValueSource.CLI]
        assert "b" in summary[ValueSource.JSON]
        assert "c" in summary[ValueSource.ENV]
        assert "d" in summary[ValueSource.DEFAULT]

    def test_model_dump_excludes_accessors(self):
        """Test that model_dump excludes accessor properties."""

        class SimpleConfig(WryModel):
            name: str = Field(default="test")
            value: int = Field(default=42)

        config = SimpleConfig()
        dumped = config.model_dump()

        # Should only have actual fields
        assert set(dumped.keys()) == {"name", "value"}
        assert "source" not in dumped
        assert "minimum" not in dumped
        assert "maximum" not in dumped
        assert "constraints" not in dumped
        assert "defaults" not in dumped

    def test_field_range(self):
        """Test getting field ranges."""

        class RangeConfig(WryModel):
            bounded: int = Field(default=50, ge=10, le=100)
            lower_only: int = Field(default=0, ge=0)
            upper_only: int = Field(default=100, le=100)
            unbounded: int = Field(default=42)

        config = RangeConfig()

        # Bounded field
        min_val, max_val = config.get_field_range("bounded")
        assert min_val == 10
        assert max_val == 100

        # Lower bounded only
        min_val, max_val = config.get_field_range("lower_only")
        assert min_val == 0
        assert max_val is None

        # Upper bounded only
        min_val, max_val = config.get_field_range("upper_only")
        assert min_val is None
        assert max_val == 100

        # Unbounded
        min_val, max_val = config.get_field_range("unbounded")
        assert min_val is None  # No constraints means no minimum
        assert max_val is None
