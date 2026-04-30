from unittest.mock import MagicMock

import respx
from httpx import Response

from ailtir_mcp.tools.kb_list import list_knowledge_bases


@respx.mock
async def test_list_returns_formatted_kbs(mock_ctx: MagicMock) -> None:
    respx.get("http://test-mcp-api/api-mcp/kbs/").mock(
        return_value=Response(
            200,
            json=[
                {"id": "abc-1", "name": "Tender Q1", "status": "ready"},
                {"id": "abc-2", "name": "Tender Q2", "status": "analysing"},
            ],
        )
    )

    result = await list_knowledge_bases(mock_ctx)

    assert "abc-1" in result
    assert "Tender Q1" in result
    assert "ready" in result
    assert "abc-2" in result


@respx.mock
async def test_list_empty(mock_ctx: MagicMock) -> None:
    respx.get("http://test-mcp-api/api-mcp/kbs/").mock(return_value=Response(200, json=[]))

    result = await list_knowledge_bases(mock_ctx)

    assert "No knowledge bases" in result


@respx.mock
async def test_list_passes_token(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-mcp-api/api-mcp/kbs/").mock(return_value=Response(200, json=[]))

    await list_knowledge_bases(mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"
