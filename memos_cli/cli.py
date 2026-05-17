"""memos CLI entry point.

Thin client over usememos REST API. Workflow conventions (tag schemes,
body templates, machine ID mapping, attachment-link composition) stay
on the caller side — see PRD section 3.2.
"""

from __future__ import annotations

import typer

from .resources import attachment as attachment_cmd
from .resources import auth as auth_cmd
from .resources import config as config_cmd
from .resources import memo as memo_cmd
from .resources import user as user_cmd

app = typer.Typer(
    help="Thin CLI for usememos self-hosted memo service",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(memo_cmd.app, name="memo")
app.add_typer(attachment_cmd.app, name="attachment")
app.add_typer(user_cmd.app, name="user")
app.add_typer(config_cmd.app, name="config")
app.add_typer(auth_cmd.app, name="auth")
