# memos-cli

Thin command-line client for [usememos](https://github.com/usememos/memos) self-hosted memo service.

## What it does

- Maps usememos REST API endpoints 1:1 to `memos <resource> <verb>` commands.
- Stores tokens in the OS keyring (macOS Keychain / Windows Credential Manager / Linux Secret Service).
- Keeps URL in `~/.config/memos/config.toml` (plaintext, non-secret).
- Handles UTF-8 encoding, base64, and multipart upload internally.
- Works identically on bash, zsh, PowerShell, and fish.

## What it does *not* do

By design — these belong on the caller side (SKILL.md, shell aliases, scripts):

- Tag conventions
- Body templates
- Machine ↔ user mapping
- Attachment-then-link composition
- Session ID stamping

See `PRD.md` section 3.2.

## Install

```bash
uv tool install memos-cli      # recommended
# or
pip install --user memos-cli
```

Requires Python 3.11+.

## First-time setup

```bash
# 1. Set the server URL (one-time).
memos config edit                       # opens config.toml in $EDITOR
# or:
export MEMOS_URL=https://memos.example.com
memos memo list                         # auto-creates config.toml from env

# 2. Store the token in the OS keyring.
memos auth login                        # prompts for token (getpass)

# 3. Verify.
memos config show
memos auth status
```

For headless environments, both can be supplied via env vars:

```bash
export MEMOS_URL=https://memos.example.com
export MEMOS_TOKEN=...
```

## Commands

### memo

```
memos memo list [--filter EXPR] [--page-size N] [--page-token T] [--pretty]
memos memo get <name> [--pretty]
memos memo create [--content STR | stdin] [--visibility V] [--pretty]
memos memo update <name> [--content STR | stdin] [--visibility V]
memos memo delete <name>
```

`--filter` accepts the usememos CEL filter expression as-is.

`update` replaces the entire body — a stderr warning is printed every time.

### attachment

```
memos attachment upload <file> [--pretty]
memos attachment list [--memo NAME] [--pretty]
memos attachment get <name> [--pretty]
memos attachment download <name> [--output PATH | -]
memos attachment delete <name>
```

`get` returns metadata (JSON). To fetch the file bytes, use `download` — without `--output`, the original filename is written to the current directory; with `--output -`, the bytes are streamed to stdout.

### user

```
memos user list [--pretty]
memos user get <id|me> [--pretty]
```

`user get me` falls back to `/api/v1/auth/sessions/current` on servers where `/users/me` is unavailable.

### config

```
memos config show           # resolved URL + token location (value masked)
memos config path           # config.toml path
memos config edit           # open in $EDITOR
```

### auth

```
memos auth login            # prompt for token, store in keyring
memos auth logout           # remove from keyring
memos auth status           # show storage location (never the value)
```

## Name handling

usememos resource names look like `{collection}/{id}` — `memos/abc123`, `attachments/xyz`, `users/3`. The CLI accepts either the canonical form or the raw id; raw ids are prefixed with the surrounding command's collection. Names containing a slash are never rewritten, so `memos attachment get memos/x` will not silently be turned into `attachments/memos/x`.

## Output

- Default: JSON on stdout.
- `--pretty`: tab-separated summary suitable for human reading.
- Errors: one line on stderr, non-zero exit code.

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | General error (network, server) |
| 2 | Usage error |
| 3 | Authentication failed (token missing/expired) |
| 4 | Permission denied (403) |
| 5 | Not found (404) |

## Security

- Token is never printed to stdout, stderr, or logs.
- `Authorization` header is masked in any request logging.
- A `token` key in `config.toml` is ignored with a stderr warning — use `memos auth login` instead.
- `update`/`delete` reject empty stdin to prevent accidental destruction.

## License

MIT
