import contextlib
import typing
from dataclasses import dataclass

import httpx
import structlog
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from ailtir_mcp.config import settings

_log = structlog.get_logger(__name__)


@dataclass
class AppContext:
    http: httpx.AsyncClient


@contextlib.asynccontextmanager
async def _lifespan(server: FastMCP) -> typing.AsyncIterator[AppContext]:
    _log.info(
        "ailtir_mcp.starting",
        api_mcp_url=settings.api_mcp_url,
        mcp_mount_path=settings.mcp_mount_path,
        log_level=settings.log_level,
    )
    async with httpx.AsyncClient(base_url=settings.api_mcp_url, timeout=30.0) as http:
        yield AppContext(http=http)
    _log.info("ailtir_mcp.stopped")


# Disable DNS rebinding protection — the server runs behind the AWS ALB which
# forwards requests with the public Host header (app.ailtir.ai).
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp: FastMCP = FastMCP(
    "ailtir-mcp",
    lifespan=_lifespan,
    transport_security=_transport_security,
)
