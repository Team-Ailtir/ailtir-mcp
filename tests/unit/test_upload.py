import pathlib
from unittest.mock import MagicMock

import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.kb_upload import upload

KB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
UPLOAD_URL = "https://uploads.ailtir.ai.s3.amazonaws.com/kbs/tenant/kb/?X-Amz-Signature=abc"
REG_RESPONSE = {"id": KB_ID, "upload_url": UPLOAD_URL}


@pytest.fixture
def zip_file(tmp_path: pathlib.Path) -> pathlib.Path:
    f = tmp_path / "docs.zip"
    f.write_bytes(b"PK\x03\x04fake-zip-content")
    return f


@respx.mock
async def test_upload_success(mock_ctx: MagicMock, zip_file: pathlib.Path) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/").mock(
        return_value=Response(201, json=REG_RESPONSE)
    )
    respx.put(UPLOAD_URL).mock(return_value=Response(200))

    result = await upload(str(zip_file), mock_ctx)

    assert result == KB_ID


@respx.mock
async def test_upload_puts_correct_content(mock_ctx: MagicMock, zip_file: pathlib.Path) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/").mock(
        return_value=Response(201, json=REG_RESPONSE)
    )
    s3_route = respx.put(UPLOAD_URL).mock(return_value=Response(200))

    await upload(str(zip_file), mock_ctx)

    assert s3_route.called
    assert s3_route.calls[0].request.headers["Content-Type"] == "application/zip"
    assert "Authorization" not in s3_route.calls[0].request.headers
    assert s3_route.calls[0].request.content == zip_file.read_bytes()


@respx.mock
async def test_upload_sends_token_to_mcp_api(mock_ctx: MagicMock, zip_file: pathlib.Path) -> None:
    route = respx.post("http://test-mcp-api/api-mcp/kbs/").mock(
        return_value=Response(201, json=REG_RESPONSE)
    )
    respx.put(UPLOAD_URL).mock(return_value=Response(200))

    await upload(str(zip_file), mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


async def test_upload_relative_path(mock_ctx: MagicMock) -> None:
    result = await upload("relative/path.zip", mock_ctx)
    assert "Error" in result


async def test_upload_file_not_found(mock_ctx: MagicMock) -> None:
    result = await upload("/nonexistent/path/docs.zip", mock_ctx)
    assert "Error" in result
