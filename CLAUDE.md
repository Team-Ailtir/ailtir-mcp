# ailtir-mcp — Developer Guide

The Ailtir MCP server. For user-facing installation and tool docs, see the
[README][readme].

## Architecture

`ailtir-mcp` is a **stdio MCP server** built with FastMCP. It runs as a local
process inside the MCP client (Claude Code, Claude Desktop) and delegates all
business logic to [mcp-api][] over REST, passing the user's `AILTIR_MCP_SECRET`
as a bearer token on every request.

```
MCP client  →  ailtir-mcp (stdio, FastMCP)  →  mcp-api  →  pgqueue
```

## Tech Stack

| Dependency | Purpose |
|------------|---------|
| `mcp[cli]` >= 1.9.0 | `FastMCP`, stdio transport |
| `httpx` | HTTP client for mcp-api calls (shared via `AppContext`) and S3 presigned uploads |
| `pydantic-settings` | `Settings` from env vars |
| `structlog` | Structured logging |

Python 3.13+.

## Project Structure

```
ailtir-mcp/
├── pyproject.toml
├── Makefile
├── src/
│   └── ailtir_mcp/
│       ├── __init__.py
│       ├── config.py        # pydantic-settings Settings
│       ├── mcp.py           # FastMCP instance + AppContext dataclass + lifespan
│       ├── server.py        # stdio entrypoint (mcp.run())
│       └── tools/
│           ├── __init__.py  # imports all tools to register them with mcp
│           ├── upload.py    # upload tool
│           ├── analyse.py   # analyse tool
│           ├── list_kbs.py  # list tool (tool name: "list")
│           ├── chat.py      # chat tool
│           └── version.py   # version tool
└── tests/
    └── unit/
        ├── conftest.py      # mock_ctx, app_context fixtures
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

mcp = FastMCP("ailtir-mcp", lifespan=_lifespan)
```

**`src/ailtir_mcp/server.py`** — stdio entrypoint:

```python
def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    mcp.run()
```

## Authentication

`AILTIR_MCP_SECRET` is a per-user bearer token. Tools read it directly from
`settings.ailtir_mcp_secret` and include it as an `Authorization: Bearer`
header on every mcp-api request. Validation happens inside mcp-api.

## Upload Flow

The `upload` tool uses a **register-first** pattern to get a server-assigned
`kb_id` whose path matches the AiltirDB record:

1. `POST /kb` on mcp-api with `{file_name}` → get `{kb_id, upload_url}` (presigned S3 URL)
2. PUT ZIP bytes directly to the presigned `upload_url` via httpx (no AWS credentials needed)
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
- Get the token: `token = settings.ailtir_mcp_secret`
- Get the http client: `ctx.request_context.lifespan_context.http`
- Return `str` for simple results. Use a `pydantic.BaseModel` subclass for structured output.
- Call `resp.raise_for_status()` on mcp-api responses; the SDK catches the exception
  and returns it to the client as `isError: true`.

## Local Development

```bash
make install-dev       # uv sync --group dev
AILTIR_MCP_SECRET=your-secret make serve  # run server over stdio
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

Use `respx` to mock httpx calls. The `autouse` `set_current_token` fixture
patches `settings.ailtir_mcp_secret` to `"test-token-abc123"` for every test.

## Config

All settings are read from environment variables (no `.env` file in production).

| Variable | Default | Description |
|----------|---------|-------------|
| `AILTIR_MCP_SECRET` | *(required)* | Per-user bearer token for mcp-api auth |
| `MCP_API_URL` | `https://app.ailtir.ai/mcp-api` | mcp-api base URL |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` |
| `LOG_FORMAT` | `console` | `console` (dev) / `json` (prod) |

## Deployment

- **Transport**: stdio — runs as a subprocess of the MCP client
- **Entrypoint**: `uvx ailtir-mcp` (or `ailtir-mcp` if installed with `uv tool install`)
- **Auth**: `AILTIR_MCP_SECRET` env var must be set; passed to mcp-api as a bearer token

[readme]: README.md
[mcp-api]: ../mcp-api/README.md
