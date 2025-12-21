import click
from rich.console import Console
from rich.table import Table
from utils.api_client import make_request


console = Console()


@click.group()
def pids():
    """List and retrieve PID records from the PID service."""
    pass


@pids.command(name="list")
@click.option('--page', type=int, default=0, show_default=True,
              help="Page number (zero-indexed) to retrieve.")
@click.option('--page-size', type=int, default=25, show_default=True,
              help="Number of items per page.")
@click.pass_context
def list_pids(ctx, page, page_size):
    """List all PIDs (with pagination)."""
    api_url = ctx.obj['API_URL']
    params = {'page': page, 'page_size': page_size}
    response = make_request("GET", api_url, "/pids", params=params)

    if not response:
        console.print("[red]❌ Failed to reach PID service[/red]")
        return

    if response.status_code != 200:
        console.print(f"[red]❌ Error {response.status_code}: {response.text}[/red]")
        return

    pid_list = response.json()
    if not pid_list:
        console.print("[yellow]No PIDs found on this page.[/yellow]")
        return

    table = Table(title=f"PIDs (page {page}, size {page_size})")
    table.add_column("PID", style="cyan")
    for pid in pid_list:
        table.add_row(pid)
    console.print(table)


@pids.command(name="get")
@click.argument('pid')
@click.pass_context
def get_pid(ctx, pid):
    """
    Retrieve a PID record. PID can be in one of two formats:
    - prefix/id
    - id  (uses application default prefix)
    """
    api_url = ctx.obj['API_URL']

    # Determine which endpoint to hit
    if '/' in pid:
        prefix, identifier = pid.split('/', 1)
        endpoint = f"/pids/{prefix}/{identifier}"
    else:
        endpoint = f"/pids/{pid}"

    response = make_request("GET", api_url, endpoint)
    if not response:
        console.print("[red]❌ Failed to reach PID service[/red]")
        return

    if response.status_code == 200:
        console.print_json(data=response.json())
    elif response.status_code == 404:
        console.print(f"[yellow]PID '{pid}' not found.[/yellow]")
    else:
        console.print(f"[red]❌ Error {response.status_code}: {response.text}[/red]")
