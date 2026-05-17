"""Tests for memos_cli.names — resource name normalization."""

from __future__ import annotations

from memos_cli.names import normalize


def test_raw_id_gets_prefix():
    assert normalize("attachments", "abc123") == "attachments/abc123"


def test_canonical_passthrough():
    assert normalize("attachments", "attachments/abc123") == "attachments/abc123"


def test_slash_input_never_rewritten():
    # If the user types a wrong prefix, do not silently fix it — surface the 404.
    assert normalize("attachments", "memos/x") == "memos/x"


def test_works_for_each_resource():
    assert normalize("memos", "x") == "memos/x"
    assert normalize("users", "3") == "users/3"
    assert normalize("attachments", "y") == "attachments/y"
