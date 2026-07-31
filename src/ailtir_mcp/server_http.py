"""HTTP (Streamable HTTP) entrypoint for the ailtir-mcp server."""

import uvicorn
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import ASGIApp

import ailtir_mcp.tools  # noqa: F401 — registers all tools with mcp instance
from ailtir_mcp.config import configure_logging, settings
from ailtir_mcp.mcp import mcp


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})


def create_app() -> ASGIApp:
    mcp.settings.streamable_http_path = settings.mcp_mount_path
    mcp._custom_starlette_routes.append(Route(f"{settings.mcp_mount_path}/health", health))
    return mcp.streamable_http_app()


def main() -> None:
    configure_logging()
    uvicorn.run(
        create_app(),
        host=settings.mcp_host,
        port=settings.mcp_port,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
