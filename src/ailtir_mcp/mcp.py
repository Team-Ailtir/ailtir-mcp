import contextlib
import typing
from dataclasses import dataclass

import httpx
import structlog
from mcp.server.fastmcp import FastMCP

from ailtir_mcp.config import settings

_log = structlog.get_logger(__name__)


@dataclass
class AppContext:
    http: httpx.AsyncClient


@contextlib.asynccontextmanager
async def _lifespan(server: FastMCP) -> typing.AsyncIterator[AppContext]:
    _log.info("ailtir_mcp.starting")
    async with httpx.AsyncClient(base_url=settings.mcp_api_url, timeout=30.0) as http:
        yield AppContext(http=http)
    _log.info("ailtir_mcp.stopped")


mcp: FastMCP = FastMCP("ailtir-mcp", lifespan=_lifespan)
