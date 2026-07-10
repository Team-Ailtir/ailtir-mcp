from unittest.mock import MagicMock

import httpx
import respx
from httpx import Response

from ailtir_mcp.auth import _bearer_token
from ailtir_mcp.tools.plugin import plugin_feedback, plugin_report_usage


@respx.mock
async def test_plugin_report_usage_is_public(mock_ctx: MagicMock) -> None:
    _bearer_token.set(None)
    route = respx.post("http://test-mcp-api/api-mcp/plugin/usage/").mock(
        return_value=Response(202, json={"status": "submitted", "message": "event submitted"})
    )

    result = await plugin_report_usage("ailtir_ingest", "2.15.0", mock_ctx)

    assert result.status == "submitted"
    assert route.calls[0].request.headers.get("Authorization") is None
    assert route.calls[0].request.read() == (
        b'{"skill_name":"ailtir_ingest","plugin_version":"2.15.0"}'
    )


@respx.mock
async def test_plugin_feedback_sends_complete_payload(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/api-mcp/plugin/feedback/").mock(
        return_value=Response(202, json={"status": "submitted", "message": "event submitted"})
    )

    result = await plugin_feedback(
        8,
        "2.15.0",
        mock_ctx,
        reason="Useful",
        workflow_name="ailtir_ingest",
        followup_answers={"output_quality": "usable_as_is"},
    )

    assert result.status == "submitted"
    body = route.calls[0].request.read()
    assert b'"rating":8' in body
    assert b'"reason":"Useful"' in body
    assert b'"output_quality":"usable_as_is"' in body


@respx.mock
async def test_plugin_report_exposes_api_failure_without_raising(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/plugin/usage/").mock(
        return_value=Response(400, json={"status": "failed", "message": "invalid skill_name"})
    )

    result = await plugin_report_usage("../bad", "2.15.0", mock_ctx)

    assert result.status == "failed"
    assert result.message == "invalid skill_name"
    mock_ctx.error.assert_awaited_once_with("invalid skill_name")


@respx.mock
async def test_plugin_report_handles_unavailable_api(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/plugin/usage/").mock(
        side_effect=httpx.ConnectError("unavailable")
    )

    result = await plugin_report_usage("ailtir_ingest", "2.15.0", mock_ctx)

    assert result.status == "failed"
    assert result.message == "usage service unavailable"


@respx.mock
async def test_plugin_report_handles_invalid_api_response(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/plugin/usage/").mock(
        return_value=Response(202, text="not-json")
    )

    result = await plugin_report_usage("ailtir_ingest", "2.15.0", mock_ctx)

    assert result.status == "failed"
    assert result.message == "usage service unavailable"
