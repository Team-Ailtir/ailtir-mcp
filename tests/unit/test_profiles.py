from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.profiles import profile_create, profile_delete, profile_get


@respx.mock
async def test_profile_get_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-mcp-api/api-mcp/profiles/").mock(
        return_value=Response(
            200, json={"id": "abc", "user_id": "u1", "profile": {"role": "admin"}}
        )
    )

    result = await profile_get(mock_ctx)

    assert "admin" in result


@respx.mock
async def test_profile_get_passes_token(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-mcp-api/api-mcp/profiles/").mock(
        return_value=Response(200, json={"id": "abc", "user_id": "u1", "profile": {}})
    )

    await profile_get(mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


@respx.mock
async def test_profile_get_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.get("http://test-mcp-api/api-mcp/profiles/").mock(return_value=Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await profile_get(mock_ctx)


@respx.mock
async def test_profile_create_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/profiles/").mock(return_value=Response(201, json={}))

    result = await profile_create({"role": "admin"}, mock_ctx)

    assert result == "Profile created."


@respx.mock
async def test_profile_create_sends_body(mock_ctx: MagicMock) -> None:
    import json

    route = respx.post("http://test-mcp-api/api-mcp/profiles/").mock(
        return_value=Response(201, json={})
    )

    await profile_create({"role": "admin"}, mock_ctx)

    body = json.loads(route.calls[0].request.content)
    assert body["profile"] == {"role": "admin"}


@respx.mock
async def test_profile_create_passes_token(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/api-mcp/profiles/").mock(
        return_value=Response(201, json={})
    )

    await profile_create({}, mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


@respx.mock
async def test_profile_create_conflict(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/profiles/").mock(return_value=Response(409))

    with pytest.raises(httpx.HTTPStatusError):
        await profile_create({}, mock_ctx)


@respx.mock
async def test_profile_delete_success(mock_ctx: MagicMock) -> None:
    respx.delete("http://test-mcp-api/api-mcp/profiles/").mock(return_value=Response(204))

    result = await profile_delete(mock_ctx)

    assert result == "Profile deleted."


@respx.mock
async def test_profile_delete_passes_token(mock_ctx: MagicMock) -> None:
    route = respx.delete("http://test-mcp-api/api-mcp/profiles/").mock(return_value=Response(204))

    await profile_delete(mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"
