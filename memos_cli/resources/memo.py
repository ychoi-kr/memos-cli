"""memo 서브커맨드."""

from __future__ import annotations

import sys

import typer

from ..api import Client
from ..output import emit, write_memo_pretty, die

app = typer.Typer(help="Manage memos", no_args_is_help=True)


def _read_content(content: str | None) -> str:
    if content is not None:
        return content
    if sys.stdin.isatty():
        die("no --content and stdin is empty", code=2)
    body = sys.stdin.read()
    if not body.strip():
        die("stdin is empty", code=2)
    return body


@app.command("list")
def list_(
    filter_: str = typer.Option(None, "--filter", help="CEL filter expression"),
    page_size: int = typer.Option(None, "--page-size"),
    page_token: str = typer.Option(None, "--page-token"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """List memos."""
    params: dict = {}
    if filter_:
        params["filter"] = filter_
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token

    client = Client()
    data = client.get("/api/v1/memos", params=params)
    memos = data.get("memos", []) if isinstance(data, dict) else data
    emit(
        data if not pretty else memos,
        pretty=pretty,
        pretty_writer=write_memo_pretty,
    )


@app.command("get")
def get(
    name: str = typer.Argument(..., help="memo name, e.g. memos/abc123"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Get a memo."""
    client = Client()
    data = client.get(f"/api/v1/{name}")
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_memo_pretty,
    )


@app.command("create")
def create(
    content: str = typer.Option(None, "--content", help="memo body (or stdin)"),
    visibility: str = typer.Option(None, "--visibility", help="PRIVATE/PROTECTED/PUBLIC"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Create a memo."""
    body = _read_content(content)
    payload: dict = {"content": body}
    if visibility:
        payload["visibility"] = visibility
    client = Client()
    data = client.post("/api/v1/memos", json=payload)
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_memo_pretty,
    )


@app.command("update")
def update(
    name: str = typer.Argument(..., help="memo name, e.g. memos/abc123"),
    content: str = typer.Option(None, "--content", help="memo body (or stdin)"),
    visibility: str = typer.Option(None, "--visibility"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Update a memo. Replaces the entire body."""
    print("warning: update replaces the entire body", file=sys.stderr)
    body = _read_content(content) if (content is not None or not sys.stdin.isatty()) else None
    payload: dict = {}
    if body is not None:
        payload["content"] = body
    if visibility:
        payload["visibility"] = visibility
    if not payload:
        die("update requires --content/stdin or --visibility", code=2)

    client = Client()
    data = client.patch(f"/api/v1/{name}", json=payload)
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_memo_pretty,
    )


@app.command("delete")
def delete(
    name: str = typer.Argument(..., help="memo name"),
):
    """Delete a memo."""
    client = Client()
    client.delete(f"/api/v1/{name}")
    print(f"deleted: {name}")
