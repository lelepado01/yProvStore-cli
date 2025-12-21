import click
from rich.console import Console
from rich.table import Table
from utils.api_client import make_request, store_dict, load_dict


console = Console()


def local_metadata_schema(api_url: str, refresh: bool = False) -> dict | None:
    """
    Returns the locally stored metadata schema for documents.
    If it does not exist, it fetches it from the API.
    """
    schema = load_dict("metadata_schema")
    if schema and not refresh:
        return schema

    response = make_request("GET", api_url, "/metadata/schema")
    if response and response.status_code == 200:
        store_dict("metadata_schema", response.json())
        return response.json()

    console.print(f"[red]❌ Error fetching metadata schema:[/red] {response.text if response else 'No response from server.'}")
    return None


@click.group(name="metadata")
def metadata():
    """
    Manage metadata for documents.
    Metadata can include additional information about the document,
    such as title, description, and keywords attributes.
    
    You must pass a fully-qualified PID (prefix/id).
    """
    pass


@metadata.command(name="get")
@click.argument('pid')
@click.pass_context
def get_metadata(ctx, pid):
    """Get metadata for a specific document by its PID."""
    api_url = ctx.obj['API_URL']
    response = make_request("GET", api_url, f"/documents/{pid}/metadata")

    if response and response.status_code == 200:
        console.print_json(data=response.json())
    else:
        console.print(f"[red]❌ Error fetching metadata for PID {pid}:[/red] {response.text if response else 'No response from server.'}")


@metadata.command(name="schema")
@click.option("--refresh-schema", is_flag=True, help="Force re-download of metadata schema")
@click.pass_context
def get_metadata_schema(ctx, refresh_schema):
    """Get the metadata schema for documents."""
    api_url = ctx.obj['API_URL']
    schema = local_metadata_schema(api_url, refresh=refresh_schema)

    if schema:
        table = Table(title="Document Metadata Schema")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Required", style="yellow")
        table.add_column("Example", style="green")

        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        for field, info in properties.items():
            required = "No"
            field_type = info.get("type", "")
            if not field_type:
                any_of = info.get("anyOf", [])
                if any_of:
                    for t in any_of:
                        t_type = t.get("type")
                        if t_type:
                            if t_type == "null":
                                required = "No"
                                continue
                            if field_type:
                                field_type += " | "
                            if t_type == "array":
                                sub_type = t.get("items", {}).get("type")
                                if sub_type:
                                    field_type += r"list\[" + sub_type + "]"
                                else:
                                    field_type += t_type
                            else:
                                field_type += t_type
            else:
                required = "Yes" if field in required_fields else "No"
            field_type = field_type if field_type else "unknown"
            example = info.get("example", "")
            table.add_row(field, field_type, required, str(example))

        console.print(table)


def _get_field_type(props_key: dict) -> str:
    """Extract the expected type from a schema property definition."""
    expected = props_key.get("type")
    if not expected and props_key.get("anyOf"):
        for item in props_key["anyOf"]:
            if item.get("type") and item.get("type") != "null":
                return item.get("type")
    return expected


def _get_dict_fields(props: dict) -> set:
    """Identify which fields in the schema are dict/object types."""
    dict_fields = set()
    for field, info in props.items():
        field_type = _get_field_type(info)
        if field_type == "object":
            dict_fields.add(field)
    return dict_fields


