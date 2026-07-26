import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


class Setting(BaseModel):
    """A key-value setting, as stored by god. Used for ingestion cursors and gates."""

    key: str
    value: str
    created_at: str
    modified_at: str


@mcp.tool(name="setting_get")
async def setting_get(
    key: str,
    ctx: Context[ServerSession, AppContext],
) -> Setting:
    """Read a cursor or gate value by key.

    Args:
        key: The setting key, e.g. "etenders.last_seeded_at".
    """
    _log.debug("setting_get.start", key=key)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.get(f"/settings/{key}")
        resp.raise_for_status()

        setting = Setting.model_validate(resp.json())
        _log.info("setting_get.done", key=key)
        return setting
    except Exception:
        _log.exception("setting_get.error")
        raise


@mcp.tool(name="setting_set")
async def setting_set(
    key: str,
    value: str,
    ctx: Context[ServerSession, AppContext],
) -> Setting:
    """Write a cursor or gate value by key.

    Args:
        key: The setting key, e.g. "etenders.last_seeded_at".
        value: The value to store.
    """
    _log.debug("setting_set.start", key=key)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.put(f"/settings/{key}", json={"value": value})
        resp.raise_for_status()

        setting = Setting.model_validate(resp.json())
        _log.info("setting_set.done", key=key)
        return setting
    except Exception:
        _log.exception("setting_set.error")
        raise
