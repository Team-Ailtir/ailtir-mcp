import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from ailtir_mcp.auth import BearerTokenMiddleware, _bearer_token, get_token
from ailtir_mcp.server_http import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=True)


def test_health_returns_200(client: TestClient) -> None:
    resp = client.get("/ailtir-mcp/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_bearer_middleware_sets_contextvar() -> None:
    """Middleware stores the Bearer token in the contextvar for the request."""
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.routing import Route

    captured: list[str | None] = []

    async def capture_token(req: Request) -> JSONResponse:
        captured.append(_bearer_token.get())
        return JSONResponse({})

    app = Starlette(
        routes=[Route("/probe", capture_token)],
        middleware=[Middleware(BearerTokenMiddleware)],
    )
    tc = TestClient(app)
    tc.get("/probe", headers={"Authorization": "Bearer my-test-token"})

    assert captured == ["my-test-token"]


def test_bearer_middleware_no_header_leaves_contextvar_none() -> None:
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.routing import Route

    captured: list[str | None] = []

    async def capture_token(req: Request) -> JSONResponse:
        captured.append(_bearer_token.get())
        return JSONResponse({})

    app = Starlette(
        routes=[Route("/probe", capture_token)],
        middleware=[Middleware(BearerTokenMiddleware)],
    )
    TestClient(app).get("/probe")

    assert captured == [None]


def test_get_token_uses_contextvar_over_env() -> None:
    _bearer_token.set("header-token")
    assert get_token() == "header-token"


def test_get_token_falls_back_to_env() -> None:
    _bearer_token.set(None)
    # env is set to "test-token-abc123" by tests/conftest.py
    assert get_token() == "test-token-abc123"
