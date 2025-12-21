import os
import json
import requests
from appdirs import user_data_dir
from pathlib import Path
from rich.console import Console


console = Console()


# Path to store the authentication token and local storage
config_path = Path(user_data_dir("yProvStore"))
config_path.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = config_path / "token.txt"
LOCAL_STORAGE_FILE = config_path / "local_storage.json"


def save_token(token: str):
    """Saves the JWT token to a file in the user's home directory."""
    try:
        TOKEN_FILE.write_text(token)
        console.print("🔑 [bold green]Authentication token saved successfully.[/bold green]")
    except IOError as e:
        console.print(f"[bold red]Error saving token:[/bold red] {e}")


def load_token() -> str | None:
    """Loads the JWT token from the file."""
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None


def clear_token():
    """Removes the saved token file for logout."""
    if TOKEN_FILE.exists():
        os.remove(TOKEN_FILE)
        console.print("✅ [bold]Successfully logged out.[/bold]")


def make_request(method: str, api_url: str, endpoint: str, **kwargs):
    """
    A centralized function to make API requests.
    It automatically adds the auth token if available.
    """
    token = load_token()
    headers = kwargs.pop("headers", {})

    # Add authentication header if a token exists
    if token:
        headers["Authorization"] = f"Bearer {token}"

    full_url = f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}"

    try:
        response = requests.request(method, full_url, headers=headers, **kwargs)

        # Check for HTTP errors and print informative messages
        if not response.ok:
            error_details = response.json() if response.headers.get("Content-Type") == "application/json" else response.text
            console.print(f"[bold red]Error {response.status_code}:[/bold red]", error_details)
            return None

        return response

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]API request failed:[/bold red] {e}")
        return None


def store_dict(key: str, data: dict):
    """Stores a dictionary under a specific key in the local storage file."""
    storage = {}
    if LOCAL_STORAGE_FILE.exists():
        try:
            storage = json.loads(LOCAL_STORAGE_FILE.read_text())
        except Exception:
            storage = {}
    storage[key] = data
    try:
        LOCAL_STORAGE_FILE.write_text(json.dumps(storage, indent=2))
        console.print(f"💾 [bold green]Data stored for key '{key}'.[/bold green]")
    except IOError as e:
        console.print(f"[bold red]Error storing data:[/bold red] {e}")


def load_dict(key: str) -> dict | None:
    """Retrieves a dictionary for a specific key from the local storage file."""
    if not LOCAL_STORAGE_FILE.exists():
        return None
    try:
        storage = json.loads(LOCAL_STORAGE_FILE.read_text())
        return storage.get(key)
    except Exception as e:
        console.print(f"[bold red]Error retrieving data:[/bold red] {e}")
        return None
