"""attachment 서브커맨드."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from ..api import Client
from ..names import normalize
from ..output import emit, write_attachment_pretty, die

app = typer.Typer(help="Manage attachments", no_args_is_help=True)


@app.command("upload")
def upload(
    file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Upload an attachment."""
    client = Client()
    data = client.upload("/api/v1/attachments", file)
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_attachment_pretty,
    )


@app.command("list")
def list_(
    memo: str = typer.Option(None, "--memo", help="filter by memo name or raw uid"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """List attachments."""
    params: dict = {}
    if memo:
        params["filter"] = f"memo == '{normalize('memos', memo)}'"
    client = Client()
    data = client.get("/api/v1/attachments", params=params)
    items = data.get("attachments", []) if isinstance(data, dict) else data
    emit(
        data if not pretty else items,
        pretty=pretty,
        pretty_writer=write_attachment_pretty,
    )


@app.command("get")
def get(
    name: str = typer.Argument(..., help="attachment name (attachments/xxxx) or raw uid"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Get attachment metadata."""
    name = normalize("attachments", name)
    client = Client()
    data = client.get(f"/api/v1/{name}")
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_attachment_pretty,
    )


@app.command("download")
def download(
    name: str = typer.Argument(..., help="attachment name or raw uid"),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="output path. Use '-' for stdout. Defaults to the original filename in the current directory.",
    ),
):
    """Download attachment content."""
    name = normalize("attachments", name)
    client = Client()
    meta = client.get(f"/api/v1/{name}")
    filename = meta.get("filename") or name.split("/")[-1]
    content = client.download(f"/file/{name}/{filename}")

    if output == "-":
        sys.stdout.buffer.write(content)
        return

    out_path = Path(output) if output else Path(filename)
    if out_path.is_dir():
        out_path = out_path / filename
    out_path.write_bytes(content)
    print(str(out_path))


@app.command("delete")
def delete(
    name: str = typer.Argument(..., help="attachment name or raw uid"),
):
    """Delete an attachment."""
    name = normalize("attachments", name)
    client = Client()
    client.delete(f"/api/v1/{name}")
    print(f"deleted: {name}")
