import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import get_token
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool(name="kb_chat")
async def chat(
    kb_id: str,
    question: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Ask a question answered using documents in a knowledge base (RAG).

    Args:
        kb_id: The knowledge base ID to query.
        question: Your natural-language question.
    """
    await ctx.info(f"Querying kb_id: {kb_id}")

    token = get_token()
    http = ctx.request_context.lifespan_context.http
    resp = await http.post(
        f"/api-mcp/kbs/{kb_id}/chat",
        json={"question": question},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    data = resp.json()
    _log.info("chat.answered", kb_id=kb_id)
    return str(data.get("answer", "No answer returned."))
