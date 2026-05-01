import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import get_token
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool(name="kb_list")
async def list_knowledge_bases(
    ctx: Context[ServerSession, AppContext],
) -> str:
    """List all knowledge bases in your Ailtir account."""
    _log.debug("kb_list.start")

    try:
        token = get_token()
        http = ctx.request_context.lifespan_context.http
        resp = await http.get(
            "/kbs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()

        kbs = resp.json()
        _log.info("kb_list.done", count=len(kbs))
        if not kbs:
            return "No knowledge bases found."

        lines = [
            f"- {kb.get('name', kb['id'])} (id: {kb['id']}, status: {kb['status']})" for kb in kbs
        ]
        return "\n".join(lines)
    except Exception:
        _log.exception("kb_list.error")
        raise
