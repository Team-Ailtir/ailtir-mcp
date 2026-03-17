"""FastAPI application and process entrypoint."""

import contextlib
import typing

import alogging
import fastapi
import structlog
import uvicorn

import ailtir_mcp.tools  # noqa: F401 — registers all tools with mcp instance
from ailtir_mcp.auth import BearerAuthMiddleware
from ailtir_mcp.config import settings
from ailtir_mcp.mcp import mcp

_log = structlog.get_logger(__name__)


@contextlib.asynccontextmanager
async def _lifespan(app: fastapi.FastAPI) -> typing.AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


app = fastapi.FastAPI(lifespan=_lifespan, root_path=settings.root_path)
app.add_middleware(BearerAuthMiddleware, verify_url=f"{settings.mcp_api_url}/auth/verify")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/", app=mcp.streamable_http_app())


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
