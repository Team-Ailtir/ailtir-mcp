from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.profile_fit_config import profile_get_fit_config, profile_set_fit_config

FIT_CONFIG = {
    "sector_weights": {"construction": 1.0},
    "geo_tiers": None,
    "route_prefs": None,
    "engagement": None,
    "score_threshold": 70,
    "max_concurrent_bids": None,
    "fit_threshold": None,
    "contact_emails": ["ops@example.com"],
}


@respx.mock
async def test_profile_get_fit_config_success(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/profiles/fit-config/t1").mock(
        return_value=Response(200, json=FIT_CONFIG)
    )

    result = await profile_get_fit_config(tenant_id="t1", ctx=mock_ctx)

    assert result.tenant_id == "t1"
    assert result.score_threshold == 70
    assert result.contact_emails == ["ops@example.com"]


@respx.mock
async def test_profile_get_fit_config_uses_god_service_token(mock_ctx: MagicMock) -> None:
    route = respx.get("http://test-god/profiles/fit-config/t1").mock(
        return_value=Response(200, json=FIT_CONFIG)
    )

    await profile_get_fit_config(tenant_id="t1", ctx=mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-god-token"


@respx.mock
async def test_profile_get_fit_config_not_found(mock_ctx: MagicMock) -> None:
    respx.get("http://test-god/profiles/fit-config/missing").mock(return_value=Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await profile_get_fit_config(tenant_id="missing", ctx=mock_ctx)


@respx.mock
async def test_profile_set_fit_config_success(mock_ctx: MagicMock) -> None:
    respx.put("http://test-god/profiles/fit-config/t1").mock(
        return_value=Response(200, json=FIT_CONFIG)
    )

    result = await profile_set_fit_config(
        tenant_id="t1",
        ctx=mock_ctx,
        score_threshold=70,
        contact_emails=["ops@example.com"],
    )

    assert result.score_threshold == 70


@respx.mock
async def test_profile_set_fit_config_omits_unset_fields(mock_ctx: MagicMock) -> None:
    route = respx.put("http://test-god/profiles/fit-config/t1").mock(
        return_value=Response(200, json=FIT_CONFIG)
    )

    await profile_set_fit_config(tenant_id="t1", ctx=mock_ctx, fit_threshold=50)

    import json

    body = json.loads(route.calls[0].request.content)
    assert body == {"fit_threshold": 50}


@respx.mock
async def test_profile_set_fit_config_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.put("http://test-god/profiles/fit-config/t1").mock(return_value=Response(401))

    with pytest.raises(httpx.HTTPStatusError):
        await profile_set_fit_config(tenant_id="t1", ctx=mock_ctx)
