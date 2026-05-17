"""자격증명·설정 조회.

조회 우선순위:
    token: keyring("memos", "token") → MEMOS_TOKEN → 종료(3)
    url:   config.toml.url → MEMOS_URL → 종료(1)
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

import keyring

KEYRING_SERVICE = "memos"
KEYRING_USERNAME = "token"


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "memos" / "config.toml"


def _read_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _write_config(data: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key, value in data.items():
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key} = "{escaped}"')
        else:
            lines.append(f"{key} = {value!r}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o644)


def get_url() -> str:
    data = _read_config()

    if "token" in data:
        print(
            f"warning: config.toml 'token' key is ignored — use 'memos auth login' instead "
            f"({config_path()})",
            file=sys.stderr,
        )

    url = data.get("url")
    if url:
        return url.rstrip("/")

    env_url = os.environ.get("MEMOS_URL")
    if env_url:
        if not config_path().exists():
            _write_config({"url": env_url})
            print(
                f"info: created {config_path()} from MEMOS_URL",
                file=sys.stderr,
            )
        return env_url.rstrip("/")

    print(
        "error: memos URL not set. run 'memos config edit' or set MEMOS_URL.",
        file=sys.stderr,
    )
    sys.exit(1)


def get_token() -> str:
    try:
        token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring.errors.KeyringError:
        token = None

    if token:
        return token

    env_token = os.environ.get("MEMOS_TOKEN")
    if env_token:
        return env_token

    print(
        "error: memos token not set. run 'memos auth login' or set MEMOS_TOKEN.",
        file=sys.stderr,
    )
    sys.exit(3)


def token_location() -> str:
    try:
        if keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME):
            return "keyring"
    except keyring.errors.KeyringError:
        pass
    if os.environ.get("MEMOS_TOKEN"):
        return "env"
    return "none"


def set_token(token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)


def delete_token() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass


def get_resolved() -> tuple[str, str]:
    return get_url(), get_token()
