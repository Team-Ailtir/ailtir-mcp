from starlette.testclient import TestClient

from ailtir_mcp.mcp import mcp
from ailtir_mcp.server_http import create_app


def test_health_returns_200() -> None:
    resp = TestClient(create_app(), raise_server_exceptions=True).get("/ailtir-mcp/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


async def test_advertises_exactly_three_anonymous_tools() -> None:
    tools = await mcp.list_tools()
    assert {tool.name for tool in tools} == {
        "plugin_feedback",
        "plugin_report_usage",
        "version",
    }
