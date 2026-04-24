import pathlib

import httpx
import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.config import settings
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool()
async def upload(
    file_path: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Upload a ZIP archive of documents to Ailtir storage.

    Args:
        file_path: Absolute path to the ZIP file to upload.
    """
    path = pathlib.Path(file_path)
    if not path.is_absolute():
        return "Error: file_path must be an absolute path."
    if not path.exists():
        return f"Error: file not found: {file_path}"
    if not path.is_file():
        return f"Error: not a file: {file_path}"

    await ctx.info(f"Uploading {path.name}")

    content = path.read_bytes()
    token = settings.ailtir_mcp_api_token
    http = ctx.request_context.lifespan_context.http

    reg_resp = await http.post(
        "/kb",
        json={"file_name": path.name},
        headers={"Authorization": f"Bearer {token}"},
    )
    reg_resp.raise_for_status()
    reg = reg_resp.json()
    kb_id: str = reg["kb_id"]
    upload_url: str = reg["upload_url"]

    # PUT directly to S3 via the presigned URL — no auth header, S3 auth is in the URL.
    async with httpx.AsyncClient(timeout=None) as s3_client:  # noqa: S113
        s3_resp = await s3_client.put(
            upload_url,
            content=content,
            headers={"Content-Type": "application/zip"},
        )
        s3_resp.raise_for_status()

    _log.info("upload.done", kb_id=kb_id)
    await ctx.info(f"Upload complete. kb_id: {kb_id}")
    return kb_id
