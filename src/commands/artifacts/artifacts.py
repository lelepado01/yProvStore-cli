import os
import hashlib
import click
from rich.console import Console
from rich.table import Table

from utils.api_client import make_request


console = Console()


@click.group()
def artifacts():
    """Upload, download, and manage artifact files."""
    pass


@artifacts.command(name="list")
@click.option('--page', default=0, show_default=True, type=int, help="Page number (zero-indexed).")
@click.option('--page-size', default=10, show_default=True, type=int, help="Number of artifacts per page.")
@click.option('--updated-after', type=str, help="List only artifacts updated after this ISO 8601 datetime (e.g., '2024-06-01T00:00:00Z').")
@click.option('--created-after', type=str, help="List only artifacts created after this ISO 8601 datetime (e.g., '2024-06-01T00:00:00Z').")
@click.option('--pid', type=str, help="Filter by a specific artifact PID.")
@click.pass_context
def list_artifacts(ctx, page, page_size, updated_after, created_after, pid):
    """List all available artifact records, with pagination and optional filters."""
    api_url = ctx.obj['API_URL']
    params = {'page': page, 'page_size': page_size}
    if updated_after:
        params['updated_after'] = updated_after
    if created_after:
        params['created_after'] = created_after
    if pid:
        params['pid'] = pid
    
    response = make_request("GET", api_url, "/artifacts", params=params)

    if response and response.status_code == 200:
        artifact_list = response.json()
        if not artifact_list:
            console.print("[yellow]No artifacts found.[/yellow]")
            return

        table = Table(title=f"Available Artifacts (Page {page}, Size {page_size})")
        table.add_column("PID", style="cyan", no_wrap=True)
        table.add_column("Filename", style="blue")
        table.add_column("Owner", style="green")
        table.add_column("Hash (SHA-256)", style="magenta")

        for artifact in artifact_list:
            hash_display = artifact.get('hash', 'N/A') or 'N/A'
            # Truncate long hashes for display
            if hash_display != 'N/A' and len(hash_display) > 16:
                hash_display = hash_display[:16] + "..."
            table.add_row(
                artifact['pid'],
                artifact.get('filename', 'N/A'),
                artifact.get('owner_email', 'Unknown'),
                hash_display
            )

        console.print(table)
    else:
        console.print(f"❌ [bold red]Error[/bold red] {response.status_code if response else ''}: {response.text if response else 'No response.'}")


