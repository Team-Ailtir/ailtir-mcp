# ailtir-mcp

An [MCP][mcp] server for anonymous Ailtir plugin telemetry. The hosted service
has no account authentication or knowledge-base access.

## Tools

The server advertises exactly three tools:

- `version` returns the installed server version.
- `plugin_report_usage` submits anonymous plugin usage telemetry.
- `plugin_feedback` submits anonymous plugin feedback.

Telemetry submission failures are returned as `status: failed` and do not
raise an MCP tool error.

## Installation

Run the stdio server without credentials:

```bash
uvx ailtir-mcp
```

For a persistent installation:

```bash
uv tool install ailtir-mcp
ailtir-mcp
```

The hosted Streamable HTTP endpoint is
`https://app.ailtir.ai/ailtir-mcp`. It is anonymous.

## Configuration

| Variable | Purpose |
|----------|---------|
| `API_MCP_URL` | Private telemetry relay base URL |
| `MCP_HOST` | HTTP bind host |
| `MCP_PORT` | HTTP bind port |
| `MCP_MOUNT_PATH` | Streamable HTTP path |
| `LOG_LEVEL` | Server log level |
| `LOG_FORMAT` | `json` or `console` |

[mcp]: https://modelcontextprotocol.io
