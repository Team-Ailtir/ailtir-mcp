# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# ailtir-mcp — Developer Guide

The Ailtir MCP server. For user-facing installation and tool docs, see the
[README][readme].

## Architecture

`ailtir-mcp` supports two transports:

- **stdio** — local subprocess of Claude Code/Claude Desktop
- **HTTP (Streamable HTTP)** — remote HTTPS endpoint for LangSmith Fleets and other HTTP-capable MCP clients

Both transports share the same FastMCP instance and tool implementations.

There are two distinct call paths, for two distinct kinds of caller:

```
MCP client (stdio)  →  ailtir-mcp (stdio, FastMCP)  →  api-mcp  →  god   (per-user, AILTIR_MCP_API_TOKEN)
LangSmith Fleets    →  ailtir-mcp (HTTPS, uvicorn)  →  api-mcp  →  god   (per-user, AILTIR_MCP_API_TOKEN)
Paperclip skill (discovery/scoring, no user)        →  ailtir-mcp  →  god   (system, GOD_SERVICE_TOKEN)
```

Per-user tools (profile CRUD, KB upload/analyse/chat/list) go through
`api-mcp`, which resolves the caller's identity from `AILTIR_MCP_API_TOKEN`
and adds `tenant_id`/`user_id` server-side. System/automation tools — the
Phase 0 tender-discovery tools in `tools/tender_notice.py`,
`tools/fit_score.py`, `tools/poll_log.py`, `tools/setting.py`, and
`tools/profile_fit_config.py` — have no logged-in user to resolve, so they
call `god` directly with the shared `GOD_SERVICE_TOKEN`, the same pattern
`god`'s `tenderinfo` handler already used. Any *new* user-invocable tool
should go through `api-mcp`; any new tool called by a scheduled Paperclip
skill should go direct to `god`.

## Tech Stack

| Dependency | Purpose |
|------------|---------|
| `mcp[cli]` >= 1.9.0 | `FastMCP`, stdio and Streamable HTTP transport |
| `httpx` | HTTP client for api-mcp calls (shared via `AppContext`) and S3 presigned uploads |
| `pydantic-settings` | `Settings` from env vars |
| `starlette` >= 0.46.0 | ASGI app for HTTP transport (`BearerTokenMiddleware`, health route) |
| `structlog` | Structured logging |
| `uvicorn` >= 0.34.0 | ASGI server for HTTP transport |

Python 3.13+.

## Project Structure

```
ailtir-mcp/
├── Dockerfile           # Container image for HTTP transport
├── pyproject.toml
├── Makefile
├── src/
│   └── ailtir_mcp/
│       ├── __init__.py
│       ├── auth.py          # get_token(), BearerTokenMiddleware, _bearer_token contextvar
│       ├── config.py        # pydantic-settings Settings
│       ├── mcp.py           # FastMCP instance + AppContext dataclass + lifespan
│       ├── server.py        # stdio entrypoint (mcp.run())
│       ├── server_http.py   # HTTP entrypoint (uvicorn + Starlette + BearerTokenMiddleware)
│       └── tools/
│           ├── __init__.py  # imports all tools to register them with mcp
│           ├── kb_upload.py
│           ├── kb_analyse.py
│           ├── kb_list.py
│           ├── kb_chat.py
│           ├── plugin.py
│           ├── profiles.py
│           ├── tender_notice.py        # system path: tender_notice_upsert/classify/list/get
│           ├── fit_score.py            # system path: fit_score_upsert/list/set_narrative
│           ├── poll_log.py             # system path: poll_log_create/list
│           ├── setting.py              # system path: setting_get/set
│           ├── profile_fit_config.py   # system path: profile_get_fit_config/set_fit_config
│           └── version.py
└── tests/
    └── unit/
        ├── conftest.py           # mock_ctx, app_context fixtures (http + god clients); reset_bearer_token autouse
        ├── test_upload.py
        ├── test_analyse.py
        ├── test_list_kbs.py
        ├── test_chat.py
        ├── test_profiles.py
        ├── test_tender_notice.py
        ├── test_fit_score.py
        ├── test_poll_log.py
        ├── test_setting.py
        ├── test_profile_fit_config.py
        └── test_server_http.py
```

