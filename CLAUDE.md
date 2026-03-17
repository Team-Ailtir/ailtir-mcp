# ailtir-mcp — Developer Guide

The Ailtir MCP server. For user-facing installation and tool docs, see the
[README][readme].

## Architecture

`ailtir-mcp` is a **hosted Streamable HTTP MCP server** (protocol version
`2025-06-18`). It authenticates callers via a per-user `AILTIR_MCP_SECRET`
bearer token, then delegates all business logic to [mcp-api][] over REST.

```
MCP client  →  ailtir-mcp (Starlette + FastMCP)  →  mcp-api  →  pgqueue
```

The server is stateless (`stateless_http=True`) and runs on ECS behind a load
balancer — any node can handle any request.

## Tech Stack

| Dependency | Purpose |
|------------|---------|
| `mcp[cli]` >= 1.9.0 | `FastMCP`, Streamable HTTP transport |
| `starlette` | ASGI host; mounts MCP app + `/health` + auth middleware |
| `uvicorn` | ASGI server |
| `httpx` | HTTP client for mcp-api calls (shared via `AppContext`) |
| `boto3` | Direct S3 upload in the `upload` tool |
| `anyio` | `to_thread.run_sync` wrapper for boto3 (sync → async) |
| `pydantic-settings` | `Settings` from env / `.env` file |
| `alogging` | Structured logging (consistent with Ailtir services) |

Python 3.13+.

## Project Structure

```
ailtir-mcp/
├── pyproject.toml
├── .env.example
├── Dockerfile
├── Makefile
├── src/
│   └── ailtir_mcp/
│       ├── __init__.py
│       ├── config.py        # pydantic-settings Settings
│       ├── auth.py          # BearerAuthMiddleware + current_token ContextVar
│       ├── mcp.py           # FastMCP instance + AppContext dataclass + lifespan
│       ├── server.py        # Starlette app + uvicorn entrypoint
│       └── tools/
│           ├── __init__.py  # imports all tools to register them with mcp
│           ├── upload.py    # upload tool
│           ├── analyse.py   # analyse tool
│           ├── list_kbs.py  # list tool (tool name: "list")
│           └── chat.py      # chat tool
└── tests/
    └── unit/
        ├── conftest.py      # mock_ctx, app_context, set_current_token fixtures
        ├── test_auth.py
        ├── test_upload.py
        ├── test_analyse.py
        ├── test_list_kbs.py
        └── test_chat.py
```

Keep files under 400 lines; test files under 800 lines.

## Key Files

**`src/ailtir_mcp/mcp.py`** — the FastMCP instance and `AppContext`:

```python
@dataclass
class AppContext:
    http: httpx.AsyncClient  # shared client for mcp-api calls
    s3: Any                  # boto3 S3 client

mcp = FastMCP("ailtir-mcp", stateless_http=True, json_response=True, lifespan=_lifespan)
```

**`src/ailtir_mcp/server.py`** — Starlette app wiring:

```python
app = Starlette(
    routes=[Route("/health", _health), Mount("/", app=mcp.streamable_http_app())],
    middleware=[Middleware(BearerAuthMiddleware, verify_url=f"{settings.mcp_api_url}/auth/verify")],
    lifespan=_lifespan,  # runs mcp.session_manager.run()
)
```

The MCP endpoint is at `/mcp` (FastMCP default).

## Authentication

`AILTIR_MCP_SECRET` is a per-user bearer token validated by calling
`GET /auth/verify` on mcp-api. The middleware stores the validated token in a
`ContextVar` so tools can include it in their mcp-api calls:

```python
# auth.py
current_token: ContextVar[str] = ContextVar("current_token", default="")

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Check Authorization header
        # 2. Call mcp-api GET /auth/verify
        # 3. On success: current_token.set(token) and call_next(request)
```

Tools read the token with `token = current_token.get()`.

## Upload Flow

The `upload` tool uses a **register-first** pattern to get a server-assigned
`kb_id` whose path matches the AiltirDB record:

1. `POST /kb` on mcp-api with `{file_name}` → get `{kb_id, s3_key}`
2. Upload ZIP bytes to S3 at `s3_key + file_name` using boto3 in a thread
3. Return `kb_id`

Do **not** pre-generate `kb_id` locally — the S3 path format
`kbs/{tenant_id}/{kb_id}/` is owned by mcp-api/knowledge-base service.

## Adding a New Tool

1. Create `src/ailtir_mcp/tools/<name>.py`
2. Import `mcp` from `ailtir_mcp.mcp` and decorate with `@mcp.tool()`
3. Add the import to `src/ailtir_mcp/tools/__init__.py`
4. Add unit tests in `tests/unit/test_<name>.py`

Tool conventions:
- Use `async def`; inject `ctx: Context[ServerSession, AppContext]` as the last parameter.
- Use `await ctx.info/debug/error()` for logging inside tools (sent to MCP client).
- Get the token: `token = current_token.get()`
- Get the http client: `ctx.request_context.lifespan_context.http`
- Get the S3 client: `ctx.request_context.lifespan_context.s3`
- Return `str` for simple results. Use a `pydantic.BaseModel` subclass for structured output.
- Call `resp.raise_for_status()` on mcp-api responses; the SDK catches the exception
  and returns it to the client as `isError: true`.

## Local Development

```bash
cp .env.example .env
make install-dev       # uv sync --group dev
make serve             # python -m ailtir_mcp.server (port 8000)
make inspect           # MCP Inspector via mcp dev
make tests-unit        # pytest with coverage
make checks            # format + lint + type-check + security
```

## Testing

Tool functions are plain `async def` — call them directly with a mocked `ctx`:

```python
# conftest.py provides: mock_ctx, app_context, set_current_token (autouse)

@respx.mock
async def test_chat_success(mock_ctx):
    respx.post("http://test-mcp-api/kb/kb-123/chat").mock(
        return_value=Response(200, json={"answer": "The deadline is 31 March."})
    )
    result = await chat("kb-123", "When?", mock_ctx)
    assert result == "The deadline is 31 March."
```

Use `respx` to mock httpx calls. The `autouse` `set_current_token` fixture sets
`current_token` to `"test-token-abc123"` for every test.

## Config (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_API_URL` | `http://localhost:8001` | mcp-api base URL |
| `AWS_REGION` | `eu-west-1` | AWS region |
| `S3_BUCKET` | `kbs.ailtir.ai` | S3 bucket for ZIP uploads |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` |
| `LOG_FORMAT` | `console` | `console` (dev) / `json` (prod) |

## Deployment

- **Transport**: Streamable HTTP, port `8000`
- **Entrypoint**: `python -m ailtir_mcp.server`
- **Health check**: `GET /health` → `{"status": "ok"}`
- **Auth**: `Authorization: Bearer <AILTIR_MCP_SECRET>` required on all routes except `/health`
- **Stateless**: no sticky sessions needed

[readme]: README.md
[mcp-api]: ../mcp-api/README.md
