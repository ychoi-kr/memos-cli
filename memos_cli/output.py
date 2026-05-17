"""출력 포맷."""

from __future__ import annotations

import json
import sys
from typing import Any


def write_json(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _truncate(s: str, n: int) -> str:
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def write_memo_pretty(memos: list[dict]) -> None:
    if not memos:
        print("(no memos)")
        return
    for m in memos:
        name = m.get("name", "?")
        vis = m.get("visibility", "")
        ts = m.get("createTime") or m.get("createdTs") or ""
        snippet = _truncate(m.get("content", ""), 60)
        print(f"{name}\t{vis}\t{ts}\t{snippet}")


def write_user_pretty(users: list[dict]) -> None:
    if not users:
        print("(no users)")
        return
    for u in users:
        name = u.get("name") or f"users/{u.get('id', '?')}"
        nick = u.get("nickname") or u.get("username") or ""
        role = u.get("role", "")
        print(f"{name}\t{nick}\t{role}")


def write_attachment_pretty(attachments: list[dict]) -> None:
    if not attachments:
        print("(no attachments)")
        return
    for a in attachments:
        name = a.get("name", "?")
        fname = a.get("filename", "")
        size = a.get("size", "")
        typ = a.get("type", "")
        print(f"{name}\t{fname}\t{size}\t{typ}")


def emit(
    value: Any,
    *,
    pretty: bool,
    pretty_writer=None,
) -> None:
    if pretty and pretty_writer is not None:
        pretty_writer(value)
    else:
        write_json(value)


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)
