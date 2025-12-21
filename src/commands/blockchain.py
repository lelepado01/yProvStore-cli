import os
import click
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from utils.blockchain.fabric import FabricConnector, BlockchainDocument

console = Console()


@click.group()
def blockchain():
    """Manage blockchain operations for document provenance."""
    pass


@blockchain.command(name="create")
@click.option('--pid', required=True, help="Unique identifier for the document.")
@click.option('--url', required=True, help="URL where the document can be accessed.")
@click.option('--hash', required=True, help="Hash of the document content.")
@click.option('--owners', required=True, help="Comma-separated list of document owners.")
@click.option('--timestamp', help="Document timestamp (ISO-8601 format). Defaults to current time.")
@click.option('--file', type=click.Path(exists=True, dir_okay=False, readable=True), 
              help="Path to a JSON file with document data.")
def create_document(pid, url, hash, owners, timestamp, file):
    """Create a new document on the blockchain."""
    
    # Handle file input vs command line arguments
    if file:
        if any([pid, url, hash, owners, timestamp]):
            raise click.UsageError("Cannot use --file with other document options.")
        
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            # Validate required fields in JSON
            required_fields = ['pid', 'url', 'hash', 'owners']
            missing = [field for field in required_fields if field not in data]
            if missing:
                raise click.BadParameter(f"Missing required fields in JSON file: {', '.join(missing)}")
            
            pid = data['pid']
            url = data['url']
            hash = data['hash']
            owners = data['owners']
            timestamp = data.get('timestamp')
            
        except (json.JSONDecodeError, IOError) as e:
            raise click.BadParameter(f"Could not read or parse JSON file: {e}")
    
    # Set default timestamp if not provided
    if not timestamp:
        timestamp = datetime.now().isoformat()
    
    # Parse owners list
    if isinstance(owners, str):
        owners_list = [owner.strip() for owner in owners.split(',') if owner.strip()]
    else:
        owners_list = owners
    
    try:
        # Create BlockchainDocument instance
        document = BlockchainDocument(
            pid=pid,
            url=url,
            hash=hash,
            timestamp=timestamp,
            owners=owners_list
        )
        
        console.print(f"Creating document with PID: [cyan]{pid}[/cyan]...")
        
        # Connect to blockchain and create document
        connector = FabricConnector()
        result = connector.create_document(document)
        
        if result.get('ok'):
            console.print("✅ [bold green]Document created successfully on blockchain![/bold green]")

            console.print(f"Transaction response: \n{result}\n")

            # TODO: check what fields are actually returned in result
            
            # Display result details
            table = Table(title="Document Details")
            table.add_column("Field", style="bold")
            table.add_column("Value")
            
            table.add_row("PID", result.get('pid', pid))
            table.add_row("Transaction ID", result.get('txId', 'N/A'))
            table.add_row("Status", "Created")
            
            console.print(table)
        else:
            console.print("❌ [bold red]Failed to create document on blockchain.[/bold red]")
            if result.get('error'):
                console.print(f"Error: {result['error']}")
    
    except Exception as e:
        console.print("❌ [bold red]Error creating document:[/bold red]")
        console.print(f"   {str(e)}")


@blockchain.command(name="read")
@click.argument('pid')
def read_document(pid):
    """Read a document from the blockchain by its PID."""
    
    try:
        console.print(f"Reading document with PID: [cyan]{pid}[/cyan]...")
        
        connector = FabricConnector()
        result = connector.read_document(pid)
        
        if result.get('ok'):
            document_data = result.get('data')
            
            if document_data:
                console.print("✅ [bold green]Document found![/bold green]")
                
                # Display document in a formatted table
                table = Table(title=f"Document: {pid}")
                table.add_column("Field", style="bold")
                table.add_column("Value")
                
                table.add_row("PID", document_data.get('pid', 'N/A'))
                table.add_row("URL", document_data.get('url', 'N/A'))
                table.add_row("Hash", document_data.get('hash', 'N/A'))
                table.add_row("Timestamp", document_data.get('timestamp', 'N/A'))
                table.add_row("Owners", ', '.join(document_data.get('owners', [])))
                
                console.print(table)
                
                # Option to show raw JSON
                if console.input("\n[dim]Show raw JSON? (y/N): [/dim]").lower() == 'y':
                    console.print(JSON(json.dumps(document_data, indent=2)))
            else:
                console.print("❌ [bold red]Document not found.[/bold red]")
        else:
            console.print("❌ [bold red]Failed to read document from blockchain.[/bold red]")
            if result.get('error'):
                console.print(f"Error: {result['error']}")
    
    except Exception as e:
        console.print("❌ [bold red]Error reading document:[/bold red]")
        console.print(f"   {str(e)}")


@blockchain.command(name="list")
@click.option('--start-time', required=True, help="Start time for the query (ISO-8601 format or timestamp).")
@click.option('--end-time', required=True, help="End time for the query (ISO-8601 format or timestamp).")
@click.option('--format', 'output_format', default='table', 
              type=click.Choice(['table', 'json']), help="Output format.")
