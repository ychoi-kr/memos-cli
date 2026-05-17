"""attachment 서브커맨드."""

from __future__ import annotations

from pathlib import Path

import typer

from ..api import Client
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
    memo: str = typer.Option(None, "--memo", help="filter by memo name"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """List attachments."""
    params: dict = {}
    if memo:
        params["filter"] = f"memo == '{memo}'"
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
    name: str = typer.Argument(..., help="attachment name, e.g. attachments/xxxx"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Get attachment metadata."""
    client = Client()
    data = client.get(f"/api/v1/{name}")
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_attachment_pretty,
    )


@app.command("delete")
def delete(
    name: str = typer.Argument(..., help="attachment name"),
):
    """Delete an attachment."""
    client = Client()
    client.delete(f"/api/v1/{name}")
    print(f"deleted: {name}")
