"""Tests for memos_cli.resources.user — /users/me fallback path."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from .conftest import FakeResponse


@pytest.fixture
def configured(isolated_config, fake_keyring, monkeypatch):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "t")


def test_user_me_uses_users_me_when_available(configured, stub_session):
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "users/3", "username": "yong"})
    )
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["user", "get", "me"])
    assert result.exit_code == 0
    assert "users/3" in result.output
    # only one HTTP call — no fallback needed
    assert len(stub_session["calls"]) == 1
    assert "/api/v1/users/me" in stub_session["calls"][0]["url"]


def test_user_me_falls_back_on_404(configured, stub_session):
    # first call (users/me) -> 404
    stub_session["responses"].append(FakeResponse(404, json_body={"message": "x"}))
    # second call (sessions/current) -> 200
    stub_session["responses"].append(
        FakeResponse(
            200,
            json_body={"user": {"name": "users/3", "username": "yong"}},
        )
    )
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["user", "get", "me"])
    assert result.exit_code == 0
    assert "users/3" in result.output
    assert len(stub_session["calls"]) == 2
    assert "/api/v1/auth/sessions/current" in stub_session["calls"][1]["url"]


def test_user_me_does_not_fall_back_on_401(configured, stub_session):
    """401 must surface as exit 3, not silently fallback."""
    stub_session["responses"].append(FakeResponse(401, json_body={"message": "x"}))
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["user", "get", "me"])
    assert result.exit_code == 3
    # no second call attempted
    assert len(stub_session["calls"]) == 1


def test_user_get_numeric_id(configured, stub_session):
    stub_session["responses"].append(FakeResponse(200, json_body={"name": "users/7"}))
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["user", "get", "7"])
    assert result.exit_code == 0
    assert "/api/v1/users/7" in stub_session["calls"][0]["url"]
