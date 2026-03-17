import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import current_token
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool()
async def analyse(
    kb_id: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Trigger analysis and Knowledge Base creation for an uploaded ZIP.

    Unzips the archive and builds an AWS Bedrock Knowledge Base from its
    contents. The pipeline runs asynchronously and may take several minutes.

    Args:
        kb_id: The knowledge base ID returned by the upload tool.
    """
    await ctx.info(f"Starting analysis for kb_id: {kb_id}")

    token = current_token.get()
    http = ctx.request_context.lifespan_context.http
    resp = await http.post(
        f"/kb/{kb_id}/analyse",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    _log.info("analyse.started", kb_id=kb_id)
    return (
        f"Analysis started for kb_id: {kb_id}. "
        "This typically takes a few minutes. Use the list tool to check status."
    )
