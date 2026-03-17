# ailtir-mcp — Developer Guide

The Ailtir MCP server. For user-facing installation and tool docs, see the
[README][readme].

## Architecture

`ailtir-mcp` is a **hosted Streamable HTTP MCP server** (protocol version
`2025-06-18`). It authenticates callers via a per-user `AILTIR_MCP_SECRET`
bearer token, then delegates all business logic to [mcp-api][] over REST.

```
MCP client  →  ailtir-mcp (this repo, Starlette + FastMCP)  →  mcp-api  →  pgqueue
```

The server runs as a stateless, containerized process on ECS behind a load
balancer. No sticky sessions are required.

## Tech Stack

| Dependency | Purpose |
|------------|---------|
| `mcp[cli]` >= 1.26.0 | MCP SDK — `FastMCP`, Streamable HTTP transport |
| `starlette` | ASGI host; mounts MCP app + health route + auth middleware |
| `uvicorn` | ASGI server |
| `httpx` | HTTP client for mcp-api calls |
| `pydantic` | Tool input/output schemas |
| `alogging` | Structured logging (consistent with Ailtir services) |

Python 3.12+.

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
│       ├── server.py        # FastMCP instance, Starlette app, entrypoint
│       ├── auth.py          # BearerAuthMiddleware — validates AILTIR_MCP_SECRET
│       ├── client.py        # httpx client for mcp-api calls
│       └── tools/
│           ├── __init__.py
│           ├── upload.py    # upload tool
│           ├── analyse.py   # analyse tool
│           ├── list_kbs.py  # list tool
│           └── chat.py      # chat tool
└── tests/
    ├── test_tools.py
    └── test_auth.py
```

Keep files under 400 lines; test files under 800 lines.

## Server Setup

Use `FastMCP` in **stateless HTTP mode** — required for multi-node ECS
deployment:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "ailtir-mcp",
    stateless_http=True,   # no per-session state; any node handles any request
    json_response=True,    # return plain JSON; no SSE streams needed for our tools
)
```

Mount into a **Starlette app** to add the `/health` route, CORS headers, and
the auth middleware alongside the MCP endpoint:

```python
import contextlib
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

@contextlib.asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield

async def health(request):
    return JSONResponse({"status": "ok"})

app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    middleware=[Middleware(BearerAuthMiddleware)],
    lifespan=lifespan,
)
```

The MCP endpoint is served at `/mcp` by default (i.e. `https://mcp.ailtir.ai/mcp`).

## Authentication

`AILTIR_MCP_SECRET` is a per-user bearer token issued by mcp-api. It is
**not** OAuth 2.1 — use a custom Starlette middleware, not `TokenVerifier`:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

EXEMPT_PATHS = {"/health"}

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return Response("Unauthorized", status_code=401)
        token = auth.removeprefix("Bearer ")
        if not await verify_secret(token):   # call mcp-api /auth/verify
            return Response("Unauthorized", status_code=401)
        return await call_next(request)
```

Validate the token by calling `mcp-api`'s `/auth/verify` endpoint — the MCP
server holds no secret store of its own.

## Tool Definition Pattern

Use the `@mcp.tool()` decorator. Type hints drive the input schema
automatically; the docstring (including `Args:`) becomes the description shown
to the LLM.

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

@mcp.tool()
async def upload(file_path: str, ctx: Context[ServerSession, None]) -> str:
    """Upload a ZIP archive of documents to Ailtir.

    Args:
        file_path: Absolute path to the local ZIP file.
    """
    await ctx.info(f"Uploading {file_path}")
    # ... call mcp-api ...
    return kb_id
```

Rules:
- Prefer `async` tools; they compose better with `httpx` I/O.
- Always inject `ctx` for logging and progress; use `await ctx.info/debug/error()`.
- Use `await ctx.report_progress(progress, total)` for long-running operations
  like `analyse` (which waits for Bedrock ingestion).
- Return a `pydantic.BaseModel` subclass for structured output; return `str` for
  simple text.
- Do **not** leak internal error details to the LLM — catch exceptions and return
  a clean error string, or let the SDK wrap them with `isError: true`.

## Shared Resources (Lifespan)

Use the lifespan pattern to manage the shared `httpx.AsyncClient` for mcp-api
calls. Do not create a new client per tool call.

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

@dataclass
class AppContext:
    http: httpx.AsyncClient

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    async with httpx.AsyncClient(base_url=MCP_API_URL) as client:
        yield AppContext(http=client)

mcp = FastMCP("ailtir-mcp", lifespan=app_lifespan, ...)

@mcp.tool()
async def list_kbs(ctx: Context[ServerSession, AppContext]) -> list[dict]:
    """List all knowledge bases for this account."""
    client = ctx.request_context.lifespan_context.http
    resp = await client.get("/kb")
    resp.raise_for_status()
    return resp.json()
```

## Security Requirements

Per the MCP specification, HTTP transport servers **must**:

1. Validate the `Origin` header on all incoming requests (DNS rebinding
   protection). In production behind a load balancer / API Gateway this is
   typically handled at the edge; verify the setup.
2. Bind to `127.0.0.1` only when running locally.
3. Use HTTPS in production (enforced by the ECS / ALB setup).

## Logging

Use `alogging` (consistent with all other Ailtir services). Do **not** use
`print()`.

```python
import structlog
log = structlog.get_logger()

log.info("tool.called", tool="upload", file_path=file_path)
```

Additionally, use `await ctx.info/debug/warning/error()` inside tools to send
structured log messages to the MCP client over the protocol.

## Local Development

```bash
cp .env.example .env     # fill AILTIR_MCP_SECRET, MCP_API_URL, etc.
make serve               # uvicorn with hot-reload
make inspect             # launches MCP Inspector at http://localhost:6274
make test                # pytest unit + integration tests
```

`make inspect` runs:
```bash
uv run mcp dev src/ailtir_mcp/server.py
```

The MCP Inspector connects to `http://localhost:8000/mcp` and lets you call
tools interactively without a real MCP client.

## Testing

Test tool functions directly (they are plain async Python functions) for unit
tests. Use the in-process MCP client for integration tests:

```python
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

@pytest.mark.asyncio
async def test_list_kbs():
    async with streamablehttp_client("http://localhost:8000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool("list_kbs", {})
            assert not result.isError
```

## Deployment

- **Transport**: Streamable HTTP on port `8000`
- **Run**: `uvicorn ailtir_mcp.server:app --host 0.0.0.0 --port 8000`
- **Stateless**: any ECS task handles any request (no sticky sessions)
- **Health check**: `GET /health` → `{"status": "ok"}`
- **Auth**: `Authorization: Bearer <AILTIR_MCP_SECRET>` on all requests except
  `/health`

## Backwards Compatibility with Legacy SSE

The deprecated HTTP+SSE transport (protocol version `2024-11-05`) is **not**
supported. All clients must use Streamable HTTP (`2025-06-18`). Claude Desktop
>= 0.10 and Jentic support this.

[readme]: README.md
[mcp-api]: ../mcp-api/README.md
