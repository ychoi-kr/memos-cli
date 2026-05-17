"""Tests for memos_cli.resources.memo — content reading + safety rules."""

from __future__ import annotations

import io

import pytest

from memos_cli.resources import memo as memo_mod


def test_read_content_from_arg():
    assert memo_mod._read_content("hello") == "hello"


def test_read_content_from_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("body from stdin"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    # StringIO.isatty() already returns False
    assert memo_mod._read_content(None) == "body from stdin"


def test_read_content_empty_stdin_exits(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("   \n"))
    with pytest.raises(SystemExit) as exc:
        memo_mod._read_content(None)
    assert exc.value.code == 2
    assert "empty" in capsys.readouterr().err


def test_read_content_tty_with_no_arg_exits(monkeypatch, capsys):
    class TtyStdin(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", TtyStdin(""))
    with pytest.raises(SystemExit) as exc:
        memo_mod._read_content(None)
    assert exc.value.code == 2


def test_update_warns_about_full_body_replace(
    isolated_config, fake_keyring, stub_session, monkeypatch, capsys
):
    """`memo update` must emit a stderr warning every call."""
    from .conftest import FakeResponse

    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "t")
    stub_session["responses"].append(FakeResponse(200, json_body={"name": "memos/x"}))

    from typer.testing import CliRunner
    from memos_cli.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["memo", "update", "memos/x", "--content", "new body"],
    )
    assert result.exit_code == 0
    # Typer's CliRunner merges stderr into stdout by default
    assert "update replaces the entire body" in (result.stderr or result.output)


def test_update_without_any_input_exits_2(
    isolated_config, fake_keyring, monkeypatch
):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "t")

    from typer.testing import CliRunner
    from memos_cli.cli import app

    runner = CliRunner()
    # No --content, no --visibility, stdin is a tty in CliRunner by default
    result = runner.invoke(app, ["memo", "update", "memos/x"])
    assert result.exit_code == 2


def test_get_normalizes_raw_memo_uid(isolated_config, fake_keyring, stub_session, monkeypatch):
    from .conftest import FakeResponse
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "t")
    stub_session["responses"].append(FakeResponse(200, json_body={"name": "memos/abc"}))

    from typer.testing import CliRunner
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["memo", "get", "abc"])
    assert result.exit_code == 0
    assert stub_session["calls"][0]["url"].endswith("/api/v1/memos/abc")


def test_delete_normalizes_raw_memo_uid(isolated_config, fake_keyring, stub_session, monkeypatch):
    from .conftest import FakeResponse
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "t")
    stub_session["responses"].append(FakeResponse(204))

    from typer.testing import CliRunner
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["memo", "delete", "abc"])
    assert result.exit_code == 0
    assert stub_session["calls"][0]["url"].endswith("/api/v1/memos/abc")