def list_documents(start_time, end_time, output_format):
    """List documents created within a specific time interval."""
    
    try:
        console.print(f"Querying documents from [cyan]{start_time}[/cyan] to [cyan]{end_time}[/cyan]...")
        
        connector = FabricConnector()
        result = connector.get_documents_by_interval(start_time, end_time)
        
        if result.get('ok'):
            documents = result.get('documents', [])
            
            if documents:
                console.print(f"✅ [bold green]Found {len(documents)} document(s)![/bold green]")
                
                if output_format == 'table':
                    # Display documents in a table
                    table = Table(title=f"Documents ({start_time} to {end_time})")
                    table.add_column("PID", style="bold")
                    table.add_column("URL")
                    table.add_column("Hash")
                    table.add_column("Timestamp")
                    table.add_column("Owners")
                    
                    for doc in documents:
                        table.add_row(
                            doc.get('pid', 'N/A'),
                            doc.get('url', 'N/A')[:50] + ('...' if len(doc.get('url', '')) > 50 else ''),
                            doc.get('hash', 'N/A')[:20] + ('...' if len(doc.get('hash', '')) > 20 else ''),
                            doc.get('timestamp', 'N/A'),
                            ', '.join(doc.get('owners', []))[:30] + ('...' if len(', '.join(doc.get('owners', []))) > 30 else '')
                        )
                    
                    console.print(table)
                
                elif output_format == 'json':
                    console.print(JSON(json.dumps(documents, indent=2)))
            else:
                console.print("ℹ️  [dim]No documents found in the specified time interval.[/dim]")
        else:
            console.print("❌ [bold red]Failed to query documents from blockchain.[/bold red]")
            if result.get('error'):
                console.print(f"Error: {result['error']}")
    
    except Exception as e:
        console.print("❌ [bold red]Error querying documents:[/bold red]")
        console.print(f"   {str(e)}")


@blockchain.command(name="test")
def test_connection():
    """
    Test the blockchain connection.

    !! This command will create a test document on the blockchain and then attempt to read it back.
    """
    
    console.print("Testing blockchain connection...")
    
    try:
        connector = FabricConnector()
        
        # Create a test document
        test_doc = BlockchainDocument(
            pid=f"TEST_PID_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            url="https://example.com/test-resource",
            hash="test_hash_" + datetime.now().strftime('%Y%m%d%H%M%S'),
            timestamp=str(int(datetime.now().timestamp() * 1000)),  # current time in ms
            owners=["test_owner"]
        )
        
        console.print("Creating test document...")
        create_result = connector.create_document(test_doc)

        console.print("✅ [green]Document creation: SUCCESS[/green]")
        console.print(f"[blue]{create_result}[/blue]\n")
        
        # Try to read the created document
        console.print("Reading test document...")
        read_result = connector.read_document(test_doc.pid)
        
        console.print("✅ [green]Document reading: SUCCESS[/green]")
        console.print(f"[blue]{read_result}[/blue]\n")

        # Try interval query
        console.print("Testing interval query...")
        start_time = str(int(datetime.now().timestamp() * 1000) - 60000)  # 1 minute ago
        end_time = str(int(datetime.now().timestamp() * 1000) + 60000)   # 1 minute from now
        
        interval_result = connector.get_documents_by_interval(start_time, end_time)
        console.print("✅ [green]Interval query: SUCCESS[/green]")
        console.print(f"[blue]{interval_result}[/blue]\n")
        
        console.print("\n✅ [bold green]Blockchain connection test completed successfully![/bold green]")
    
    except Exception as e:
        console.print("\n❌ [bold red]Blockchain connection test failed:[/bold red]")
        console.print(f"   {str(e)}")
        console.print("\n[dim]Make sure all required environment variables are set:[/dim]")
        console.print(f"[dim]- CONNECTOR_USR_PKEY_PATH={os.getenv('CONNECTOR_USR_PKEY_PATH')}[/dim]")
        console.print(f"[dim]- CONNECTOR_USR_CERT_PATH={os.getenv('CONNECTOR_USR_CERT_PATH')}[/dim]")
        console.print(f"[dim]- CONNECTOR_PEER_TLSCERT_PATH={os.getenv('CONNECTOR_PEER_TLSCERT_PATH')}[/dim]")
        console.print(f"[dim]- CONNECTOR_PEER_ENDPOINT={os.getenv('CONNECTOR_PEER_ENDPOINT')}[/dim]")
        console.print(f"[dim]- CONNECTOR_PEER_HOSTNAME={os.getenv('CONNECTOR_PEER_HOSTNAME')}[/dim]")
        console.print(f"[dim]- CONNECTOR_PEER_MSP_ID={os.getenv('CONNECTOR_PEER_MSP_ID')}[/dim]")