Keep files under 400 lines; test files under 800 lines.

## Key Files

**`src/ailtir_mcp/auth.py`** — token resolution and middleware:

```python
_bearer_token: ContextVar[str | None]  # set per-request by BearerTokenMiddleware

def get_token() -> str:
    # contextvar (HTTP) → settings.ailtir_mcp_api_token (stdio) → ValueError

class BearerTokenMiddleware:
    # Extracts "Authorization: Bearer <token>" and stores it in _bearer_token
```

**`src/ailtir_mcp/mcp.py`** — the FastMCP instance and `AppContext`:

```python
@dataclass
class AppContext:
    http: httpx.AsyncClient  # shared client for api-mcp calls (per-user tools)
    god: httpx.AsyncClient   # shared client for direct god calls (system-path tools),
                             # pre-authenticated with GOD_SERVICE_TOKEN at construction

mcp = FastMCP("ailtir-mcp", lifespan=_lifespan)
```

**`src/ailtir_mcp/server.py`** — stdio entrypoint:

```python
def main() -> None:
    mcp.run()  # stdio transport
```

**`src/ailtir_mcp/server_http.py`** — HTTP entrypoint:

```python
def create_app() -> Starlette:
    # Routes: /{mcp_mount_path}/health + Mount(mcp_mount_path, mcp.streamable_http_app())
    # Middleware: BearerTokenMiddleware

def main() -> None:
    uvicorn.run(create_app(), host=settings.mcp_host, port=settings.mcp_port)
```

## Authentication

Two paths, unified by `get_token()` in `src/ailtir_mcp/auth.py`:

- **stdio**: `AILTIR_MCP_API_TOKEN` env var → `settings.ailtir_mcp_api_token`
- **HTTP**: `Authorization: Bearer <token>` request header → `_bearer_token` contextvar

Each tool calls `get_token()` instead of reading `settings` directly. This means tools
work in both transports with no code duplication.

`plugin_report_usage` and `plugin_feedback` are intentional exceptions: they
call public api-mcp routes without reading or forwarding a bearer token. All
other tools remain authenticated.

## Upload Flow

The `upload` tool uses a **register-first** pattern to get a server-assigned
`kb_id` whose path matches the AiltirDB record:

1. `POST /api-mcp/kbs/` with `{file_name}` → get `{kb_id, upload_url}` (presigned S3 URL)
2. PUT ZIP bytes directly to the presigned `upload_url` via httpx (no AWS credentials needed)
3. Return `kb_id`

Do **not** pre-generate `kb_id` locally — the S3 path format
`kbs/{tenant_id}/{kb_id}/` is owned by api-mcp/god.

## Adding a New Tool

1. Create `src/ailtir_mcp/tools/<name>.py`
2. Import `mcp` from `ailtir_mcp.mcp` and decorate with `@mcp.tool()`
3. Add the import to `src/ailtir_mcp/tools/__init__.py`
4. Add unit tests in `tests/unit/test_<name>.py`

Tool conventions:
- Use `async def`; inject `ctx: Context[ServerSession, AppContext]` as the last parameter.
- Use `await ctx.info/debug/error()` for logging inside tools (sent to MCP client).
- Return `str` for simple results. Use a `pydantic.BaseModel` subclass for structured output.
- Call `resp.raise_for_status()` on responses; the SDK catches the exception
  and returns it to the client as `isError: true`.

For a **per-user** tool (calls `api-mcp`):
- Get the token: `token = get_token()` (import from `ailtir_mcp.auth`)
- Get the http client: `ctx.request_context.lifespan_context.http`
- Pass `headers={"Authorization": f"Bearer {token}"}` on every request.

For a **system-path** tool (calls `god` directly — no logged-in user, e.g. a
scheduled discovery/scoring skill):
- Get the god client: `ctx.request_context.lifespan_context.god` — it is
  already authenticated with `GOD_SERVICE_TOKEN` from `mcp.py`'s lifespan, so
  do not set an `Authorization` header per-request.
- Model the response shape with a `pydantic.BaseModel`, and pass
  `Model.model_validate(resp.json())` rather than hand-parsing the JSON —
  see `tools/tender_notice.py` for the pattern.

## Local Development

