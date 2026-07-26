from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.fit_score import fit_score_list, fit_score_set_narrative, fit_score_upsert

SCORE = {
    "id": "s1",
    "tenant_id": "t1",
    "notice_id": "n1",
    "profile_id": "p1",
    "total": 80,
    "dimensions": {"sector": 80},
    "disqualified": False,
    "disqualifier": [],
    "narrative": "",
    "created_at": "2026-01-01T00:00:00Z",
    "modified_at": "2026-01-01T00:00:00Z",
}


@respx.mock
async def test_fit_score_upsert_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-god/fit-scores").mock(return_value=Response(200, json=SCORE))

    result = await fit_score_upsert(
        tenant_id="t1",
        notice_id="n1",
        profile_id="p1",
        total=80,
        dimensions={"sector": 80},
        ctx=mock_ctx,
    )

    assert result.id == "s1"
    assert result.total == 80


@respx.mock
async def test_fit_score_upsert_sends_disqualifier_default(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-god/fit-scores").mock(return_value=Response(200, json=SCORE))

    await fit_score_upsert(
        tenant_id="t1", notice_id="n1", profile_id="p1", total=0, dimensions={}, ctx=mock_ctx
    )

    import json

    body = json.loads(route.calls[0].request.content)
    assert body["disqualifier"] == []
    assert body["disqualified"] is False


@respx.mock
async def test_fit_score_upsert_uses_god_service_token(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-god/fit-scores").mock(return_value=Response(200, json=SCORE))

    await fit_score_upsert(
        tenant_id="t1", notice_id="n1", profile_id="p1", total=0, dimensions={}, ctx=mock_ctx
    )

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-god-token"


@respx.mock
async def test_fit_score_upsert_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.post("http://test-god/fit-scores").mock(return_value=Response(400))

    with pytest.raises(httpx.HTTPStatusError):
        await fit_score_upsert(
            tenant_id="t1", notice_id="n1", profile_id="p1", total=0, dimensions={}, ctx=mock_ctx
        )


@respx.mock
async def test_fit_score_list_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/fit-scores").mock(return_value=Response(200, json=[SCORE]))

    result = await fit_score_list(tenant_id="t1", profile_id="p1", ctx=mock_ctx)

    assert len(result) == 1
    assert result[0].id == "s1"


@respx.mock
async def test_fit_score_list_passes_min_total(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-god/fit-scores").mock(return_value=Response(200, json=[]))

    await fit_score_list(tenant_id="t1", profile_id="p1", ctx=mock_ctx, min_total=50)

    request = route.calls[0].request
    assert request.url.params["min_total"] == "50"


@respx.mock
async def test_fit_score_set_narrative_success(mock_ctx: MagicMock) -> None:
    updated = {**SCORE, "narrative": "Great fit."}
    respx.patch("http://test-god/fit-scores/s1/narrative").mock(
        return_value=Response(200, json=updated)
    )

    result = await fit_score_set_narrative(score_id="s1", narrative="Great fit.", ctx=mock_ctx)

    assert result.narrative == "Great fit."


@respx.mock
async def test_fit_score_set_narrative_not_found(mock_ctx: MagicMock) -> None:
    respx.patch("http://test-god/fit-scores/missing/narrative").mock(return_value=Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await fit_score_set_narrative(score_id="missing", narrative="x", ctx=mock_ctx)