@metadata.command(name="update", context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option("--refresh-schema", is_flag=True, help="Force re-download of metadata schema")
@click.argument('pid')
@click.pass_context
def update_metadata(ctx, pid, refresh_schema, **kwargs):
    """
    Update metadata for a specific document by its PID.
    The command dynamically accepts and validates any field
    defined in the server's metadata schema.
    Metadata fields can be passed as command-line options.

    Example:

        yprov documents metadata update <prefix/id> --title "New Title" --keywords "keyword1" --keywords "keyword2"
        or
        yprov documents metadata update <prefix/id> --title "New Title" --keywords "keyword1,keyword2"

        # This command will empty both title and keywords:\n
        yprov documents metadata update <prefix/id> --title "" --keywords ""

        # For dict fields, use double underscore to specify nested keys:\n
        yprov documents metadata update <prefix/id> --extra__custom_field "value"
        
        # To delete a dict key, pass an empty string:\n
        yprov documents metadata update <prefix/id> --extra__custom_field ""
    
    - The PID must be fully qualified (prefix/id).
    - Fields not defined in the schema will be ignored.
    - To set an empty field, use an empty string
    - To set a list field, use multiple invocations of the same option, or pass a list as a comma-separated string.
    - To update a list field, you need to pass the entire list each time.
    - For dict fields, use --<dict_field>__<key> "value" syntax to set nested keys.
    - To delete a dict key, pass an empty string as the value.
    - If no fields are provided, the command will exit with a warning.
    """
    api_url = ctx.obj['API_URL']

    metadata = local_metadata_schema(api_url, refresh=refresh_schema)
    if not metadata:
        console.print("[red]❌ Cannot update metadata without a valid schema.[/red]")
        return
    
    if pid.startswith("--") or pid.startswith("-"):
        console.print(f"[red]❌ Invalid PID: {pid} (pass the PID before the metadata options)[/red]")
        return

    props = metadata.get("properties", {})
    dict_fields = _get_dict_fields(props)

    # 1) Gather only the dynamic fields:
    key = ""
    raw = {}
    for arg in ctx.args:
        if arg.startswith("--"):
            if key:
                console.print(f"[red]❌ Unexpected argument: {key} without value.[/red]")
                ctx.exit(1)
            key = arg[2:]
        else:
            if key:
                # Check if this is a dict field with __ syntax
                if "__" in key:
                    dict_field, dict_key = key.split("__", 1)
                    if dict_field in dict_fields:
                        if dict_field not in raw:
                            raw[dict_field] = {}
                        # Empty string means delete (set to None)
                        raw[dict_field][dict_key] = None if arg == "" else arg
                    else:
                        console.print(f"[red]❌ Field '{dict_field}' is not a dict field, cannot use '__' syntax.[/red]")
                        ctx.exit(1)
                elif key in raw:
                    if arg:
                        if isinstance(raw[key], list):
                            if arg not in raw[key]:
                                raw[key].append(arg)
                        elif arg != raw[key]:
                            raw[key] = [raw[key]].append(arg.split(","))
                else:
                    raw[key] = arg.split(",") if "," in arg else arg
                key = ""
            else:
                console.print(f"[red]❌ Unexpected value: {arg} without a preceding option.[/red]")
                ctx.exit(1)

    if key:
        console.print(f"[red]❌ Missing value for option: {key}.[/red]")
        ctx.exit(1)

    # 2) Load + validate
    errors = []
    for key, val in raw.items():
        if key not in props:
            errors.append(f"Unknown field: {key}")
            continue
        # basic type‐check
        props_key = props[key]
        expected = _get_field_type(props_key)
        if not expected and props_key.get("anyOf"):
            props_key = props_key["anyOf"][0]
        
        if expected == "string" and not isinstance(val, str):
            errors.append(f"{key} must be a string")
        # e.g. maxLength
        if isinstance(val, str) and "maxLength" in props_key:
            mx = props_key["maxLength"]
            if len(val) > mx:
                errors.append(f"{key} too long (max {mx})")
        # list‐of‐strings via multiple invocations
        if expected == "array" and props_key.get("items", {}).get("type") == "string":
            if not isinstance(val, (list, tuple)):
                if val == "":
                    raw[key] = []
                else:
                    raw[key] = [val]
        # dict/object type validation
        if expected == "object":
            if not isinstance(val, dict):
                errors.append(f"{key} must be a dict (use --{key}__<subkey> syntax)")
    if errors:
        for err in errors:
            click.echo(f"Error: {err}", err=True)
        ctx.exit(1)

    # 3) Send only those keys
    payload = raw
    if not payload:
        console.print("[yellow]No metadata provided to update.[/yellow]")
        return
    response = make_request("PATCH", api_url, f"/documents/{pid}/metadata", json=payload)

    if response and response.status_code == 200:
        console.print(f"[green]✔️ Metadata for PID {pid} updated successfully.[/green]")
        console.print_json(data=response.json())
    else:
        console.print(f"[red]❌ Error updating metadata for PID {pid}:[/red] {response.text if response else 'No response from server.'}")
