import typing
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

import httpx
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_log = structlog.get_logger(__name__)

# Holds the validated bearer token for the current request.
# Set by BearerAuthMiddleware; read by tools.
current_token: ContextVar[str] = ContextVar("current_token", default="")

_EXEMPT_PATHS = {"/health"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Validate AILTIR_MCP_SECRET on every request except /health."""

    def __init__(self, app: typing.Any, verify_url: str) -> None:
        super().__init__(app)
        self._verify_url = verify_url

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            _log.warning("auth.missing_token", path=request.url.path)
            return Response("Unauthorized", status_code=401)

        token = auth.removeprefix("Bearer ")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    self._verify_url,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.RequestError as exc:
            _log.error("auth.verify_unreachable", error=str(exc))
            return Response("Service unavailable", status_code=503)

        if resp.status_code != 200:
            _log.warning("auth.invalid_token", status=resp.status_code)
            return Response("Unauthorized", status_code=401)

        current_token.set(token)
        return await call_next(request)
