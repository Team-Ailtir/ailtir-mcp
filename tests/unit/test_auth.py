import httpx
import pytest
import respx
from httpx import Response
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from ailtir_mcp.auth import BearerAuthMiddleware

VERIFY_URL = "http://mcp-api/auth/verify"


async def _ok(request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def _health(request: Request) -> PlainTextResponse:
    return PlainTextResponse("healthy")


def _make_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/health", _health),
            Route("/protected", _ok),
        ],
        middleware=[Middleware(BearerAuthMiddleware, verify_url=VERIFY_URL)],
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(_make_app(), raise_server_exceptions=False)


def test_health_exempt_from_auth(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200


def test_missing_authorization_header(client: TestClient) -> None:
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_malformed_authorization_header(client: TestClient) -> None:
    resp = client.get("/protected", headers={"Authorization": "NotBearer abc"})
    assert resp.status_code == 401


@respx.mock
def test_valid_token_allowed(client: TestClient) -> None:
    respx.get(VERIFY_URL).mock(return_value=Response(200))
    resp = client.get("/protected", headers={"Authorization": "Bearer good-token"})
    assert resp.status_code == 200


@respx.mock
def test_invalid_token_rejected(client: TestClient) -> None:
    respx.get(VERIFY_URL).mock(return_value=Response(401))
    resp = client.get("/protected", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401


@respx.mock
def test_verify_unreachable_returns_503(client: TestClient) -> None:
    respx.get(VERIFY_URL).mock(side_effect=httpx.ConnectError("unreachable"))
    resp = client.get("/protected", headers={"Authorization": "Bearer any-token"})
    assert resp.status_code == 503
