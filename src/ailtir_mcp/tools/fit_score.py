from typing import Any

import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


class FitScore(BaseModel):
    """A fit score for one (notice, tenant, profile), as stored by god."""

    id: str
    tenant_id: str
    notice_id: str
    profile_id: str
    total: int
    dimensions: dict[str, Any]
    disqualified: bool
    disqualifier: list[str] = []
    narrative: str = ""
    created_at: str
    modified_at: str


@mcp.tool(name="fit_score_upsert")
async def fit_score_upsert(
    tenant_id: str,
    notice_id: str,
    profile_id: str,
    total: int,
    dimensions: dict[str, Any],
    ctx: Context[ServerSession, AppContext],
    disqualified: bool = False,
    disqualifier: list[str] | None = None,
) -> FitScore:
    """Create or update a deterministic fit score for a notice.

    Idempotent on (notice_id, profile_id): calling this again for the same
    notice/profile pair replaces the score in place rather than duplicating it.

    Args:
        tenant_id: The tenant this score belongs to.
        notice_id: The tender notice being scored.
        profile_id: The tenant fit profile used to compute the score.
        total: Overall fit score, 0-100.
        dimensions: Per-dimension score breakdown as JSON.
        disqualified: Whether the notice is disqualified regardless of score.
        disqualifier: Reasons for disqualification, if any.
    """
    _log.debug(
        "fit_score_upsert.start", tenant_id=tenant_id, notice_id=notice_id, profile_id=profile_id
    )
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.post(
            "/fit-scores",
            json={
                "tenant_id": tenant_id,
                "notice_id": notice_id,
                "profile_id": profile_id,
                "total": total,
                "dimensions": dimensions,
                "disqualified": disqualified,
                "disqualifier": disqualifier or [],
            },
        )
        resp.raise_for_status()

        score = FitScore.model_validate(resp.json())
        _log.info("fit_score_upsert.done", score_id=score.id, total=total)
        return score
    except Exception:
        _log.exception("fit_score_upsert.error")
        raise


@mcp.tool(name="fit_score_list")
async def fit_score_list(
    tenant_id: str,
    profile_id: str,
    ctx: Context[ServerSession, AppContext],
    min_total: int | None = None,
    skip: int = 0,
    take: int = 20,
) -> list[FitScore]:
    """List fit scores for a tenant profile, for a digest or review pass.

    Args:
        tenant_id: The tenant to list scores for.
        profile_id: The fit profile the scores were computed against.
        min_total: Only include scores at or above this total.
        skip: Number of scores to skip, for pagination.
        take: Maximum number of scores to return.
    """
    _log.debug("fit_score_list.start", tenant_id=tenant_id, profile_id=profile_id)
    try:
        god = ctx.request_context.lifespan_context.god
        params: dict[str, str | int] = {
            "tenant_id": tenant_id,
            "profile_id": profile_id,
            "skip": skip,
            "take": take,
        }
        if min_total is not None:
            params["min_total"] = min_total
        resp = await god.get("/fit-scores", params=params)
        resp.raise_for_status()

        scores = [FitScore.model_validate(s) for s in resp.json()]
        _log.info("fit_score_list.done", count=len(scores))
        return scores
    except Exception:
        _log.exception("fit_score_list.error")
        raise


@mcp.tool(name="fit_score_set_narrative")
async def fit_score_set_narrative(
    score_id: str,
    narrative: str,
    ctx: Context[ServerSession, AppContext],
) -> FitScore:
    """Fill in the LLM-authored rationale for a fit score.

    Args:
        score_id: The fit score to update.
        narrative: Human-readable rationale text.
    """
    _log.debug("fit_score_set_narrative.start", score_id=score_id)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.patch(
            f"/fit-scores/{score_id}/narrative",
            json={"narrative": narrative},
        )
        resp.raise_for_status()

        score = FitScore.model_validate(resp.json())
        _log.info("fit_score_set_narrative.done", score_id=score.id)
        return score
    except Exception:
        _log.exception("fit_score_set_narrative.error")
        raise
