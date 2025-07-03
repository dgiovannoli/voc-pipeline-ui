import click
from .processor import process_transcript

@click.group()
def cli():
    """VoC Pipeline CLI tools"""
    pass

cli.add_command(process_transcript)

if __name__ == "__main__":
    cli() 