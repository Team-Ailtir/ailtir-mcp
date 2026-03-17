import base64
import functools

import anyio
import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import current_token
from ailtir_mcp.config import settings
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
        content = base64.b64decode(file_content_base64)
    except Exception:
        return "Error: file_content_base64 is not valid base64."

    # Register with mcp-api first to get a server-assigned kb_id and S3 key.
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
    s3_key: str = reg["s3_key"] + file_name

    s3 = ctx.request_context.lifespan_context.s3
    await anyio.to_thread.run_sync(
        functools.partial(
            s3.put_object,
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=content,
            ContentType="application/zip",
        )
    )
    _log.info("upload.done", kb_id=kb_id, s3_key=s3_key)
    await ctx.info(f"Upload complete. kb_id: {kb_id}")
    return kb_id
