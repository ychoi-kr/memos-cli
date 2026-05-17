"""usememos REST 클라이언트.

HTTP 상태 → 종료 코드 매핑:
    401 → 3 (인증 실패)
    403 → 4 (권한 거부)
    404 → 5 (자원 없음)
    그 외 4xx/5xx/네트워크 → 1 (일반 오류)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

from . import creds


def _exit_for_status(resp: requests.Response, *, silent: bool = False) -> None:
    if resp.status_code < 400:
        return
    if resp.status_code == 401:
        code, label = 3, "authentication failed"
    elif resp.status_code == 403:
        code, label = 4, "permission denied"
    elif resp.status_code == 404:
        code, label = 5, "not found"
    else:
        code, label = 1, f"http {resp.status_code}"

    if not silent:
        detail = ""
        try:
            body = resp.json()
            detail = body.get("message") or body.get("error") or ""
        except ValueError:
            detail = resp.text[:200]
        print(f"error: {label}{': ' + detail if detail else ''}", file=sys.stderr)
    sys.exit(code)


class Client:
    def __init__(self, url: str | None = None, token: str | None = None):
        self.url = (url or creds.get_url()).rstrip("/")
        self.token = token or creds.get_token()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "User-Agent": "memos-cli/0.1.0",
            }
        )

    def _full(self, path: str) -> str:
        return self.url + path

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: Any = None,
        files: dict | None = None,
        data: Any = None,
        silent: bool = False,
    ) -> Any:
        try:
            resp = self.session.request(
                method,
                self._full(path),
                params=params,
                json=json,
                files=files,
                data=data,
                timeout=30,
            )
        except requests.RequestException as e:
            if not silent:
                print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

        _exit_for_status(resp, silent=silent)

        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}

    def get(self, path: str, params: dict | None = None, *, silent: bool = False) -> Any:
        return self._request("GET", path, params=params, silent=silent)

    def post(self, path: str, json: Any = None) -> Any:
        return self._request("POST", path, json=json)

    def patch(self, path: str, json: Any = None) -> Any:
        return self._request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def upload(self, path: str, file_path: Path, *, mime: str | None = None) -> Any:
        """Upload a file. usememos expects base64 content inside a JSON body."""
        import base64
        import mimetypes

        if mime is None:
            mime, _ = mimetypes.guess_type(str(file_path))
            if mime is None:
                mime = "application/octet-stream"

        payload = {
            "filename": file_path.name,
            "type": mime,
            "content": base64.b64encode(file_path.read_bytes()).decode("ascii"),
        }
        return self._request("POST", path, json=payload)

    def download(self, path: str) -> bytes:
        """Fetch a raw binary response (e.g. attachment content)."""
        try:
            resp = self.session.get(self._full(path), timeout=60)
        except requests.RequestException as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        _exit_for_status(resp)
        return resp.content
