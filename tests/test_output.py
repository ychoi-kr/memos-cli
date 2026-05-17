"""Tests for memos_cli.output — JSON / pretty formatters."""

from __future__ import annotations

import json

from memos_cli import output


def test_write_json_utf8(capsys):
    output.write_json({"k": "한글"})
    out = capsys.readouterr().out
    assert json.loads(out) == {"k": "한글"}


def test_emit_json_when_pretty_false(capsys):
    output.emit({"a": 1}, pretty=False, pretty_writer=output.write_memo_pretty)
    assert json.loads(capsys.readouterr().out) == {"a": 1}


def test_emit_pretty_invokes_writer(capsys):
    output.emit(
        [{"name": "memos/x", "visibility": "PRIVATE", "createTime": "t", "content": "hi"}],
        pretty=True,
        pretty_writer=output.write_memo_pretty,
    )
    out = capsys.readouterr().out
    assert "memos/x" in out and "PRIVATE" in out


def test_memo_pretty_empty(capsys):
    output.write_memo_pretty([])
    assert "no memos" in capsys.readouterr().out


def test_memo_pretty_truncates_long_content(capsys):
    long = "a" * 200
    output.write_memo_pretty(
        [{"name": "memos/x", "visibility": "P", "createTime": "t", "content": long}]
    )
    out = capsys.readouterr().out
    assert "…" in out


def test_memo_pretty_strips_newlines(capsys):
    output.write_memo_pretty(
        [{"name": "memos/x", "visibility": "P", "createTime": "t", "content": "line1\nline2"}]
    )
    out = capsys.readouterr().out
    # newline inside content should be replaced with space; the line itself ends with \n
    assert "line1 line2" in out


def test_die_exits_with_code(capsys):
    import pytest
    with pytest.raises(SystemExit) as exc:
        output.die("nope", code=2)
    assert exc.value.code == 2
    assert "nope" in capsys.readouterr().err
