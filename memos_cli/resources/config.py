"""config 서브커맨드."""

from __future__ import annotations

import os
import subprocess
import sys

import typer

from .. import creds
from ..output import die

app = typer.Typer(help="Manage local configuration", no_args_is_help=True)


@app.command("show")
def show():
    """Show resolved URL and token location (token value is masked)."""
    url_source = "config.toml"
    try:
        url = creds._read_config().get("url")
        if not url:
            url = os.environ.get("MEMOS_URL")
            url_source = "MEMOS_URL" if url else "(none)"
    except Exception:
        url = None
        url_source = "(error)"

    print(f"url:     {url or '(not set)'}  [{url_source}]")
    print(f"token:   <masked>  [{creds.token_location()}]")
    print(f"config:  {creds.config_path()}")


@app.command("path")
def path():
    """Print the config.toml path."""
    print(creds.config_path())


@app.command("edit")
def edit():
    """Open config.toml in $EDITOR."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        die("EDITOR or VISUAL environment variable not set", code=2)

    path = creds.config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text('url = ""\n', encoding="utf-8")
        path.chmod(0o644)

    try:
        subprocess.run([editor, str(path)], check=True)
    except subprocess.CalledProcessError as e:
        die(f"editor exited with {e.returncode}", code=1)
    except FileNotFoundError:
        die(f"editor not found: {editor}", code=2)
