"""auth 서브커맨드."""

from __future__ import annotations

import getpass

import typer

from .. import creds
from ..output import die

app = typer.Typer(help="Manage authentication credentials", no_args_is_help=True)


@app.command("login")
def login():
    """Prompt for token and store in OS keyring."""
    token = getpass.getpass("memos token: ")
    if not token.strip():
        die("empty token", code=2)
    creds.set_token(token.strip())
    print("token stored in keyring")


@app.command("logout")
def logout():
    """Remove token from OS keyring."""
    creds.delete_token()
    print("token removed from keyring")


@app.command("status")
def status():
    """Show where the token is stored. Never prints the value."""
    print(f"token: <masked>  [{creds.token_location()}]")
