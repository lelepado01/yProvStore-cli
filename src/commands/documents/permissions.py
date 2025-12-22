import click
from rich.console import Console
from rich.table import Table
from utils.api_client import make_request


console = Console()


@click.group(name="permissions")
def permissions():
    """
    Manage read/write permissions on documents.

    Permissions are always stored on the *first-version* of a document.
    Listing or adding on any version will target that original version.
    You must pass a fully-qualified PID (prefix/id).
    """
    pass


@permissions.command(name="add")
@click.argument("pid")
@click.option("--user-email", required=True, help="Email of the user to grant permission to.")
@click.option(
    "--permission-level",
    type=click.Choice(["write", "read"], case_sensitive=False),
    required=True,
    help="Permission level to grant. Note: 'read' may error if docs are public."
)
@click.pass_context
def add_permission(ctx, pid, user_email, permission_level):
    """
    Add a permission for USER_EMAIL on PID.

    Note:
    - Permissions are stored on the first version of the document.
    - The document must exist on this server instance.
    """
    api_url = ctx.obj["API_URL"]

    params = {"pid": pid}
    body = {"user_email": user_email, "permission_level": permission_level.lower()}

    response = make_request("POST", api_url, "/documents/permissions", params=params, json=body)
    if not response:
        console.print("[red]❌ Failed to add permission[/red]")
        return

    if response.status_code == 200 or response.status_code == 201:
        console.print("✅ [bold green]Permission added![/bold green]")
        console.print_json(data=response.json())
    else:
        console.print(f"❌ [bold red]Error {response.status_code}:[/bold red] {response.text}")


@permissions.command(name="list")
@click.argument("pid")
@click.pass_context
def list_permissions(ctx, pid):
    """
    List all permissions set on PID.
    Permissions for documents are always stored on the first version of the document.

    PID may be 'prefix/id' or just 'id' (uses default prefix).
    """
    api_url = ctx.obj["API_URL"]

    endpoint = f"/documents/{pid}/permissions"

    response = make_request("GET", api_url, endpoint)
    if not response:
        console.print("[red]❌ Failed to list permissions[/red]")
        return

    if response.status_code == 200:
        perms = response.json()
        if not perms:
            console.print("[yellow]No permissions set on this document.[/yellow]")
            return

        table = Table(title=f"Permissions for {pid}")
        table.add_column("User Email", style="magenta")
        table.add_column("Level", style="cyan")
        table.add_column("PID", style="green")
        for p in perms:
            table.add_row(p["user_email"], p["permission_level"], p.get("pid", "N/A"))
        console.print(table)
    else:
        console.print(f"❌ [bold red]Error {response.status_code}:[/bold red] {response.text}")


@permissions.command(name="delete")
@click.argument("pid")
@click.option("--user-email", required=True, help="Email of the user to revoke permission from.")
@click.pass_context
def delete_permission(ctx, pid, user_email):
    """
    Delete a permission for USER_EMAIL on PID.

    Note:
    - Permissions are stored on the first version of the document.
    - The document must exist on this server instance.
    """
    api_url = ctx.obj["API_URL"]

    params = {"pid": pid}
    body = {"user_email": user_email}

    endpoint = f"/documents/{pid}/permissions"

    response = make_request("DELETE", api_url, endpoint, params=params, json=body)
    if not response:
        console.print("[red]❌ Failed to delete permission[/red]")
        return

    if response.status_code == 200:
        console.print("✅ [bold green]Permission deleted![/bold green]")
        console.print_json(data=response.json())
    else:
        console.print(f"❌ [bold red]Error {response.status_code}:[/bold red] {response.text}")
