import contextlib
import typing
from dataclasses import dataclass
from typing import Any

import boto3
import httpx
import structlog
from mcp.server.fastmcp import FastMCP

from ailtir_mcp.config import settings

_log = structlog.get_logger(__name__)


@dataclass
class AppContext:
    http: httpx.AsyncClient
    s3: Any  # boto3 S3 client


@contextlib.asynccontextmanager
async def _lifespan(server: FastMCP) -> typing.AsyncIterator[AppContext]:
    _log.info("ailtir_mcp.starting")
    async with httpx.AsyncClient(base_url=settings.mcp_api_url, timeout=30.0) as http:
        s3 = boto3.client("s3", region_name=settings.aws_region)
        yield AppContext(http=http, s3=s3)
    _log.info("ailtir_mcp.stopped")


mcp: FastMCP = FastMCP(
    "ailtir-mcp",
    stateless_http=True,
    json_response=True,
    lifespan=_lifespan,
)
