"""Resource name normalization.

usememos uses `{collection}/{id}` names (e.g. `memos/abc123`, `attachments/xyz`).
The CLI accepts either form — `attachments/xyz` or the raw `xyz` — and
normalizes to the canonical form before constructing API paths.

If a name already contains a slash it is returned unchanged, so a caller
who explicitly wrote `memos/abc123` is never silently rewritten.
"""

from __future__ import annotations


def normalize(prefix: str, name: str) -> str:
    if "/" in name:
        return name
    return f"{prefix}/{name}"
