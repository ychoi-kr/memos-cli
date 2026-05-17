# memos-cli PRD

| | |
|---|---|
| 작성 | 2026-05-18 |
| 상태 | 초안 v0.3 |
| 대상 서버 | usememos v0.25+ |
| 언어/배포 | Python 3.11+, PyPI 패키지 |
| CLI 프레임워크 | typer |

## 1. 개요

memos-cli는 [usememos](https://github.com/usememos/memos) self-hosted 메모 서비스의 **얇은 명령행 클라이언트**입니다. usememos REST API와 1:1로 대응하는 서브커맨드를 제공하며, 셸·플랫폼별 의존성(jq, base64, heredoc, 인코딩)·자격증명 보관 같은 보일러플레이트만 처리합니다. 워크플로 컨벤션(태그 규약, 본문 포맷, 첨부 후 본문 합성 같은 패턴)은 의도적으로 제외하고 사용자/스킬 쪽에 남깁니다.

## 2. 동기

usememos는 풍부한 REST API를 제공하지만, 현재 공개된 CLI 후보들은 모두 사망(themagiulio archived) 또는 기능 부족(paulvandermeijs는 post/list만, vinicius507는 삭제됨)입니다. 한편 `curl` + `jq` 직접 사용은 셸/플랫폼별로 깨지고(UTF-8, 따옴표, base64), 자격증명을 평문 셸 명령에 노출시키는 보안 문제도 있습니다.

memos-cli는 이 두 격차만 메웁니다.

## 3. 범위

### 3.1 In scope

- usememos REST API(v0.25+)의 주요 엔드포인트를 자원·동사 형태로 노출
- 자격증명 안전 보관: 토큰 keyring, URL 평문 config.toml, env fallback
- 머신·환경 독립(macOS·Windows·Linux × bash·zsh·PowerShell)
- 인코딩(UTF-8) 및 첨부 업로드(base64 JSON body) 내부 처리
- JSON 기본 출력, `--pretty` 옵션으로 표/사람 친화 출력

### 3.2 Out of scope (사용자/스킬이 결정)

- 태그 컨벤션(`#스킬/...`, `#sysadmin/...` 같은 규약)
- 본문 포맷(제목 줄, 태그 줄, 푸터 포맷)
- 머신 ↔ 사용자 ID 매핑·머신 필터
- 첨부 업로드 후 본문에 자동 링크 삽입 같은 다단계 합성
- 세션 ID 통합
- visibility 기본값 변경(API 기본 `PRIVATE` 그대로 둠)

위 항목들이 필요한 경우 사용자가 SKILL.md 또는 셸 스크립트로 memos-cli 호출을 합성합니다.

## 4. 명령 구조

자원(resource) · 동사 형태. API 엔드포인트에 1:1로 매핑.

### 4.1 `memo`

| 명령 | API |
|---|---|
| `memos memo list [--filter EXPR] [--page-size N] [--page-token T]` | `GET /api/v1/memos` |
| `memos memo get <name>` | `GET /api/v1/memos/{name}` |
| `memos memo create [--content STR \| stdin] [--visibility V]` | `POST /api/v1/memos` |
| `memos memo update <name> [--content STR \| stdin] [--visibility V]` | `PATCH /api/v1/memos/{name}` |
| `memos memo delete <name>` | `DELETE /api/v1/memos/{name}` |

- `update`는 본문 **전체 교체**입니다. stderr에 한 줄 경고를 매번 출력합니다("update replaces the entire body").
- `--filter`는 usememos의 [CEL 필터 표현식](https://github.com/usememos/memos/blob/main/docs/api/filter.md)을 그대로 받습니다.

### 4.2 `attachment`

| 명령 | API |
|---|---|
| `memos attachment upload <file>` | `POST /api/v1/attachments` |
| `memos attachment list [--memo NAME]` | `GET /api/v1/attachments` |
| `memos attachment get <name>` | `GET /api/v1/attachments/{name}` (메타데이터) |
| `memos attachment download <name> [--output PATH \| -]` | `GET /file/attachments/{uid}/{filename}` (콘텐츠) |
| `memos attachment delete <name>` | `DELETE /api/v1/attachments/{name}` |

`get`은 메타데이터(JSON)만 반환합니다. 실제 파일 바이트를 받으려면 `download`를 사용합니다. `--output`을 생략하면 원본 `filename`을 현재 디렉터리에 저장하고, `-`을 주면 stdout으로 출력합니다(파이프 가능).

`upload`는 응답에서 `name`(예: `attachments/xxxx`)과 `filename`을 JSON으로 반환합니다. 사용자가 본문에 링크를 박을지 여부는 호출자가 결정합니다.

### 4.3 `user`

| 명령 | API |
|---|---|
| `memos user list` | `GET /api/v1/users` |
| `memos user get <id\|me>` | `GET /api/v1/users/{id}` (또는 `/users/me`) |

`me`는 v0.25에서 `/users/me`가 404를 반환하는 환경이 있습니다. 그 경우 `/api/v1/auth/sessions/current`의 `user` 필드를 추출하는 fallback을 내부 처리합니다.

### 4.4 `config`

| 명령 | 기능 |
|---|---|
| `memos config show` | 현재 해석된 URL·user 출력(토큰은 마스킹) |
| `memos config path` | config.toml 파일 경로 출력 |
| `memos config edit` | `$EDITOR`로 config.toml 열기 |

### 4.5 `auth`

| 명령 | 기능 |
|---|---|
| `memos auth login` | 토큰 입력 프롬프트(getpass) → keyring 저장 |
| `memos auth logout` | keyring에서 토큰 삭제 |
| `memos auth status` | 토큰 보관 위치(keyring/env/없음) 출력. 값은 출력하지 않음 |

### 4.6 이름 입력 규칙

usememos REST API는 `{collection}/{id}` 형태의 자원 이름을 사용합니다(`memos/abc123`, `attachments/xyz`, `users/3`). CLI는 두 가지 입력을 모두 받습니다.

| 입력 | 해석 |
|---|---|
| `memos/abc123` | 정규형 — 그대로 사용 |
| `abc123` | 컨텍스트 자원에 맞춰 `{prefix}/abc123`로 보정 |
| `attachments/xyz` (memo 명령에 입력 등 다른 prefix) | 슬래시가 포함돼 있으면 보정하지 않고 그대로 전달 — 잘못 입력하면 404 |

각 명령은 자신이 다루는 자원에 한해 raw id를 받아 prefix를 자동으로 붙입니다. 슬래시가 포함된 입력은 사용자가 의도적으로 지정한 것으로 보고 절대 재작성하지 않습니다.

## 5. 자격증명 및 설정

### 5.1 분리 원칙

| 종류 | 보관 위치 | 권한 |
|---|---|---|
| 토큰(비밀) | OS 키링(macOS Keychain / Windows Credential Manager / Linux Secret Service) | OS 보호 |
| URL(비밀 아닌 구성) | `~/.config/memos/config.toml` (XDG) | 0644 평문 |
| headless fallback | `MEMOS_TOKEN` / `MEMOS_URL` env | `~/.profile`에 export + `chmod 600` |

### 5.2 config.toml 구조

```toml
url = "https://memos.example.com"
```

추가 키는 받지 않습니다(thin 원칙). 머신 ID·기본 visibility 같은 사용자 컨벤션은 환경변수 또는 셸 alias로 처리.

### 5.3 조회 우선순위

```
token: keyring("memos","token") → MEMOS_TOKEN → 종료(1)
url:   config.toml.url → MEMOS_URL → 종료(1)
```

### 5.4 config.toml 자동 생성

`memos <subcmd>` 첫 호출 시 config.toml이 없는데 `MEMOS_URL` env가 있으면 자동 생성하고 stderr에 한 줄 안내. 이후 호출은 파일 경로로 일관.

→ 호출자가 셸로 URL을 파일에 적을 필요 없음. 사용자가 인터랙티브 셸에서 한 번만 호출하면 마이그레이션 완료.

## 6. 출력 규약

- 기본: `--pretty` 없을 때 JSON(stdout)
- `--pretty`: 사람용 표·요약 출력
- 모든 비정상 종료는 stderr에 한 줄 사유 출력, 종료 코드 비0

| 종료 코드 | 의미 |
|---|---|
| 0 | 성공 |
| 1 | 일반 오류(네트워크·서버) |
| 2 | 사용법 오류(인자·stdin 부족) |
| 3 | 인증 실패(토큰 만료·미설정) |
| 4 | 권한 거부(403) |
| 5 | 자원 없음(404) |

## 7. 안전 규칙

- 토큰을 stdout/stderr·로그에 **0회** 출력. `--debug`도 마스킹 유지.
- API 요청 로그 시 `Authorization` 헤더 마스킹.
- `update`/`delete` 호출 시 본문이 빈 stdin이면 거부(실수 방지).
- `update`는 매번 stderr에 전체 교체 경고 한 줄(이전 사용 중 부분 수정 오해로 본문이 손실된 사례 있음).
- config.toml에 `token`이 적혀 있으면 stderr 경고 후 무시(평문 토큰 차단).

## 8. 비기능 요구사항

- Python 3.11+ (tomllib 표준 사용)
- CLI 프레임워크: `typer` (click·rich·shellingham 전이 의존성 포함)
- 의존성: `requests`, `keyring`, `typer`
- 콜드 스타트 < 500ms (Apple Silicon 측정 ~150ms)
- 셸 비의존: bash·zsh·PowerShell·fish 어디서나 동일
- 인코딩: UTF-8, BOM 미허용

## 9. 패키지 구조

```
memos-cli/
├── pyproject.toml
├── README.md
├── PRD.md
├── LICENSE                ← MIT
├── memos_cli/
│   ├── __init__.py
│   ├── __main__.py        ← entry point
│   ├── cli.py             ← typer 앱 + 서브커맨드 디스패치
│   ├── api.py             ← REST 클라이언트
│   ├── creds.py           ← keyring + config.toml + env
│   ├── output.py          ← JSON / pretty
│   └── resources/
│       ├── memo.py
│       ├── attachment.py
│       ├── user.py
│       ├── config.py
│       └── auth.py
└── tests/
```

`pyproject.toml`:

```toml
[project]
name = "memos-cli"
version = "0.1.0"
description = "Thin CLI for usememos self-hosted memo service"
requires-python = ">=3.11"
dependencies = ["requests>=2.31", "keyring>=24.0", "typer>=0.12"]

[project.scripts]
memos = "memos_cli.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

설치:

```bash
uv tool install memos-cli      # 권장
# 또는
pip install --user memos-cli
```

## 10. 마일스톤

| 버전 | 내용 |
|---|---|
| v0.1 | memo·attachment·user·config·auth 기본 CRUD. 단일 머신 동작 확인 |
| v0.2 | 다중 머신 배포. 사용자 측 SKILL.md·셸 alias를 memos-cli 호출 + 사용자 워크플로 컨벤션만 남기도록 슬림화 |
| v0.3 | pytest 단위 테스트, GitHub Actions CI |
| v1.0 | usememos v0.26 호환 확인, README 완성, 콜드 스타트 측정, PyPI 공개 검토 |

## 11. 미정 사항

| 항목 | 시점 |
|---|---|
| GitHub 리포 public/private | v0.2 직전 |
| 출력 색상(rich 도입 여부) | v0.3 |
| `--filter` 외 `--keyword`·`--tag` 같은 편의 플래그 추가 여부 | 사용 후 판단 |
| MCP 서버 wrapper 별도 제공 여부 | v1.0 이후 |

## 12. 사용자 워크플로 위임의 예

CLI가 직접 처리하지 않는 합성을 사용자 측에서 처리하는 예. SKILL.md 또는 셸 alias로 두기 좋습니다.

### 12.1 첨부 + 본문에 마크다운 링크 삽입

```bash
upload=$(memos attachment upload "$file")
uid=$(echo "$upload" | jq -r '.name | split("/")[1]')
fname=$(echo "$upload" | jq -r '.filename')
body+=$'\n\n['"$fname"'](/file/attachments/'"$uid"'/'"$fname"')'
echo "$body" | memos memo create --visibility PROTECTED
```

### 12.2 머신 이름 → 사용자 ID 매핑 후 필터

```bash
# 사용자 SKILL.md 또는 셸 alias에 매핑 표 보관
declare -A MACHINES=([host-a]=users/3 [host-b]=users/4 [host-c]=users/5)
memos memo list --filter "creator == '${MACHINES[host-c]}'" --pretty
```

### 12.3 본문 푸터에 세션 ID 자동 추가

```bash
session=$(cat ~/.claude/sessions/$(ls -t ~/.claude/sessions | head -1) | jq -r .sessionId)
echo -e "$body\n\n세션: $session" | memos memo create
```

이런 합성은 사용자가 자신의 사용 패턴에 맞춰 정의합니다 — memos-cli는 단지 그 부품을 제공합니다.

## 13. 참고

- usememos: <https://github.com/usememos/memos>
- usememos API v1: <https://github.com/usememos/memos/tree/main/api/v1>
- 사망/기능 부족 선행 CLI: paulvandermeijs/memos-cli(Rust, post+list만), themagiulio/memos-cli(Python, 2024-04-27 archived)
