import base64
from unittest.mock import MagicMock

import respx
from httpx import Response

from ailtir_mcp.tools.upload import upload

VALID_ZIP_B64 = base64.b64encode(b"PK\x03\x04fake-zip-content").decode()
KB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@respx.mock
async def test_upload_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/kb").mock(return_value=Response(201, json={"kb_id": KB_ID}))

    result = await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert result == KB_ID


@respx.mock
async def test_upload_passes_file_to_mcp_api(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/kb").mock(
        return_value=Response(201, json={"kb_id": KB_ID})
    )

    await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert route.called
    body = route.calls[0].request.read()
    import json

    payload = json.loads(body)
    assert payload["file_name"] == "docs.zip"
    assert payload["file_content_base64"] == VALID_ZIP_B64


@respx.mock
async def test_upload_passes_token_to_mcp_api(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/kb").mock(
        return_value=Response(201, json={"kb_id": KB_ID})
    )

    await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"
