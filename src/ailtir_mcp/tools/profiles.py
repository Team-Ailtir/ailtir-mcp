import json
from typing import Any

import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ailtir_mcp.auth import get_token
from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


@mcp.tool(name="profile_get")
async def profile_get(
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Get the profile for the authenticated user."""
    token = get_token()
    http = ctx.request_context.lifespan_context.http
    resp = await http.get(
        "/api-mcp/profiles/",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    data = resp.json()
    _log.info("profile_get.done")
    return json.dumps(data.get("profile", {}))


@mcp.tool(name="profile_create")
async def profile_create(
    profile: dict[str, Any],
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Create a profile for the authenticated user.

    Args:
        profile: Arbitrary JSON object to store as the profile.
    """
    token = get_token()
    http = ctx.request_context.lifespan_context.http
    resp = await http.post(
        "/api-mcp/profiles/",
        json={"profile": profile},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    _log.info("profile_create.done")
    return "Profile created."


@mcp.tool(name="profile_delete")
async def profile_delete(
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Delete the profile for the authenticated user."""
    token = get_token()
    http = ctx.request_context.lifespan_context.http
    resp = await http.delete(
        "/api-mcp/profiles/",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    _log.info("profile_delete.done")
    return "Profile deleted."
