from typing import Any

import structlog
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

from ailtir_mcp.mcp import AppContext, mcp

_log = structlog.get_logger(__name__)


class PollLog(BaseModel):
    """Fleet telemetry for one ingestion run, as stored by god."""

    id: str
    source: str
    mode: str
    ok: bool
    records_returned: int
    errors: list[dict[str, Any]] = []
    started_at: str
    finished_at: str
    created_at: str


@mcp.tool(name="poll_log_create")
async def poll_log_create(
    source: str,
    mode: str,
    ok: bool,
    records_returned: int,
    started_at: str,
    finished_at: str,
    ctx: Context[ServerSession, AppContext],
    errors: list[dict[str, Any]] | None = None,
) -> PollLog:
    """Record fleet telemetry for one ingestion run.

    Args:
        source: Source polled, e.g. "etenders".
        mode: Run mode, e.g. "incremental" or "backfill".
        ok: Whether the run completed without a fatal error.
        records_returned: Number of records the run returned.
        started_at: Run start timestamp, ISO 8601.
        finished_at: Run end timestamp, ISO 8601.
        errors: Per-item failure summaries. An empty list means no errors,
            not omitted — a partially failed run is still auditable here.
    """
    _log.debug("poll_log_create.start", source=source, mode=mode, ok=ok)
    try:
        god = ctx.request_context.lifespan_context.god
        resp = await god.post(
            "/poll-logs",
            json={
                "source": source,
                "mode": mode,
                "ok": ok,
                "records_returned": records_returned,
                "errors": errors if errors is not None else [],
                "started_at": started_at,
                "finished_at": finished_at,
            },
        )
        resp.raise_for_status()

        log = PollLog.model_validate(resp.json())
        _log.info("poll_log_create.done", log_id=log.id)
        return log
    except Exception:
        _log.exception("poll_log_create.error")
        raise


@mcp.tool(name="poll_log_list")
async def poll_log_list(
    ctx: Context[ServerSession, AppContext],
    source: str | None = None,
    take: int = 10,
) -> list[PollLog]:
    """List recent poll logs, for fleet health monitoring.

    Args:
        source: Filter by source, e.g. "etenders".
        take: Maximum number of logs to return, most recent first.
    """
    _log.debug("poll_log_list.start", source=source, take=take)
    try:
        god = ctx.request_context.lifespan_context.god
        params: dict[str, str | int] = {"take": take}
        if source is not None:
            params["source"] = source
        resp = await god.get("/poll-logs", params=params)
        resp.raise_for_status()

        logs = [PollLog.model_validate(entry) for entry in resp.json()]
        _log.info("poll_log_list.done", count=len(logs))
        return logs
    except Exception:
        _log.exception("poll_log_list.error")
        raise
