import click
import json
import requests
from rich.console import Console

from commands.auth import auth
from commands.documents import documents
from commands.pids import pids
from commands.blockchain import blockchain
from commands.artifacts import artifacts
from utils.api_client import make_request

console = Console()


@click.group()
@click.option(
    '--api-url',
    default='http://127.0.0.1:8000',
    help='Base URL of the yProv API server.',
    envvar='YPROV_API_URL'  # Allows setting via environment variable
)
@click.pass_context
def cli(ctx, api_url):
    """
    yProv CLI: A command-line tool for the yProv Provenance Service.

    You can set the API URL using the --api-url option or by setting
    the YPROV_API_URL environment variable.
    """
    # Ensure the context object exists and store the API URL
    ctx.ensure_object(dict)
    ctx.obj['API_URL'] = api_url


@cli.command()
@click.pass_context
def check(ctx):
    """Verify if the yProv server is reachable."""
    api_url = ctx.obj['API_URL']
    console.print(f"Pinging server at [cyan]{api_url}[/cyan]...")

    try:
        # Make a simple request to the root endpoint with a timeout
        response = make_request("GET", api_url, "/status", timeout=5)
        if response is None:
            console.print("❌ [bold red]Server is unreachable or did not respond as expected.[/bold red]")
            return
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        try:
            data = response.json()
            if data.get("status") != "ok":
                console.print(f"❌ [bold red]Server is reachable but returned an unexpected status: {data.get('status')}.[/bold red]")
                return
        except json.JSONDecodeError:
            console.print("❌ [bold red]Server is reachable but did not return valid JSON.[/bold red]")
            return
        console.print("✅ [bold green]Server is reachable and responding.[/bold green]")
    except requests.exceptions.RequestException as e:
        console.print("❌ [bold red]Server is unreachable.[/bold red]")
        console.print(f"   Error: {e}")


# Add command groups to the main CLI
cli.add_command(auth)
cli.add_command(documents)
cli.add_command(pids)
cli.add_command(blockchain)
cli.add_command(artifacts)


if __name__ == '__main__':
    cli()
