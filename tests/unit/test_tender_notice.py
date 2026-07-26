from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.tender_notice import (
    tender_notice_classify,
    tender_notice_get,
    tender_notice_list,
    tender_notice_upsert,
)

NOTICE = {
    "id": "n1",
    "tenant_id": "t1",
    "source": "etenders",
    "resource_id": "12345",
    "portal_url": "https://etenders.gov.ie/12345",
    "listing": {"title": "Road works"},
    "detail": None,
    "status": "new",
    "classification": None,
    "procurement_type": None,
    "authority_name": None,
    "cpv_codes": [],
    "deadline": None,
    "published_at": None,
    "created_at": "2026-01-01T00:00:00Z",
    "modified_at": "2026-01-01T00:00:00Z",
}


@respx.mock
async def test_tender_notice_upsert_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-god/tender-notices").mock(return_value=Response(200, json=NOTICE))

    result = await tender_notice_upsert(
        tenant_id="t1",
        source="etenders",
        resource_id="12345",
        portal_url="https://etenders.gov.ie/12345",
        listing={"title": "Road works"},
        ctx=mock_ctx,
    )

    assert result.id == "n1"
    assert result.status == "new"


@respx.mock
async def test_tender_notice_upsert_sends_body(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-god/tender-notices").mock(
        return_value=Response(200, json=NOTICE)
    )

    await tender_notice_upsert(
        tenant_id="t1",
        source="etenders",
        resource_id="12345",
        portal_url="https://etenders.gov.ie/12345",
        listing={"title": "Road works"},
        ctx=mock_ctx,
        cpv_codes=["45233141"],
    )

    import json

    body = json.loads(route.calls[0].request.content)
    assert body["tenant_id"] == "t1"
    assert body["cpv_codes"] == ["45233141"]


@respx.mock
async def test_tender_notice_upsert_uses_god_service_token(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-god/tender-notices").mock(
        return_value=Response(200, json=NOTICE)
    )

    await tender_notice_upsert(
        tenant_id="t1",
        source="etenders",
        resource_id="12345",
        portal_url="https://etenders.gov.ie/12345",
        listing={},
        ctx=mock_ctx,
    )

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-god-token"


@respx.mock
async def test_tender_notice_upsert_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.post("http://test-god/tender-notices").mock(return_value=Response(400))

    with pytest.raises(httpx.HTTPStatusError):
        await tender_notice_upsert(
            tenant_id="t1",
            source="etenders",
            resource_id="12345",
            portal_url="https://etenders.gov.ie/12345",
            listing={},
            ctx=mock_ctx,
        )


@respx.mock
async def test_tender_notice_classify_success(mock_ctx: MagicMock) -> None:
    classified = {**NOTICE, "status": "classified", "classification": {"sector": "construction"}}
    respx.patch("http://test-god/tender-notices/n1/classification").mock(
        return_value=Response(200, json=classified)
    )

    result = await tender_notice_classify(
        notice_id="n1", classification={"sector": "construction"}, ctx=mock_ctx
    )

    assert result.status == "classified"
    assert result.classification == {"sector": "construction"}


@respx.mock
async def test_tender_notice_list_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/tender-notices").mock(return_value=Response(200, json=[NOTICE]))

    result = await tender_notice_list(tenant_id="t1", ctx=mock_ctx)

    assert len(result) == 1
    assert result[0].id == "n1"


@respx.mock
async def test_tender_notice_list_passes_filters(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-god/tender-notices").mock(return_value=Response(200, json=[]))

    await tender_notice_list(tenant_id="t1", ctx=mock_ctx, status="new", skip=5, take=10)

    request = route.calls[0].request
    assert request.url.params["tenant_id"] == "t1"
    assert request.url.params["status"] == "new"
    assert request.url.params["skip"] == "5"
    assert request.url.params["take"] == "10"


@respx.mock
async def test_tender_notice_get_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/tender-notices/n1").mock(return_value=Response(200, json=NOTICE))

    result = await tender_notice_get(notice_id="n1", ctx=mock_ctx)

    assert result.id == "n1"


@respx.mock
async def test_tender_notice_get_not_found(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/tender-notices/missing").mock(return_value=Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await tender_notice_get(notice_id="missing", ctx=mock_ctx)
