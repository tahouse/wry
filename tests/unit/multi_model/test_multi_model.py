"""Test coverage gaps in multi_model.py module."""

from pydantic import BaseModel, Field

from wry import create_models


class TestMultiModelCoverage:
    """Test multi_model coverage gaps."""

    def test_create_models_without_context(self):
        """Test create_models when ctx is None (line 110)."""

        class Config1(BaseModel):
            name: str = Field(default="test")

        class Config2(BaseModel):
            count: int = Field(default=0)

        # Call with ctx=None to hit line 110
        kwargs = {"name": "custom", "count": 42}
        models = create_models(None, kwargs, Config1, Config2)

        assert Config1 in models
        assert Config2 in models
        assert models[Config1].name == "custom"
        assert models[Config2].count == 42

    def test_create_models_with_non_dry_model(self):
        """Test create_models with regular BaseModel (not WryModel)."""

        class RegularModel(BaseModel):
            value: str = "default"

        # Even with ctx, should use line 110 for non-WryModel
        from click import Context, command

        @command()
        def dummy_cmd():
            pass

        ctx = Context(dummy_cmd)

        kwargs = {"value": "test"}
        models = create_models(ctx, kwargs, RegularModel)

        assert RegularModel in models
        assert models[RegularModel].value == "test"
