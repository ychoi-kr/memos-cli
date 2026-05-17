"""Tests for memos_cli.resources.attachment — download + prefix normalization."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from .conftest import FakeResponse


@pytest.fixture
def configured(isolated_config, fake_keyring, monkeypatch):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('url = "https://x"\n', encoding="utf-8")
    monkeypatch.setenv("MEMOS_TOKEN", "t")


class RawResponse:
    """FakeResponse variant carrying raw bytes for download tests."""

    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        self.text = ""

    def json(self):
        raise ValueError("not json")


def test_get_normalizes_raw_uid(configured, stub_session):
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "attachments/abc", "filename": "x.txt"})
    )
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["attachment", "get", "abc"])
    assert result.exit_code == 0
    assert stub_session["calls"][0]["url"].endswith("/api/v1/attachments/abc")


def test_get_passes_canonical_name_through(configured, stub_session):
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "attachments/abc"})
    )
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["attachment", "get", "attachments/abc"])
    assert result.exit_code == 0
    assert stub_session["calls"][0]["url"].endswith("/api/v1/attachments/abc")


def test_delete_normalizes_raw_uid(configured, stub_session):
    stub_session["responses"].append(FakeResponse(204))
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["attachment", "delete", "abc"])
    assert result.exit_code == 0
    assert stub_session["calls"][0]["method"] == "DELETE"
    assert stub_session["calls"][0]["url"].endswith("/api/v1/attachments/abc")


def test_list_normalizes_memo_filter(configured, stub_session):
    stub_session["responses"].append(FakeResponse(200, json_body={"attachments": []}))
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["attachment", "list", "--memo", "abc"])
    assert result.exit_code == 0
    sent_filter = stub_session["calls"][0]["params"]["filter"]
    assert "memo == 'memos/abc'" == sent_filter


def test_download_to_named_path(configured, stub_session, tmp_path):
    # metadata
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "attachments/abc", "filename": "x.txt"})
    )
    # content
    stub_session["responses"].append(RawResponse(200, b"hello bytes"))
    from memos_cli.cli import app

    out = tmp_path / "out.bin"
    result = CliRunner().invoke(app, ["attachment", "download", "abc", "--output", str(out)])
    assert result.exit_code == 0
    assert out.read_bytes() == b"hello bytes"
    assert stub_session["calls"][1]["url"].endswith("/file/attachments/abc/x.txt")


def test_download_default_uses_filename(configured, stub_session, tmp_path, monkeypatch):
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "attachments/abc", "filename": "y.md"})
    )
    stub_session["responses"].append(RawResponse(200, b"# heading"))
    monkeypatch.chdir(tmp_path)
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["attachment", "download", "abc"])
    assert result.exit_code == 0
    assert (tmp_path / "y.md").read_bytes() == b"# heading"
    assert "y.md" in result.output


def test_download_stdout_with_dash(configured, stub_session, tmp_path, monkeypatch):
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "attachments/abc", "filename": "y.md"})
    )
    stub_session["responses"].append(RawResponse(200, b"# heading"))
    monkeypatch.chdir(tmp_path)
    from memos_cli.cli import app

    result = CliRunner().invoke(app, ["attachment", "download", "abc", "--output", "-"])
    assert result.exit_code == 0
    # No file written to cwd when piping to stdout
    assert not (tmp_path / "y.md").exists()


def test_download_to_directory_appends_filename(
    configured, stub_session, tmp_path, monkeypatch
):
    stub_session["responses"].append(
        FakeResponse(200, json_body={"name": "attachments/abc", "filename": "y.md"})
    )
    stub_session["responses"].append(RawResponse(200, b"bytes"))
    target_dir = tmp_path / "downloads"
    target_dir.mkdir()
    from memos_cli.cli import app

    result = CliRunner().invoke(
        app, ["attachment", "download", "abc", "--output", str(target_dir)]
    )
    assert result.exit_code == 0
    assert (target_dir / "y.md").read_bytes() == b"bytes"
