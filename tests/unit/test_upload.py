import base64
from unittest.mock import MagicMock

import respx
from httpx import Response

from ailtir_mcp.tools.upload import upload

VALID_ZIP_B64 = base64.b64encode(b"PK\x03\x04fake-zip-content").decode()

KB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
REG_RESPONSE = {"kb_id": KB_ID, "s3_key": f"kbs/{TENANT_ID}/{KB_ID}/"}


@respx.mock
async def test_upload_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/kb").mock(return_value=Response(201, json=REG_RESPONSE))

    result = await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert result == KB_ID
    mock_ctx.request_context.lifespan_context.s3.put_object.assert_called_once()
    call_kwargs = mock_ctx.request_context.lifespan_context.s3.put_object.call_args[1]
    assert call_kwargs["Key"] == f"kbs/{TENANT_ID}/{KB_ID}/docs.zip"
    assert call_kwargs["ContentType"] == "application/zip"


async def test_upload_invalid_base64(mock_ctx: MagicMock) -> None:
    result = await upload("docs.zip", "not-valid-base64!!!", mock_ctx)
    assert "Error" in result
    mock_ctx.request_context.lifespan_context.s3.put_object.assert_not_called()


@respx.mock
async def test_upload_passes_token_to_mcp_api(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/kb").mock(return_value=Response(201, json=REG_RESPONSE))

    await upload("docs.zip", VALID_ZIP_B64, mock_ctx)

    assert route.called
    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"
