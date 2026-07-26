from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.poll_log import poll_log_create, poll_log_list

LOG = {
    "id": "l1",
    "source": "etenders",
    "mode": "incremental",
    "ok": True,
    "records_returned": 5,
    "errors": [],
    "started_at": "2026-01-01T00:00:00Z",
    "finished_at": "2026-01-01T00:00:05Z",
    "created_at": "2026-01-01T00:00:05Z",
}


@respx.mock
async def test_poll_log_create_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-god/poll-logs").mock(return_value=Response(201, json=LOG))

    result = await poll_log_create(
        source="etenders",
        mode="incremental",
        ok=True,
        records_returned=5,
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:05Z",
        ctx=mock_ctx,
    )

    assert result.id == "l1"
    assert result.ok is True


@respx.mock
async def test_poll_log_create_sends_empty_errors_default(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-god/poll-logs").mock(return_value=Response(201, json=LOG))

    await poll_log_create(
        source="etenders",
        mode="incremental",
        ok=True,
        records_returned=5,
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:05Z",
        ctx=mock_ctx,
    )

    import json

    body = json.loads(route.calls[0].request.content)
    assert body["errors"] == []


@respx.mock
async def test_poll_log_create_uses_god_service_token(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-god/poll-logs").mock(return_value=Response(201, json=LOG))

    await poll_log_create(
        source="etenders",
        mode="incremental",
        ok=True,
        records_returned=5,
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:05Z",
        ctx=mock_ctx,
    )

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-god-token"


@respx.mock
async def test_poll_log_create_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.post("http://test-god/poll-logs").mock(return_value=Response(400))

    with pytest.raises(httpx.HTTPStatusError):
        await poll_log_create(
            source="etenders",
            mode="incremental",
            ok=False,
            records_returned=0,
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:05Z",
            ctx=mock_ctx,
        )


@respx.mock
async def test_poll_log_list_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/poll-logs").mock(return_value=Response(200, json=[LOG]))

    result = await poll_log_list(ctx=mock_ctx)

    assert len(result) == 1
    assert result[0].source == "etenders"


@respx.mock
async def test_poll_log_list_passes_source_filter(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-god/poll-logs").mock(return_value=Response(200, json=[]))

    await poll_log_list(ctx=mock_ctx, source="ted", take=3)

    request = route.calls[0].request
    assert request.url.params["source"] == "ted"
    assert request.url.params["take"] == "3"