@artifacts.command(name="upload")
@click.argument('file_path', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('--filename', type=str, help="Custom filename to use for the artifact. Defaults to the original filename.")
@click.pass_context
def upload_artifact(ctx, file_path, filename):
    """Upload an artifact file and receive a PID for it.
    
    FILE_PATH is the path to the file to upload.
    
    This command uses a two-step process:
    1. Request an upload URL and PID from the server
    2. Upload the file to the presigned URL
    
    Example:

        yprov artifacts upload ./my_artifact.tar.gz

        yprov artifacts upload ./data.csv --filename "experiment_data.csv"
    """
    api_url = ctx.obj['API_URL']
    
    # Determine filename
    artifact_filename = filename or os.path.basename(file_path)
    
    console.print(f"📤 Uploading artifact [cyan]{artifact_filename}[/cyan]...")
    
    # Step 1: Get upload URL
    console.print("[dim]Step 1/2: Requesting upload URL...[/dim]")
    params = {'filename': artifact_filename}
    response = make_request("POST", api_url, "/artifacts/upload/url", params=params)
    
    if not response or response.status_code != 200:
        console.print(f"❌ [bold red]Error[/bold red]: Failed to get upload URL.")
        if response:
            console.print(f"   {response.text}")
        return
    
    upload_info = response.json()
    artifact_pid = upload_info.get('pid')
    upload_url = upload_info.get('upload_url')
    expires_at = upload_info.get('url_expires_at')
    
    if not artifact_pid or not upload_url:
        console.print("❌ [bold red]Error[/bold red]: Invalid response from server (missing pid or upload_url).")
        return
    
    console.print(f"   PID assigned: [cyan]{artifact_pid}[/cyan]")
    if expires_at:
        console.print(f"   URL expires at: [yellow]{expires_at}[/yellow]")
    
    # Step 2: Upload file to presigned URL
    console.print("[dim]Step 2/2: Uploading file...[/dim]")
    
    try:
        file_size = os.path.getsize(file_path)
        console.print(f"   File size: {file_size:,} bytes")
        
        with open(file_path, 'rb') as f:
            files = {'document_file': (artifact_filename, f, 'application/octet-stream')}
            # The upload URL is a full URL (proxy or direct), so we make a direct request
            import requests
            from utils.api_client import load_token
            
            headers = {}
            token = load_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            upload_response = requests.put(upload_url, files=files, headers=headers)
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                console.print("✅ [bold green]Artifact uploaded successfully![/bold green]")
                console.print(f"   PID: [cyan]{result.get('pid', artifact_pid)}[/cyan]")
                if result.get('hash'):
                    console.print(f"   SHA-256: [magenta]{result.get('hash')}[/magenta]")
            else:
                console.print(f"❌ [bold red]Error[/bold red]: Upload failed ({upload_response.status_code}).")
                try:
                    error_detail = upload_response.json()
                    console.print(f"   {error_detail}")
                except Exception:
                    console.print(f"   {upload_response.text}")
    except IOError as e:
        console.print(f"❌ [bold red]Error[/bold red]: Cannot read file '{file_path}': {e}")
        return
    except Exception as e:
        console.print(f"❌ [bold red]Error[/bold red]: Upload failed: {e}")
        return


@artifacts.command(name="download")
@click.argument('pid')
@click.option(
    '-o', '--output',
    type=click.Path(dir_okay=False, writable=True),
    help="Full path to save the file (e.g., 'my_dir/artifact.bin'). This overrides --output-folder."
)
@click.option(
    '--output-folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help="Folder to save the file in. The filename will be determined from the server response."
)
@click.option(
    '--verify/--no-verify',
    default=False,
    help="Verify SHA-256 hash of the downloaded file against the server-reported hash."
)
@click.pass_context
def download_artifact(ctx, pid, output, output_folder, verify):
    """Download an artifact file by its PID.
    
    PID is the unique identifier of the artifact to download.
    
    This command uses a two-step process:
    1. Request a download URL from the server
    2. Download the file from the presigned URL
    
    Example:

        yprov artifacts download 21.T11961/abc123

        yprov artifacts download abc123 -o ./downloaded_artifact.tar.gz

        yprov artifacts download abc123 --output-folder ./downloads --verify
    """
    api_url = ctx.obj['API_URL']
    
    console.print(f"📥 Downloading artifact [cyan]{pid}[/cyan]...")
    
    # Step 1: Get download URL
    console.print("[dim]Step 1/2: Requesting download URL...[/dim]")
    
    # Determine the endpoint path based on PID format
    if '/' in pid:
        endpoint = f"/artifacts/{pid}/download/url"
    else:
        endpoint = f"/artifacts/{pid}/download/url"
    
    response = make_request("GET", api_url, endpoint)
    
    if not response or response.status_code != 200:
        console.print(f"❌ [bold red]Error[/bold red]: Failed to get download URL.")
        if response:
            console.print(f"   {response.text}")
        return
    
    download_info = response.json()
    download_url = download_info.get('download_url')
    filename = download_info.get('filename', f"{pid.replace('/', '_')}.bin")
    server_hash = download_info.get('hash')
    expires_at = download_info.get('url_expires_at')
    
    if not download_url:
        console.print("❌ [bold red]Error[/bold red]: Invalid response from server (missing download_url).")
        return
    
    console.print(f"   Filename: [cyan]{filename}[/cyan]")
    if expires_at:
        console.print(f"   URL expires at: [yellow]{expires_at}[/yellow]")
    if server_hash:
        console.print(f"   Expected SHA-256: [magenta]{server_hash[:16]}...[/magenta]")
    
    # Determine output path
    if output:
        output_path = output
        output_dir = os.path.dirname(output_path) or os.getcwd()
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    else:
        base_folder = output_folder or os.getcwd()
        # Handle PID with prefix
        split = pid.split('/')
        if len(split) == 2:
            prefix, artifact_id = split
            prefix_path = os.path.join(base_folder, prefix)
            os.makedirs(prefix_path, exist_ok=True)
            output_path = os.path.join(prefix_path, filename)
        else:
            output_path = os.path.join(base_folder, filename)
    
    # Step 2: Download file from presigned URL
    console.print(f"[dim]Step 2/2: Downloading file to [yellow]{output_path}[/yellow]...[/dim]")
    
    try:
        import requests
        from utils.api_client import load_token
        
        headers = {}
        token = load_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        download_response = requests.get(download_url, headers=headers, stream=True)
        
        if download_response.status_code != 200:
            console.print(f"❌ [bold red]Error[/bold red]: Download failed ({download_response.status_code}).")
            try:
                error_detail = download_response.json()
                console.print(f"   {error_detail}")
            except Exception:
                console.print(f"   {download_response.text}")
            return
        
        # Stream download to file
        total_size = 0
        hash_obj = hashlib.sha256() if verify else None
        
        with open(output_path, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
                    if hash_obj:
                        hash_obj.update(chunk)
        
        console.print(f"✅ [bold green]Download complete![/bold green] ({total_size:,} bytes)")
        console.print(f"   File saved to: [yellow]{output_path}[/yellow]")
        
        # Verify hash if requested
        if verify:
            local_hash = hash_obj.hexdigest()
            console.print(f"\n🔎 Verifying file integrity...")
            console.print(f"   Local SHA-256:  [magenta]{local_hash}[/magenta]")
            
            if server_hash:
                console.print(f"   Server SHA-256: [magenta]{server_hash}[/magenta]")
                if local_hash == server_hash:
                    console.print("   ✅ [bold green]Hash verification passed![/bold green]")
                else:
                    console.print("   ❌ [bold red]Hash verification FAILED![/bold red]")
                    console.print("   [yellow]The downloaded file may be corrupted or tampered with.[/yellow]")
            else:
                console.print("   [yellow]⚠️ Server did not provide a hash for verification.[/yellow]")
    
    except IOError as e:
        console.print(f"❌ [bold red]Error[/bold red]: Cannot write to file '{output_path}': {e}")
        return
    except Exception as e:
        console.print(f"❌ [bold red]Error[/bold red]: Download failed: {e}")
        return


@artifacts.command(name="get")
@click.argument('pid')
@click.pass_context
def get_artifact_info(ctx, pid):
    """Get information about an artifact by its PID.
    
    PID is the unique identifier of the artifact.
    
    Example:
        yprov artifacts get 21.T11961/abc123
        yprov artifacts get abc123
    """
    api_url = ctx.obj['API_URL']
    
    console.print(f"🔍 Fetching artifact info for [cyan]{pid}[/cyan]...")
    
    # Use the list endpoint with pid filter to get artifact info
    params = {'pid': pid}
    response = make_request("GET", api_url, "/artifacts", params=params)
    
    if not response or response.status_code != 200:
        console.print(f"❌ [bold red]Error[/bold red]: Failed to get artifact info.")
        if response:
            console.print(f"   {response.text}")
        return
    
    artifact_list = response.json()
    
    if not artifact_list:
        console.print(f"[yellow]Artifact with PID '{pid}' not found.[/yellow]")
        return
    
    artifact = artifact_list[0]
    
    # Display artifact info in a nice table
    table = Table(title=f"Artifact: {pid}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("PID", artifact.get('pid', 'N/A'))
    table.add_row("Owner", artifact.get('owner_email', 'Unknown'))
    table.add_row("Storage URL", artifact.get('storage_url', 'N/A'))
    table.add_row("SHA-256 Hash", artifact.get('hash', 'N/A') or 'N/A')
    
    console.print(table)
