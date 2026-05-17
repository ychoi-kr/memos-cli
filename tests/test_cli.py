"""Tests for memos_cli.cli — top-level dispatch."""

from __future__ import annotations

from typer.testing import CliRunner

from memos_cli.cli import app


def test_help_lists_all_resources():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("memo", "attachment", "user", "config", "auth"):
        assert cmd in result.output


def test_no_args_shows_help():
    result = CliRunner().invoke(app, [])
    # typer exits with non-zero when no_args_is_help is set
    assert "Commands" in result.output or "Usage" in result.output


def test_memo_help_lists_verbs():
    result = CliRunner().invoke(app, ["memo", "--help"])
    assert result.exit_code == 0
    for verb in ("list", "get", "create", "update", "delete"):
        assert verb in result.output


def test_auth_status_shows_none_when_unset(isolated_config, fake_keyring):
    result = CliRunner().invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "[none]" in result.output


def test_config_path_prints_xdg_path(isolated_config, fake_keyring):
    result = CliRunner().invoke(app, ["config", "path"])
    assert result.exit_code == 0
    assert "memos/config.toml" in result.output
