from typing import Any

import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


class FitConfig(BaseModel):
    """Tenant fit-scoring configuration, as stored on the god profile entity."""

    tenant_id: str
    sector_weights: dict[str, Any] | None = None
    geo_tiers: dict[str, Any] | None = None
    route_prefs: dict[str, Any] | None = None
    engagement: dict[str, Any] | None = None
    score_threshold: int | None = None
    max_concurrent_bids: int | None = None
    fit_threshold: int | None = None
    contact_emails: list[str] = []


@mcp.tool(name="profile_get_fit_config")
async def profile_get_fit_config(
    tenant_id: str,
    ctx: Context[ServerSession, AppContext],
) -> FitConfig:
    """Read the fit-scoring configuration for a tenant's profile.

    Args:
        tenant_id: The tenant whose fit configuration to read.
    """
    _log.debug("profile_get_fit_config.start", tenant_id=tenant_id)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.get(f"/profiles/fit-config/{tenant_id}")
        resp.raise_for_status()

        config = FitConfig.model_validate({"tenant_id": tenant_id, **resp.json()})
        _log.info("profile_get_fit_config.done", tenant_id=tenant_id)
        return config
    except Exception:
        _log.exception("profile_get_fit_config.error")
        raise


@mcp.tool(name="profile_set_fit_config")
async def profile_set_fit_config(
    tenant_id: str,
    ctx: Context[ServerSession, AppContext],
    sector_weights: dict[str, Any] | None = None,
    geo_tiers: dict[str, Any] | None = None,
    route_prefs: dict[str, Any] | None = None,
    engagement: dict[str, Any] | None = None,
    score_threshold: int | None = None,
    max_concurrent_bids: int | None = None,
    fit_threshold: int | None = None,
    contact_emails: list[str] | None = None,
) -> FitConfig:
    """Write the fit-scoring configuration for a tenant's profile.

    Omitted fields leave the corresponding stored value unchanged.

    Args:
        tenant_id: The tenant whose fit configuration to write.
        sector_weights: Sector weighting configuration for scoring.
        geo_tiers: Geographic tier configuration for scoring.
        route_prefs: Route/logistics preference configuration for scoring.
        engagement: Engagement-type gate configuration.
        score_threshold: Minimum total score for a Paperclip task to be created.
        max_concurrent_bids: Maximum number of bids to pursue concurrently.
        fit_threshold: Minimum score below which a notice is disqualified.
        contact_emails: Emails to notify for this tenant's fit-scored notices.
    """
    _log.debug("profile_set_fit_config.start", tenant_id=tenant_id)
    try:
        god = ctx.request_context.lifespan_context.god
        body: dict[str, Any] = {}
        if sector_weights is not None:
            body["sector_weights"] = sector_weights
        if geo_tiers is not None:
            body["geo_tiers"] = geo_tiers
        if route_prefs is not None:
            body["route_prefs"] = route_prefs
        if engagement is not None:
            body["engagement"] = engagement
        if score_threshold is not None:
            body["score_threshold"] = score_threshold
        if max_concurrent_bids is not None:
            body["max_concurrent_bids"] = max_concurrent_bids
        if fit_threshold is not None:
            body["fit_threshold"] = fit_threshold
        if contact_emails is not None:
            body["contact_emails"] = contact_emails

        resp = await god.put(f"/profiles/fit-config/{tenant_id}", json=body)
        resp.raise_for_status()

        config = FitConfig.model_validate({"tenant_id": tenant_id, **resp.json()})
        _log.info("profile_set_fit_config.done", tenant_id=tenant_id)
        return config
    except Exception:
        _log.exception("profile_set_fit_config.error")
        raise
