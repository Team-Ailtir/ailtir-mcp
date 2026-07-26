from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.setting import setting_get, setting_set

SETTING = {
    "key": "etenders.last_seeded_at",
    "value": "2026-01-01T00:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "modified_at": "2026-01-01T00:00:00Z",
}


@respx.mock
async def test_setting_get_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/settings/etenders.last_seeded_at").mock(
        return_value=Response(200, json=SETTING)
    )

    result = await setting_get(key="etenders.last_seeded_at", ctx=mock_ctx)

    assert result.value == "2026-01-01T00:00:00Z"


@respx.mock
async def test_setting_get_uses_god_service_token(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-god/settings/etenders.last_seeded_at").mock(
        return_value=Response(200, json=SETTING)
    )

    await setting_get(key="etenders.last_seeded_at", ctx=mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-god-token"


@respx.mock
async def test_setting_get_not_found(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/settings/missing").mock(return_value=Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await setting_get(key="missing", ctx=mock_ctx)


@respx.mock
async def test_setting_set_success(mock_ctx: MagicMock) -> None:
    respx.put("http://test-god/settings/etenders.last_seeded_at").mock(
        return_value=Response(200, json=SETTING)
    )

    result = await setting_set(
        key="etenders.last_seeded_at", value="2026-01-01T00:00:00Z", ctx=mock_ctx
    )

    assert result.key == "etenders.last_seeded_at"


@respx.mock
async def test_setting_set_sends_value_body(mock_ctx: MagicMock) -> None:
    route = respx.put("http://test-god/settings/etenders.last_seeded_at").mock(
        return_value=Response(200, json=SETTING)
    )

    await setting_set(key="etenders.last_seeded_at", value="2026-01-01T00:00:00Z", ctx=mock_ctx)

    import json

    body = json.loads(route.calls[0].request.content)
    assert body == {"value": "2026-01-01T00:00:00Z"}


@respx.mock
async def test_setting_set_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.put("http://test-god/settings/key").mock(return_value=Response(401))

    with pytest.raises(httpx.HTTPStatusError):
        await setting_set(key="key", value="v", ctx=mock_ctx)
