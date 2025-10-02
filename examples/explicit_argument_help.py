"""Example demonstrating explicit click.argument with help text injection."""

from typing import Annotated

import click
from pydantic import ConfigDict, Field

from wry import AutoArgument, AutoWryModel


class FileProcessorArgs(AutoWryModel):
    """Configuration for file processing command."""

    model_config = ConfigDict(env_prefix="FILEPROC_")

    # Explicit click.argument with Field description
    input_file: Annotated[
        str,
        click.argument("input_file", type=click.Path(exists=False, path_type=str)),
    ] = Field(
        description="Input file path to process",
    )

    # AutoArgument with Field description
    output_dir: Annotated[str, AutoArgument] = Field(
        default="./output",
        description="Directory where results will be saved",
    )


@click.command()
@FileProcessorArgs.generate_click_parameters()
def process(**kwargs):
    """Process input file and save results.

    This command demonstrates argument help text injection.
    """
    config = FileProcessorArgs(**kwargs)
    click.echo(f"Processing: {config.input_file}")
    click.echo(f"Output directory: {config.output_dir}")
    click.echo("")
    click.echo("Field descriptions:")
    click.echo(f"  input_file: {FileProcessorArgs.model_fields['input_file'].description}")
    click.echo(f"  output_dir: {FileProcessorArgs.model_fields['output_dir'].description}")


if __name__ == "__main__":
    process()
