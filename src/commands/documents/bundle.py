import os
import csv
import json
import click
import statistics
import requests
from rich.console import Console
from rich.table import Table

from utils.api_client import make_request, load_token

console = Console()


def _resolve_artifact_path(value, prov_dir, dirname):
    if not isinstance(value, str) or not value:
        return None
    candidates = [os.path.normpath(os.path.join(prov_dir, value))]
    if value.startswith(f"prov/{dirname}/"):
        candidates.append(os.path.normpath(os.path.join(prov_dir, value[len(f"prov/{dirname}/"):])))
    else:
        parts = value.split("/", 2)
        if len(parts) == 3 and parts[0] == "prov":
            candidates.append(os.path.normpath(os.path.join(prov_dir, parts[2])))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _path_category(path, prov_dir):
    top = os.path.relpath(path, prov_dir).split(os.sep)[0]
    if top.startswith("artifacts"):
        return "artifact"
    if top.startswith("metrics"):
        return "metric"
    return None


def _summarize_csv(path):
    if not path.endswith('.csv'):
        return None
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return None
        col = 'value' if 'value' in reader.fieldnames else reader.fieldnames[-1]
        values = []
        for row in reader:
            try:
                values.append(float(row[col]))
            except (TypeError, ValueError):
                continue
    if not values:
        return None
    return {
        'count': len(values),
        'min': min(values),
        'max': max(values),
        'mean': statistics.mean(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def _upload_file(api_url, path):
    filename = os.path.basename(path)
    resp = make_request("POST", api_url, "/artifacts/upload/url", params={'filename': filename})
    if not resp or resp.status_code != 200:
        return None
    info = resp.json()
    pid, upload_url = info.get('pid'), info.get('upload_url')
    if not pid or not upload_url:
        return None
    headers = {}
    token = load_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with open(path, 'rb') as f:
        r = requests.put(upload_url, files={'document_file': (filename, f, 'application/octet-stream')}, headers=headers)
    return pid if r.status_code == 200 else None


@click.command(name="upload-bundle")
@click.argument('prov_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--json-file', type=click.Path(exists=True, dir_okay=False), help="Explicit path to the provenance JSON file inside the directory.")
@click.option('--parent-pid', help="PID of the parent document, if any.")
@click.option('--dry-run', is_flag=True, help="Resolve artifacts to upload without uploading or publishing anything.")
@click.option('--summarize-metrics/--upload-metrics', default=True, help="Summarize metric CSVs inline (default) instead of uploading them as artifacts.")
@click.pass_context
def upload_bundle(ctx, prov_dir, json_file, parent_pid, dry_run, summarize_metrics):
    """Upload every local artifact referenced in a provenance JSON, substitute PIDs, then publish the document.

    PROV_DIR is a directory containing the provenance JSON and its referenced artifact files.

    Example:
        yprov documents upload-bundle ./example_2
    """
    api_url = ctx.obj['API_URL']
    prov_dir = os.path.abspath(prov_dir)
    dirname = os.path.basename(prov_dir)

    if not json_file:
        candidates = [f for f in os.listdir(prov_dir) if f.endswith('.json')]
        if len(candidates) != 1:
            console.print(f"❌ [bold red]Error:[/bold red] expected exactly one JSON file in '{prov_dir}', found {len(candidates)}. Use --json-file.")
            return
        json_file = os.path.join(prov_dir, candidates[0])

    with open(json_file) as f:
        doc = json.load(f)

    path_to_pid = {}
    upload_replacements = []
    metric_replacements = []
    for entity_id, entity_data in doc.get('entity', {}).items():
        if not isinstance(entity_data, dict):
            continue
        for key, value in entity_data.items():
            path = _resolve_artifact_path(value, prov_dir, dirname)
            if not path:
                continue
            category = _path_category(path, prov_dir)
            if category == "artifact" or (category == "metric" and not summarize_metrics):
                upload_replacements.append((entity_id, key, path))
                path_to_pid.setdefault(path, None)
            elif category == "metric":
                metric_replacements.append((entity_id, key, path))

    if not path_to_pid and not metric_replacements:
        console.print("[yellow]No local artifact or metric files found.[/yellow]")
    if path_to_pid:
        table = Table(title="Artifacts to upload")
        table.add_column("File")
        for p in path_to_pid:
            table.add_row(os.path.relpath(p, prov_dir))
        console.print(table)
    if metric_replacements:
        table = Table(title="Metrics to summarize")
        table.add_column("File")
        for _, _, p in metric_replacements:
            table.add_row(os.path.relpath(p, prov_dir))
        console.print(table)

    if dry_run:
        console.print(f"[dim]Dry run: {len(path_to_pid)} artifact(s) would be uploaded, {len(metric_replacements)} metric(s) would be summarized.[/dim]")
        return

    for path in path_to_pid:
        console.print(f"📤 Uploading [cyan]{os.path.relpath(path, prov_dir)}[/cyan]...")
        pid = _upload_file(api_url, path)
        if not pid:
            console.print(f"❌ [bold red]Failed to upload {path}, aborting.[/bold red]")
            return
        path_to_pid[path] = pid
        console.print(f"   → PID: [green]{pid}[/green]")

    for entity_id, key, path in upload_replacements:
        doc['entity'][entity_id][key] = path_to_pid[path]

    for entity_id, key, path in metric_replacements:
        summary = _summarize_csv(path)
        if summary is not None:
            doc['entity'][entity_id][key] = summary

    tmp_path = os.path.join(prov_dir, f".{dirname}_resolved.json")
    with open(tmp_path, 'w') as f:
        json.dump(doc, f)

    console.print("📄 Publishing document...")
    try:
        with open(tmp_path, 'rb') as f:
            files = {'document_file': (os.path.basename(json_file), f, 'application/json')}
            params = {'parent_document_pid': parent_pid} if parent_pid else {}
            response = make_request("POST", api_url, "/documents", params=params, files=files)
    finally:
        os.remove(tmp_path)

    if response and response.status_code == 200:
        console.print("✅ [bold green]Document published successfully![/bold green]")
        console.print_json(data=response.json())
    else:
        console.print(f"❌ [bold red]Error[/bold red] {response.status_code if response else ''}: {response.text if response else 'No response.'}")
