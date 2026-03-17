import base64
from unittest.mock import MagicMock

import respx
from httpx import Response

from ailtir_mcp.tools.upload import upload

VALID_ZIP_B64 = base64.b64encode(b"PK\x03\x04fake-zip-content").decode()
KB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
UPLOAD_URL = "https://uploads.ailtir.ai.s3.amazonaws.com/kbs/tenant/kb/?X-Amz-Signature=abc"
REG_RESPONSE = {"kb_id": KB_ID, "upload_url": UPLOAD_URL}


@respx.mock
async def test_upload_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/kb").mock(return_value=Response(201, json=REG_RESPONSE))
    respx.put(UPLOAD_URL).mock(return_value=Response(200))

    result = await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert result == KB_ID


@respx.mock
async def test_upload_puts_to_presigned_url(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/kb").mock(return_value=Response(201, json=REG_RESPONSE))
    s3_route = respx.put(UPLOAD_URL).mock(return_value=Response(200))

    await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert s3_route.called
    assert s3_route.calls[0].request.headers["Content-Type"] == "application/zip"
    assert "Authorization" not in s3_route.calls[0].request.headers
    assert s3_route.calls[0].request.content == base64.b64decode(VALID_ZIP_B64)


@respx.mock
async def test_upload_passes_token_to_mcp_api(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/kb").mock(return_value=Response(201, json=REG_RESPONSE))
    respx.put(UPLOAD_URL).mock(return_value=Response(200))

    await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


async def test_upload_invalid_base64(mock_ctx: MagicMock) -> None:
    result = await upload("docs.zip", "not-valid-base64!!!", mock_ctx)
    assert "Error" in result
