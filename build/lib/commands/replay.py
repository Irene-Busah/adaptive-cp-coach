import os
import json
import requests
import typer
from rich.console import Console
from rich.syntax import Syntax

console = Console()
replay_app = typer.Typer(help="Replay the last failing API request locally")

CACHE_FILE = "/tmp/dev_toolbox_last_request.json"

@replay_app.callback(invoke_without_command=True)
def replay():
    if not os.path.exists(CACHE_FILE):
        console.print("[red]No cached API request found.[/red] Ensure the background daemon is running.")
        raise typer.Exit(1)
        
    with open(CACHE_FILE, "r") as f:
        try:
            req_data = json.load(f)
        except json.JSONDecodeError:
            console.print("[red]Cache file is corrupt.[/red]")
            raise typer.Exit(1)
            
    method = req_data.get("method", "GET").upper()
    url = req_data.get("url", "")
    headers = req_data.get("headers", {})
    body = req_data.get("body", {})
    
    console.print(f"[bold cyan]Replaying: {method} {url}[/bold cyan]")
    
    # We could open an interactive editor here:
    # editor = os.environ.get("EDITOR", "nano")
    # subprocess.run([editor, CACHE_FILE])
    
    console.print("[yellow]Sending request...[/yellow]")
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=body)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=body)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, json=body)
        else:
            console.print(f"[red]Unsupported method: {method}[/red]")
            raise typer.Exit(1)
            
        console.print(f"[bold {'green' if resp.ok else 'red'}]Status: {resp.status_code}[/bold {'green' if resp.ok else 'red'}]")
        
        try:
            resp_json = resp.json()
            syntax = Syntax(json.dumps(resp_json, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        except:
            console.print(resp.text)
            
    except Exception as e:
        console.print(f"[red]Request failed: {str(e)}[/red]")
