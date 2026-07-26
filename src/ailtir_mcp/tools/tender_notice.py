from typing import Any

import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


class TenderNotice(BaseModel):
    """A canonical tender notice, as stored by god."""

    id: str
    tenant_id: str
    source: str
    resource_id: str
    portal_url: str
    listing: dict[str, Any]
    detail: dict[str, Any] | None = None
    status: str
    classification: dict[str, Any] | None = None
    procurement_type: str | None = None
    authority_name: str | None = None
    cpv_codes: list[str] = []
    deadline: str | None = None
    published_at: str | None = None
    created_at: str
    modified_at: str


@mcp.tool(name="tender_notice_upsert")
async def tender_notice_upsert(
    tenant_id: str,
    source: str,
    resource_id: str,
    portal_url: str,
    listing: dict[str, Any],
    ctx: Context[ServerSession, AppContext],
    detail: dict[str, Any] | None = None,
    authority_name: str | None = None,
    cpv_codes: list[str] | None = None,
    procurement_type: str | None = None,
    deadline: str | None = None,
    published_at: str | None = None,
) -> TenderNotice:
    """Create or update a tender notice in god.

    Idempotent on (source, resource_id): calling this again for the same
    notice updates it in place rather than creating a duplicate.

    Args:
        tenant_id: The tenant this notice belongs to.
        source: Notice source, e.g. "etenders".
        resource_id: The source's own identifier for this notice.
        portal_url: Public URL of the notice on the source portal.
        listing: Raw listing payload as JSON.
        detail: Raw detail-page payload as JSON, once fetched.
        authority_name: Contracting authority name.
        cpv_codes: CPV classification codes for the notice.
        procurement_type: Procurement type/category, e.g. "open".
        deadline: Submission deadline, ISO 8601.
        published_at: Original publication timestamp, ISO 8601.
    """
    _log.debug(
        "tender_notice_upsert.start", tenant_id=tenant_id, source=source, resource_id=resource_id
    )
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.post(
            "/tender-notices",
            json={
                "tenant_id": tenant_id,
                "source": source,
                "resource_id": resource_id,
                "portal_url": portal_url,
                "listing": listing,
                "detail": detail,
                "authority_name": authority_name,
                "cpv_codes": cpv_codes,
                "procurement_type": procurement_type,
                "deadline": deadline,
                "published_at": published_at,
            },
        )
        resp.raise_for_status()

        notice = TenderNotice.model_validate(resp.json())
        _log.info("tender_notice_upsert.done", notice_id=notice.id)
        return notice
    except Exception:
        _log.exception("tender_notice_upsert.error")
        raise


@mcp.tool(name="tender_notice_classify")
async def tender_notice_classify(
    notice_id: str,
    classification: dict[str, Any],
    ctx: Context[ServerSession, AppContext],
) -> TenderNotice:
    """Store the LLM classification result for a tender notice.

    Args:
        notice_id: The tender notice to classify.
        classification: Classification payload, e.g. {sector, region,
            engagement, cpv_codes}. Set {"failed": true} on a classification
            failure so scoring can degrade gracefully.
    """
    _log.debug("tender_notice_classify.start", notice_id=notice_id)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.patch(
            f"/tender-notices/{notice_id}/classification",
            json={"classification": classification},
        )
        resp.raise_for_status()

        notice = TenderNotice.model_validate(resp.json())
        _log.info("tender_notice_classify.done", notice_id=notice.id)
        return notice
    except Exception:
        _log.exception("tender_notice_classify.error")
        raise


@mcp.tool(name="tender_notice_list")
async def tender_notice_list(
    tenant_id: str,
    ctx: Context[ServerSession, AppContext],
    status: str | None = None,
    deadline_after: str | None = None,
    skip: int = 0,
    take: int = 20,
) -> list[TenderNotice]:
    """List tender notices for a tenant, for a scoring or review pass.

    Args:
        tenant_id: The tenant to list notices for.
        status: Filter by lifecycle status, e.g. "new", "classified", "scored".
        deadline_after: Only include notices with a deadline at or after this
            ISO 8601 timestamp.
        skip: Number of notices to skip, for pagination.
        take: Maximum number of notices to return.
    """
    _log.debug("tender_notice_list.start", tenant_id=tenant_id, status=status)
    try:
        god = ctx.request_context.lifespan_context.god
        params: dict[str, str | int] = {"tenant_id": tenant_id, "skip": skip, "take": take}
        if status is not None:
            params["status"] = status
        if deadline_after is not None:
            params["deadline_after"] = deadline_after
        resp = await god.get("/tender-notices", params=params)
        resp.raise_for_status()

        notices = [TenderNotice.model_validate(n) for n in resp.json()]
        _log.info("tender_notice_list.done", count=len(notices))
        return notices
    except Exception:
        _log.exception("tender_notice_list.error")
        raise


@mcp.tool(name="tender_notice_get")
async def tender_notice_get(
    notice_id: str,
    ctx: Context[ServerSession, AppContext],
) -> TenderNotice:
    """Get a single tender notice by id.

    Args:
        notice_id: The tender notice to fetch.
    """
    _log.debug("tender_notice_get.start", notice_id=notice_id)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.get(f"/tender-notices/{notice_id}")
        resp.raise_for_status()

        notice = TenderNotice.model_validate(resp.json())
        _log.info("tender_notice_get.done", notice_id=notice.id)
        return notice
    except Exception:
        _log.exception("tender_notice_get.error")
        raise
