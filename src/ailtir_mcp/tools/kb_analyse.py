import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import get_token
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool(name="kb_analyse")
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
    _log.debug("kb_analyse.start", kb_id=kb_id)
    await ctx.info(f"Starting analysis for kb_id: {kb_id}")

    try:
        token = get_token()
        http = ctx.request_context.lifespan_context.http
        resp = await http.post(
            f"/api-mcp/kbs/{kb_id}/analyse",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()

        _log.info("kb_analyse.started", kb_id=kb_id)
        return (
            f"Analysis started for kb_id: {kb_id}. "
            "This typically takes a few minutes. Use the list tool to check status."
        )
    except Exception:
        _log.exception("kb_analyse.error", kb_id=kb_id)
        raise
