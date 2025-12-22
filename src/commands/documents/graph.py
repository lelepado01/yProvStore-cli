import os
import click
import json

from rich.console import Console
from rich.table import Table

from utils.api_client import make_request


console = Console()


@click.group(name="graph")
def graph():
    """
    Manage graph operations on provenance documents.

    You must pass a fully-qualified PID (prefix/id).
    """
    pass


@graph.command(name="list")
@click.argument("pid")
@click.option("--entity-types", "-t", multiple=True, help="Filter by entity types (e.g., entity, agent, wasDerivedFrom).")
@click.option("--entity-ids", "-e", multiple=True, help="Filter by entity IDs.")
@click.option("--in-json", "-j", is_flag=True, help="Output the results in JSON format (all data is written).")
@click.option("--display-data", "-d", is_flag=True, help="Display the data field in the output console.")
@click.option("--output", "-o", type=click.Path(), help="Output file path to save the results (all data is written).")
@click.option("--is-element", "-ie", is_flag=True, help="Filter by whether the entity is an element.")
@click.option("--is-relation", "-ir", is_flag=True, help="Filter by whether the entity is a relation.")
@click.pass_context
def list_elements(ctx, pid, entity_types, entity_ids, in_json, display_data, output, is_element, is_relation):
    """
    List elements in a provenance document graph.

    PID should be in the format prefix/id.
    """
    api_url = ctx.obj['API_URL']

    if pid.count("/") != 1:
        console.print("[red]Error: PID must be in the format prefix/id.[/red]")
        return

    response = make_request(
        method="GET",
        api_url=api_url,
        endpoint=f"/documents/{pid}/graph/list",
        params={
            "entity_types": list(entity_types) if entity_types else None,
            "entity_ids": list(entity_ids) if entity_ids else None,
            "is_element": is_element,
            "is_relation": is_relation
        }
    )
    if not response:
        console.print("[red]❌ Failed to perform the list operation.[/red]")
        return

    data = response.json()
    if output:
        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, 'w') as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Results saved to {output}[/green]")
        return
    if in_json:
        console.print(json.dumps(data, indent=2))
        return
    table = Table(title="Provenance Document Graph Elements")

    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Group", style="green")
    table.add_column("Is Element", style="yellow")
    table.add_column("Is Relation", style="blue")
    if display_data:
        table.add_column("Data", style="white")
    
    for element in data.get("elements", []):
        row = [
            element["id"],
            element["type"],
            element["group"],
            str(element["is_element"]),
            str(element["is_relation"])
        ]
        if display_data:
            row.append(
                json.dumps(element["data"], indent=2)
            )
        table.add_row(*row)

    console.print(table)
    if data.get("warnings"):
        console.print("[yellow]Warnings:[/yellow]")
        for warning in data["warnings"]:
            console.print(f"- {warning}")
    else:
        console.print("[green]No warnings encountered.[/green]")
    console.print(f"[blue]Total elements found: {len(data.get('elements', []))}[/blue]")


@graph.command(name="subgraph")
@click.argument("pid")
@click.option(
    "--entity-id", "-e", "entity_ids", 
    multiple=True, 
    required=True, 
    help="[Required] Entity ID to start the subgraph from. Can be used multiple times."
)
@click.option(
    "--direction", "-d",
    type=click.Choice(['both', 'forward', 'backward'], case_sensitive=False),
    default='both',
    show_default=True,
    help="Direction of the subgraph traversal."
)
@click.option("--output", "-o", type=click.Path(), help="Output file path to save the resulting PROV-JSON subgraph.")
@click.pass_context
def subgraph(ctx, pid, entity_ids, direction, output):
    """
    Extract a subgraph from a provenance document.

    This command starts a traversal from one or more given entity IDs and
    returns a new, self-contained PROV-JSON document representing the
    subgraph.
    """
    api_url = ctx.obj['API_URL']

    if pid.count("/") != 1:
        console.print("[red]Error: PID must be in the format prefix/id.[/red]")
        return
    
    prefix, pid_part = pid.split("/", 1)

    response = make_request(
        method="GET",
        api_url=api_url,
        endpoint=f"/documents/{pid}/graph/subgraph",
        params={
            "prefix": prefix,
            "pid": pid_part,
            "entity_ids": list(entity_ids),
            "direction": direction,
        }
    )
    if not response:
        console.print("[red]❌ Failed to perform the subgraph operation.[/red]")
        return

    data = response.json()
    subgraph_data = data.get("subgraph", {})
    warnings = data.get("warnings", [])

    if output:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save the subgraph data to the specified file
        with open(output, 'w') as f:
            json.dump(subgraph_data, f, indent=2)
        console.print(f"[green]Subgraph saved to {output}[/green]")
    else:
        # Print the subgraph data to the console
        if len(json.dumps(subgraph_data)) > 10000:  # 10000 bytes threshold
            # If the subgraph is too large, save it to a file instead
            pid = pid.replace("/", "_")
            warning_msg = f"[yellow]Subgraph too large to display. Saved to subgraph_{pid}.json instead.[/yellow]"
            with open(f"subgraph_{pid}.json", 'w') as f:
                json.dump(subgraph_data, f, indent=2)
            console.print(warning_msg)
        else:
            console.print(json.dumps(data, indent=2))

    # Always print any warnings to the console for visibility
    if warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"- {warning}")
