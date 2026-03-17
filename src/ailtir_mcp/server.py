"""Starlette application and process entrypoint."""

import contextlib
import typing

import alogging
import structlog
import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

import ailtir_mcp.tools  # noqa: F401 — registers all tools with mcp instance
from ailtir_mcp.auth import BearerAuthMiddleware
from ailtir_mcp.config import settings
from ailtir_mcp.mcp import mcp

_log = structlog.get_logger(__name__)


@contextlib.asynccontextmanager
async def _lifespan(app: Starlette) -> typing.AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


async def _health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/health", _health),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    middleware=[
        Middleware(
            BearerAuthMiddleware,
            verify_url=f"{settings.mcp_api_url}/auth/verify",
        )
    ],
    lifespan=_lifespan,
)


def main() -> None:
    alogging.setup(settings.log_level, settings.log_format)
    _log.info("ailtir_mcp.server.starting", port=8000)
    uvicorn.run(
        "ailtir_mcp.server:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        log_config=None,
    )


if __name__ == "__main__":
    main()
