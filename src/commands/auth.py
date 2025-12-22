import click
import json
from rich.console import Console
from utils.api_client import make_request, save_token, clear_token

console = Console()


def get_credentials(email, password, file):
    """
    Helper function to determine credentials from provided options.
    - Prioritizes file if provided.
    - Then checks for email/password flags.
    - Returns None if no options are given, to trigger interactive prompts.
    """
    # Check for mutually exclusive options
    if file and (email or password):
        raise click.UsageError("Cannot use --file with --email or --password.")

    if file:
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise click.BadParameter(f"Could not read or parse JSON file: {e}")

    if email and password:
        return {"email": email, "password": password}

    # If only one of email/password is provided, it's an error
    if email or password:
        raise click.UsageError("Both --email and --password must be provided together.")

    return None  # No options provided, will trigger interactive mode


@click.group()
def auth():
    """Manages user authentication."""
    pass


@auth.command()
@click.option('--email', help="User's email address.")
@click.option('--password', help="User's password.")
@click.option('--file', type=click.Path(exists=True, dir_okay=False, readable=True), help="Path to a JSON file with credentials.")
@click.pass_context
def login(ctx, email, password, file):
    """Log in with flags, a file, or interactively."""
    api_url = ctx.obj['API_URL']

    # Get credentials from options or set to None for interactive mode
    data = get_credentials(email, password, file)

    # If no credentials were passed via options, prompt interactively
    if data is None:
        email_prompt = click.prompt("User's email address")
        password_prompt = click.prompt("User's password", hide_input=True)
        data = {"email": email_prompt, "password": password_prompt}

    console.print(f"Attempting to log in as [cyan]{data['email']}[/cyan]...")
    response = make_request("POST", api_url, "/auth/login", json=data)

    if response and response.status_code == 200:
        token_data = response.json()
        save_token(token_data["access_token"])
    else:
        console.print("[bold red]Login failed.[/bold red]")


@auth.command()
@click.option('--email', help="Your desired email address.")
@click.option('--password', help="Your desired password.")
@click.option('--file', type=click.Path(exists=True, dir_okay=False, readable=True), help="Path to a JSON file with credentials.")
@click.pass_context
def signup(ctx, email, password, file):
    """Sign up with flags, a file, or interactively."""
    api_url = ctx.obj['API_URL']

    data = get_credentials(email, password, file)

    # Interactive mode if no options are provided
    if data is None:
        email_prompt = click.prompt("Your desired email address")
        password_prompt = click.prompt("Your desired password", hide_input=True, confirmation_prompt=True)
        data = {"email": email_prompt, "password": password_prompt}

    response = make_request("POST", api_url, "/auth/signup", json=data)

    if response and response.status_code == 201:
        console.print("✅ [bold green]User registration successful! You can now log in.[/bold green]")


@auth.command()
@click.pass_context
def verify(ctx):
    """Verify the current session token."""
    api_url = ctx.obj['API_URL']
    response = make_request("POST", api_url, "/auth/verify")

    if response and response.status_code == 200:
        user_data = response.json()
        console.print(f"✅ [bold green]Token is valid.[/bold green] Logged in as: [cyan]{user_data['email']}[/cyan]")


@auth.command()
def logout():
    """Log out by deleting the local token."""
    clear_token()
