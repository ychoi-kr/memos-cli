"""Shared fixtures for memos-cli tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point XDG_CONFIG_HOME at a temp dir and clear MEMOS_* env vars."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("MEMOS_URL", raising=False)
    monkeypatch.delenv("MEMOS_TOKEN", raising=False)
    return tmp_path / "memos" / "config.toml"


@pytest.fixture
def fake_keyring(monkeypatch):
    """Replace keyring backend with an in-memory store.

    On macOS this patches subprocess.run to intercept ``security`` CLI calls.
    Patching at the subprocess level survives importlib.reload() in tests.
    On other platforms it patches the keyring module functions.
    """
    import subprocess
    import sys

    store: dict[tuple[str, str], str] = {}

    if sys.platform == "darwin":
        _real_run = subprocess.run

        def _fake_run(cmd, *args, **kwargs):
            if isinstance(cmd, list) and cmd and cmd[0] == "security":
                if "find-generic-password" in cmd:
                    token = store.get(("memos", "token"))
                    if token:
                        return subprocess.CompletedProcess(cmd, 0, stdout=token + "\n", stderr="")
                    return subprocess.CompletedProcess(cmd, 44, stdout="", stderr="")
                if "add-generic-password" in cmd:
                    w_idx = cmd.index("-w")
                    store[("memos", "token")] = cmd[w_idx + 1]
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                if "delete-generic-password" in cmd:
                    store.pop(("memos", "token"), None)
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return _real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", _fake_run)
    else:
        def get_password(service, username):
            return store.get((service, username))

        def set_password(service, username, password):
            store[(service, username)] = password

        def delete_password(service, username):
            if (service, username) not in store:
                import keyring.errors
                raise keyring.errors.PasswordDeleteError(f"no entry for {service}/{username}")
            del store[(service, username)]

        monkeypatch.setattr("keyring.get_password", get_password)
        monkeypatch.setattr("keyring.set_password", set_password)
        monkeypatch.setattr("keyring.delete_password", delete_password)
    return store


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code=200, json_body=None, text=""):
        self.status_code = status_code
        self._json = json_body
        self.text = text
        self.content = b"x" if (json_body is not None or text) else b""

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


@pytest.fixture
def stub_session(monkeypatch):
    """Replace requests.Session.request with a recorder/dispatcher."""
    calls: list[dict] = []
    responses: list[FakeResponse] = []

    def request(self, method, url, **kwargs):
        calls.append({"method": method, "url": url, "headers": dict(self.headers), **kwargs})
        if not responses:
            return FakeResponse(200, json_body={})
        return responses.pop(0)

    monkeypatch.setattr("requests.Session.request", request)
    return {"calls": calls, "responses": responses}
