from typing import Literal

import httpx
import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


class PluginReportResult(BaseModel):
    """Result returned by public plugin reporting tools."""

    status: Literal["submitted", "failed"]
    message: str


async def _submit(
    path: str,
    payload: dict[str, object],
    ctx: Context[ServerSession, AppContext],
) -> PluginReportResult:
    http = ctx.request_context.lifespan_context.http
    try:
        response = await http.post(path, json=payload)
        data = response.json()
        if response.is_success and data.get("status") == "submitted":
            await ctx.info(data.get("message", "event submitted"))
            return PluginReportResult(status="submitted", message="event submitted")

        message = str(data.get("message", "usage service rejected event"))
        await ctx.error(message)
        return PluginReportResult(status="failed", message=message)
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        _log.info("plugin_report.failed", path=path, error=str(exc))
        await ctx.error("usage service unavailable")
        return PluginReportResult(status="failed", message="usage service unavailable")


@mcp.tool(name="plugin_report_usage")
async def plugin_report_usage(
    skill_name: str,
    plugin_version: str,
    installation_id: str,
    ctx: Context[ServerSession, AppContext],
) -> PluginReportResult:
    """Report anonymous Ailtir plugin skill usage without an MCP API token.

    Args:
        skill_name: Exact Ailtir plugin skill folder name.
        plugin_version: Semantic version of the Ailtir plugin.
        installation_id: Stable anonymous UUID stored by the plugin installation.
    """
    return await _submit(
        "/api-mcp/plugin/usage/",
        {
            "skill_name": skill_name,
            "plugin_version": plugin_version,
            "installation_id": installation_id,
        },
        ctx,
    )


@mcp.tool(name="plugin_feedback")
async def plugin_feedback(
    rating: int,
    plugin_version: str,
    installation_id: str,
    ctx: Context[ServerSession, AppContext],
    reason: str = "",
    workflow_name: str = "",
    workflow_kind: Literal["skill", "plugin", "session"] = "skill",
    followup_answers: dict[str, str] | None = None,
) -> PluginReportResult:
    """Submit anonymous Ailtir plugin feedback without an MCP API token.

    Args:
        rating: Usefulness rating from 1 to 10.
        plugin_version: Semantic version of the Ailtir plugin.
        installation_id: Stable anonymous UUID stored by the plugin installation.
        reason: Optional short reason for the rating; omit sensitive details.
        workflow_name: Optional exact workflow or skill name being rated.
        workflow_kind: Whether feedback applies to a skill, plugin, or session.
        followup_answers: Up to three short structured follow-up answers.
    """
    return await _submit(
        "/api-mcp/plugin/feedback/",
        {
            "rating": rating,
            "plugin_version": plugin_version,
            "installation_id": installation_id,
            "reason": reason,
            "workflow_name": workflow_name,
            "workflow_kind": workflow_kind,
            "followup_answers": followup_answers or {},
        },
        ctx,
    )
