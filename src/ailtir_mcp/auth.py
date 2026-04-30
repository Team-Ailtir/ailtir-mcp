from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

from ailtir_mcp.config import settings

_bearer_token: ContextVar[str | None] = ContextVar("bearer_token", default=None)


def get_token() -> str:
    """Return the bearer token for the current request or fall back to env settings."""
    token = _bearer_token.get()
    if token:
        return token
    if settings.ailtir_mcp_api_token:
        return settings.ailtir_mcp_api_token
    raise ValueError(
        "No auth token: set AILTIR_MCP_API_TOKEN or send Authorization: Bearer <token>"
    )


class BearerTokenMiddleware:
    """Extract a Bearer token from the Authorization header and store it per-request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            auth_value = b""
            for name, value in scope.get("headers", []):
                if name.lower() == b"authorization":
                    auth_value = value
                    break
            auth = auth_value.decode()
            tok = auth[7:] if auth.lower().startswith("bearer ") else None
            reset_tok = _bearer_token.set(tok)
            try:
                await self.app(scope, receive, send)
            finally:
                _bearer_token.reset(reset_tok)
        else:
            await self.app(scope, receive, send)
