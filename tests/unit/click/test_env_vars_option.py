"""Test Click environment variables option functionality."""

from typing import Annotated, ClassVar

import click
from click.testing import CliRunner
from pydantic import BaseModel

from wry import AutoOption, WryModel, generate_click_parameters


class TestEnvVarsOption:
    """Test the --show-env-vars option functionality."""

    def test_show_env_vars_flag(self):
        """Test that --show-env-vars flag is added and works."""

        class Config(BaseModel):
            env_prefix: str = "APP_"
            api_key: Annotated[str, AutoOption] = "default"
            timeout: Annotated[int, AutoOption] = 30

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            return kwargs

        # Check that show-env-vars option exists
        show_env_option = next((p for p in cmd.params if p.name == "show_env_vars"), None)
        assert show_env_option is not None
        assert show_env_option.is_flag
        assert show_env_option.is_eager
        assert not show_env_option.expose_value

    def test_show_env_vars_execution(self):
        """Test that --show-env-vars prints env vars and exits."""

        class Config(WryModel):
            env_prefix: ClassVar[str] = "TEST_"
            database_url: Annotated[str, AutoOption] = "sqlite:///:memory:"

        @click.command()
        @generate_click_parameters(Config)
        def cmd(**kwargs):
            # Should not reach here when --show-env-vars is used
            return "command executed"

        runner = CliRunner()
        result = runner.invoke(cmd, ["--show-env-vars"])

        # Should exit with code 0
        assert result.exit_code == 0
        # Should print environment variables
        assert "TEST_DATABASE_URL" in result.output

    def test_model_without_print_env_vars(self):
        """Test handling of model without print_env_vars method."""

        class SimpleModel(BaseModel):
            # No env_prefix, no print_env_vars method
            value: Annotated[str, AutoOption] = "default"

        @click.command()
        @generate_click_parameters(SimpleModel)
        def cmd(**kwargs):
            return kwargs

        # Should still add the option but handle gracefully
        show_env_option = next((p for p in cmd.params if p.name == "show_env_vars"), None)
        assert show_env_option is not None
