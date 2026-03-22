import subprocess
import typer
from rich.console import Console

console = Console()
hop_app = typer.Typer(help="Safely stash changes and hop between branches")

def get_current_branch() -> str:
    res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    return res.stdout.strip()

def has_uncommitted_changes() -> bool:
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    return len(res.stdout.strip()) > 0

@hop_app.callback(invoke_without_command=True)
def hop(
    branch: str = typer.Argument(..., help="The branch to hop to, or '-' to hop back")
):
    current = get_current_branch()
    if not current:
        console.print("[red]Error: Not currently in a git repository or no commits yet.[/red]")
        raise typer.Exit(1)
        
    if branch == "-":
        console.print("[cyan]Hopping back to previous branch...[/cyan]")
        subprocess.run(["git", "checkout", "-"])
        console.print("[cyan]Popping the most recent stash...[/cyan]")
        # We try to pop, but if there's nothing, git will just print a message
        subprocess.run(["git", "stash", "pop"])
        console.print("[bold green]Successfully hopped back![/bold green]")
        return
        
    if branch == current:
        console.print(f"[yellow]Already on branch '{current}'[/yellow]")
        return
        
    if has_uncommitted_changes():
        stash_msg = f"Auto-stash before hopping from {current} to {branch}"
        console.print(f"[yellow]Changes detected! Saving stash...[/yellow]")
        subprocess.run(["git", "stash", "save", stash_msg])
    
    console.print(f"[cyan]Checking out branch '{branch}'...[/cyan]")
    res = subprocess.run(["git", "checkout", branch])
    if res.returncode != 0:
        console.print(f"[red]Failed to checkout '{branch}'. Check if it exists branch.[/red]")
        raise typer.Exit(1)
        
    console.print(f"[cyan]Pulling latest changes...[/cyan]")
    # We ignore standard output/error to not clutter the screen 
    subprocess.run(["git", "pull"], capture_output=True)
    
    console.print(f"[bold green]Successfully hopped to {branch}![/bold green]")
