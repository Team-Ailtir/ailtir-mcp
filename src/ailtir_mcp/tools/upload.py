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

    token = current_token.get()
    http = ctx.request_context.lifespan_context.http
    resp = await http.post(
        "/kb",
        json={"file_name": file_name, "file_content_base64": file_content_base64},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    kb_id: str = resp.json()["kb_id"]

    _log.info("upload.done", kb_id=kb_id)
    await ctx.info(f"Upload complete. kb_id: {kb_id}")
    return kb_id
