import typer
from rich.console import Console
from rich import print

app = typer.Typer(help="The Unified Developer CLI Suite", add_completion=False)
console = Console()

@app.command()
def version():
    """Show the current version of the CLI."""
    console.print("[bold green]dev-toolbox[/bold green] version 0.1.0")

from commands import hop, replay
from server import daemon

app.add_typer(hop.hop_app, name="hop")
app.add_typer(replay.replay_app, name="replay")

@app.command()
def start_daemon():
    """Start the background listener daemon for API Replay."""
    daemon.run_daemon()

if __name__ == "__main__":
    app()
