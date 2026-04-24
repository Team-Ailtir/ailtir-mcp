import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.config import settings
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool(name="list")
async def list_knowledge_bases(
    ctx: Context[ServerSession, AppContext],
) -> str:
    """List all knowledge bases in your Ailtir account."""
    token = settings.ailtir_mcp_api_token
    http = ctx.request_context.lifespan_context.http
    resp = await http.get(
        "/kb",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    kbs = resp.json()
    if not kbs:
        return "No knowledge bases found."

    lines = [
        f"- {kb.get('name', kb['kb_id'])} (id: {kb['kb_id']}, status: {kb['status']})" for kb in kbs
    ]
    _log.info("list_kbs.returned", count=len(kbs))
    return "\n".join(lines)
