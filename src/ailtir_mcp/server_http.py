"""HTTP (Streamable HTTP) entrypoint for the ailtir-mcp server."""

import contextlib
import logging
import typing

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import ASGIApp

import ailtir_mcp.tools  # noqa: F401 — registers all tools with mcp instance
from ailtir_mcp.auth import BearerTokenMiddleware
from ailtir_mcp.config import settings
from ailtir_mcp.mcp import mcp


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})


def create_app() -> Starlette:
    mcp_app = mcp.streamable_http_app()

    @contextlib.asynccontextmanager
    async def lifespan(_: ASGIApp) -> typing.AsyncIterator[None]:
        async with mcp.session_manager.run():
            yield

    return Starlette(
        lifespan=lifespan,
        routes=[
            Route(f"{settings.mcp_mount_path}/health", health),
            Mount(settings.mcp_mount_path, mcp_app),
        ],
        middleware=[Middleware(BearerTokenMiddleware)],
    )


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    uvicorn.run(create_app(), host=settings.mcp_host, port=settings.mcp_port)


if __name__ == "__main__":
    main()
