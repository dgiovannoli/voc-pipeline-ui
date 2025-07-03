import click
from .processor import process_transcript, validate, build_table

@click.group()
def cli():
    """VoC Pipeline CLI tools"""
    pass

cli.add_command(process_transcript)
cli.add_command(validate)
cli.add_command(build_table)

if __name__ == "__main__":
    cli() 