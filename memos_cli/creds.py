"""자격증명·설정 조회.

조회 우선순위:
    token: keyring("memos", "token") → MEMOS_TOKEN → 종료(3)
    url:   config.toml.url → MEMOS_URL → 종료(1)

macOS에서는 security CLI로 Keychain에 접근한다.
Python 바이너리의 코드 서명 상태와 무관하게 토큰을 읽고 쓸 수 있다.
Linux 등 다른 플랫폼에서는 keyring 라이브러리를 사용한다.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

_IS_MACOS = sys.platform == "darwin"

if not _IS_MACOS:
    import keyring

KEYRING_SERVICE = "memos"
KEYRING_USERNAME = "token"


def _security_get() -> str | None:
    try:
        result = subprocess.run(
            ["security", "find-generic-password",
             "-s", KEYRING_SERVICE, "-a", KEYRING_USERNAME, "-w"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _security_set(token: str) -> None:
    subprocess.run(
        ["security", "add-generic-password",
         "-s", KEYRING_SERVICE, "-a", KEYRING_USERNAME, "-w", token, "-U"],
        check=True, capture_output=True,
    )


def _security_delete() -> None:
    subprocess.run(
        ["security", "delete-generic-password",
         "-s", KEYRING_SERVICE, "-a", KEYRING_USERNAME],
        capture_output=True,
    )


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
    if _IS_MACOS:
        token = _security_get()
    else:
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
    if _IS_MACOS:
        if _security_get():
            return "keyring"
    else:
        try:
            if keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME):
                return "keyring"
        except keyring.errors.KeyringError:
            pass
    if os.environ.get("MEMOS_TOKEN"):
        return "env"
    return "none"


def set_token(token: str) -> None:
    if _IS_MACOS:
        _security_set(token)
    else:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)


def delete_token() -> None:
    if _IS_MACOS:
        _security_delete()
    else:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except keyring.errors.PasswordDeleteError:
            pass


def get_resolved() -> tuple[str, str]:
    return get_url(), get_token()