```bash
make install-dev       # uv sync --group dev
AILTIR_MCP_API_TOKEN=your-secret make serve       # stdio server
AILTIR_MCP_API_TOKEN=your-secret make serve-http  # HTTP server on :8000/mcp
make inspect           # MCP Inspector via mcp dev
make tests-unit        # pytest with coverage
make checks            # format + lint + type-check + security
make checks-fix        # auto-fix formatting and lint issues
make docker-build      # build Docker image
make docker-run        # run HTTP server container locally
make bump-patch        # bump patch version (also: bump-minor, bump-major)
make release           # commit, tag, push, and publish to PyPI
```

To run a single test:
```bash
uv run pytest tests/unit/test_chat.py::test_chat_success
```

For local HTTP development, `serve-http` sets `MCP_MOUNT_PATH=/mcp` (not `/ailtir-mcp`)
to avoid the ALB prefix. The MCP endpoint is then `http://localhost:8000/mcp`.

## Testing

Tool functions are plain `async def` — call them directly with a mocked `ctx`:

```python
# conftest.py provides: mock_ctx, app_context, reset_bearer_token (autouse)

@respx.mock
async def test_chat_success(mock_ctx):
    respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/chat").mock(
        return_value=Response(200, json={"answer": "The deadline is 31 March."})
    )
    result = await chat("kb-123", "When?", mock_ctx)
    assert result == "The deadline is 31 March."
```

To test the contextvar path (HTTP transport), set `_bearer_token` directly:

```python
from ailtir_mcp.auth import _bearer_token

def test_uses_header_token(mock_ctx):
    _bearer_token.set("my-header-token")
    # ... call tool, assert Authorization header used "my-header-token"
```

The `autouse` `reset_bearer_token` fixture clears `_bearer_token` before every test.

System-path tools use the `mock_god` fixture (also part of `app_context`) instead
of `mock_http`:

```python
@respx.mock
async def test_tender_notice_get_success(mock_ctx):
    respx.get("http://test-god/tender-notices/n1").mock(return_value=Response(200, json=NOTICE))
    result = await tender_notice_get(notice_id="n1", ctx=mock_ctx)
    assert result.id == "n1"
```

## Config

All settings are read from environment variables (no `.env` file in production).

All variables are required (no defaults) except `AILTIR_MCP_API_TOKEN`.

| Variable | Example | Description |
|----------|---------|-------------|
| `AILTIR_MCP_API_TOKEN` | `""` | Per-user bearer token (stdio); not used for HTTP transport |
| `API_MCP_URL` | `https://app.ailtir.ai/api-mcp` | api-mcp base URL |
| `GOD_URL` | `https://god.internal:8000` | god base URL, for system-path tools |
| `GOD_SERVICE_TOKEN` | `""` | Shared service token gating god's system-path write endpoints |
| `MCP_HOST` | `0.0.0.0` | Bind host for HTTP transport |
| `MCP_PORT` | `8000` | Bind port for HTTP transport |
| `MCP_MOUNT_PATH` | `/ailtir-mcp` | URL prefix for HTTP transport (set to `/mcp` locally) |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` |
| `LOG_FORMAT` | `json` | `console` (dev) / `json` (prod) |

## Deployment

### stdio (Claude Code / Claude Desktop)

- **Transport**: stdio — runs as a subprocess of the MCP client
- **Entrypoint**: `uvx ailtir-mcp` (or `ailtir-mcp` if installed with `uv tool install`)
- **Auth**: `AILTIR_MCP_API_TOKEN` env var must be set

### HTTP (LangSmith Fleets / ECS Fargate)

- **Transport**: Streamable HTTP over HTTPS via AWS ALB
- **Entrypoint**: `ailtir-mcp-http` (Docker image, port 8000)
- **MCP endpoint**: `https://app.ailtir.ai/ailtir-mcp`
- **Health check**: `https://app.ailtir.ai/ailtir-mcp/health`
- **Auth**: LangSmith Fleet header `Authorization: Bearer <AILTIR_MCP_API_TOKEN>`
- **Infrastructure**: see `../infrastructure/src/service_ailtir_mcp.py`

[readme]: README.md
[api-mcp]: ../api-mcp/README.md
