import base64

import httpx
import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import current_token
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool()
async def upload(
    file_name: str,
    file_content_base64: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Upload a ZIP archive of documents to Ailtir storage.

    Args:
        file_name: Name of the ZIP file, e.g. 'tender_docs.zip'.
        file_content_base64: Base64-encoded content of the ZIP file.
    """
    await ctx.info(f"Uploading {file_name}")

    try:
        content = base64.b64decode(file_content_base64, validate=True)
    except Exception:
        return "Error: file_content_base64 is not valid base64."

    # Register with mcp-api to get a server-assigned kb_id and presigned upload URL.
    token = current_token.get()
    http = ctx.request_context.lifespan_context.http
    reg_resp = await http.post(
        "/kb",
        json={"file_name": file_name},
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
