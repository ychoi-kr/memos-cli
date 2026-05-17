"""user 서브커맨드.

`get me`는 일부 환경에서 /users/me가 동작하지 않는 경우 토큰 소유자 검색으로 fallback.
"""

from __future__ import annotations

import typer

from ..api import Client
from ..output import emit, write_user_pretty

app = typer.Typer(help="Manage users", no_args_is_help=True)


@app.command("list")
def list_(
    pretty: bool = typer.Option(False, "--pretty"),
):
    """List users."""
    client = Client()
    data = client.get("/api/v1/users")
    users = data.get("users", []) if isinstance(data, dict) else data
    emit(
        data if not pretty else users,
        pretty=pretty,
        pretty_writer=write_user_pretty,
    )


@app.command("get")
def get(
    target: str = typer.Argument(..., help="user id, 'users/N', or 'me'"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Get a user."""
    client = Client()

    if target == "me":
        try:
            data = client.get("/api/v1/users/me", silent=True)
            emit(
                [data] if pretty else data,
                pretty=pretty,
                pretty_writer=write_user_pretty,
            )
            return
        except SystemExit as e:
            # 404일 때만 현재 세션에서 본인 정보 추출
            if e.code != 5:
                raise
            data = client.get("/api/v1/auth/sessions/current")
            user = data.get("user") or data
            emit(
                [user] if pretty else user,
                pretty=pretty,
                pretty_writer=write_user_pretty,
            )
            return

    path = target if target.startswith("users/") else f"users/{target}"
    data = client.get(f"/api/v1/{path}")
    emit(
        [data] if pretty else data,
        pretty=pretty,
        pretty_writer=write_user_pretty,
    )
