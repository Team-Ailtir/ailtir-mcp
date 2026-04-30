from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.kb_chat import chat


@respx.mock
async def test_chat_returns_answer(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/chat").mock(
        return_value=Response(200, json={"answer": "The tender closes on 31 March."})
    )

    result = await chat("kb-123", "When does the tender close?", mock_ctx)

    assert result == "The tender closes on 31 March."


@respx.mock
async def test_chat_sends_question_in_body(mock_ctx: MagicMock) -> None:
    import json

    route = respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/chat").mock(
        return_value=Response(200, json={"answer": "42"})
    )

    await chat("kb-123", "What is the answer?", mock_ctx)

    body = json.loads(route.calls[0].request.content)
    assert body["question"] == "What is the answer?"


@respx.mock
async def test_chat_passes_token(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/chat").mock(
        return_value=Response(200, json={"answer": "ok"})
    )

    await chat("kb-123", "q", mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


@respx.mock
async def test_chat_missing_answer_field(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/chat").mock(
        return_value=Response(200, json={})
    )

    result = await chat("kb-123", "q", mock_ctx)

    assert "No answer" in result


@respx.mock
async def test_chat_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/kb-500/chat").mock(return_value=Response(500))

    with pytest.raises(httpx.HTTPStatusError):
        await chat("kb-500", "q", mock_ctx)
