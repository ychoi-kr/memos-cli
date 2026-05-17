"""Tests for memos_cli.api — HTTP status to exit code mapping."""

from __future__ import annotations

import pytest

from .conftest import FakeResponse


@pytest.fixture
def client(isolated_config, fake_keyring, monkeypatch):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x.example.com"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "tok")
    from memos_cli.api import Client
    return Client()


def test_authorization_header_set(client):
    assert client.session.headers["Authorization"] == "Bearer tok"


@pytest.mark.parametrize(
    "status,code",
    [(401, 3), (403, 4), (404, 5), (500, 1), (418, 1)],
)
def test_status_to_exit_code(client, stub_session, status, code, capsys):
    stub_session["responses"].append(FakeResponse(status, json_body={"message": "x"}))
    with pytest.raises(SystemExit) as exc:
        client.get("/api/v1/memos")
    assert exc.value.code == code


def test_silent_suppresses_stderr(client, stub_session, capsys):
    stub_session["responses"].append(FakeResponse(404, json_body={"message": "x"}))
    with pytest.raises(SystemExit):
        client.get("/api/v1/users/me", silent=True)
    captured = capsys.readouterr()
    assert captured.err == ""


def test_non_silent_writes_stderr(client, stub_session, capsys):
    stub_session["responses"].append(FakeResponse(404, json_body={"message": "boom"}))
    with pytest.raises(SystemExit):
        client.get("/api/v1/memos/missing")
    captured = capsys.readouterr()
    assert "not found" in captured.err
    assert "boom" in captured.err


def test_2xx_returns_parsed_json(client, stub_session):
    stub_session["responses"].append(FakeResponse(200, json_body={"name": "memos/x"}))
    assert client.get("/api/v1/memos/x") == {"name": "memos/x"}


def test_empty_body_returns_empty_dict(client, stub_session):
    stub_session["responses"].append(FakeResponse(204))
    assert client.delete("/api/v1/memos/x") == {}


def test_request_url_is_joined(client, stub_session):
    stub_session["responses"].append(FakeResponse(200, json_body={}))
    client.get("/api/v1/memos")
    assert stub_session["calls"][0]["url"] == "https://x.example.com/api/v1/memos"


def test_network_error_exits_1(client, monkeypatch, capsys):
    import requests

    def boom(*a, **kw):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr("requests.Session.request", boom)
    with pytest.raises(SystemExit) as exc:
        client.get("/api/v1/memos")
    assert exc.value.code == 1
    assert "no route" in capsys.readouterr().err
