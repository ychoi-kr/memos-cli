"""Tests for memos_cli.creds — credential lookup priority and config bootstrapping."""

from __future__ import annotations

import importlib

import pytest


def _reload_creds():
    import memos_cli.creds as creds
    return importlib.reload(creds)


def test_get_url_from_config(isolated_config, fake_keyring):
    creds = _reload_creds()
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://memos.example.com"\n', encoding="utf-8")
    assert creds.get_url() == "https://memos.example.com"


def test_get_url_strips_trailing_slash(isolated_config, fake_keyring):
    creds = _reload_creds()
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://memos.example.com/"\n', encoding="utf-8")
    assert creds.get_url() == "https://memos.example.com"


def test_get_url_from_env_creates_config(isolated_config, fake_keyring, monkeypatch, capsys):
    creds = _reload_creds()
    monkeypatch.setenv("MEMOS_URL", "https://from-env.example.com")
    assert creds.get_url() == "https://from-env.example.com"
    assert isolated_config.exists()
    body = isolated_config.read_text(encoding="utf-8")
    assert "from-env.example.com" in body
    captured = capsys.readouterr()
    assert "created" in captured.err


def test_get_url_missing_exits(isolated_config, fake_keyring):
    creds = _reload_creds()
    with pytest.raises(SystemExit) as exc:
        creds.get_url()
    assert exc.value.code == 1


def test_config_token_key_warns(isolated_config, fake_keyring, capsys):
    creds = _reload_creds()
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text(
        'url = "https://x"\ntoken = "leaked-token"\n',
        encoding="utf-8",
    )
    creds.get_url()
    captured = capsys.readouterr()
    assert "token" in captured.err
    assert "ignored" in captured.err


def test_get_token_from_keyring(isolated_config, fake_keyring):
    creds = _reload_creds()
    fake_keyring[("memos", "token")] = "kr-token"
    assert creds.get_token() == "kr-token"


def test_get_token_from_env(isolated_config, fake_keyring, monkeypatch):
    creds = _reload_creds()
    monkeypatch.setenv("MEMOS_TOKEN", "env-token")
    assert creds.get_token() == "env-token"


def test_get_token_keyring_beats_env(isolated_config, fake_keyring, monkeypatch):
    creds = _reload_creds()
    fake_keyring[("memos", "token")] = "kr-token"
    monkeypatch.setenv("MEMOS_TOKEN", "env-token")
    assert creds.get_token() == "kr-token"


def test_get_token_missing_exits(isolated_config, fake_keyring):
    creds = _reload_creds()
    with pytest.raises(SystemExit) as exc:
        creds.get_token()
    assert exc.value.code == 3


def test_token_location(isolated_config, fake_keyring, monkeypatch):
    creds = _reload_creds()
    assert creds.token_location() == "none"
    monkeypatch.setenv("MEMOS_TOKEN", "x")
    assert creds.token_location() == "env"
    fake_keyring[("memos", "token")] = "y"
    assert creds.token_location() == "keyring"


def test_set_and_delete_token(isolated_config, fake_keyring):
    creds = _reload_creds()
    creds.set_token("new")
    assert fake_keyring[("memos", "token")] == "new"
    creds.delete_token()
    assert ("memos", "token") not in fake_keyring


def test_delete_token_when_absent_is_silent(isolated_config, fake_keyring):
    creds = _reload_creds()
    creds.delete_token()  # should not raise
