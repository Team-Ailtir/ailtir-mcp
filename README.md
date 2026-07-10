# ailtir-mcp

An [MCP][mcp] server that gives Claude direct access to [Ailtir's][ailtir]
Knowledge Base platform. Upload documents, build a Bedrock-powered knowledge
base, and run RAG chat — all from within your AI assistant.

## Prerequisites

- Python 3.13+ (or [uv][uv] — no separate Python install needed with `uvx`)
- An [Ailtir account][ailtir]
- An `AILTIR_MCP_API_TOKEN` for authenticated knowledge-base and profile tools.
  The plugin reporting tools do not require a token.

## Installation

`uvx` runs the server in an isolated environment with no install step —
it is the recommended approach. You need [uv][] installed (`curl -LsSf
https://astral.sh/uv/install.sh | sh`).

### Claude Code

```bash
claude mcp add ailtir uvx ailtir-mcp \
  -e AILTIR_MCP_API_TOKEN=your-secret-here
```

Or add manually to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ailtir": {
      "command": "uvx",
      "args": ["ailtir-mcp"],
      "env": {
        "AILTIR_MCP_API_TOKEN": "your-secret-here"
      }
    }
  }
}
```

### Claude Desktop

Add the following to your `claude_desktop_config.json`
(`~/Library/Application Support/Claude/` on macOS,
`%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "ailtir": {
      "command": "uvx",
      "args": ["ailtir-mcp"],
      "env": {
        "AILTIR_MCP_API_TOKEN": "your-secret-here"
      }
    }
  }
}
```

Replace `your-secret-here` with the secret you copied in Step 1, then
restart Claude Desktop.

### Persistent install (optional)

If you prefer `ailtir-mcp` installed as a persistent global tool:

```bash
uv tool install ailtir-mcp
```

Then use `ailtir-mcp` as the command instead of `uvx ailtir-mcp`.
`pip install` is not recommended — it installs into the active Python
environment and can cause dependency conflicts.

## Tools

Once connected, your AI assistant has access to authenticated Ailtir platform
tools plus two public plugin reporting tools.

### `plugin_report_usage` (public)

Reports an anonymous Ailtir plugin skill invocation. It does not require
`AILTIR_MCP_API_TOKEN` and does not collect a stable installation or workspace
identifier.

```
plugin_report_usage(skill_name: string, plugin_version: string) → PluginReportResult
```

### `plugin_feedback` (public)

Submits an anonymous 1–10 rating, optional short reason, workflow name, and up
to three structured follow-up answers. It does not require
`AILTIR_MCP_API_TOKEN`.

```
plugin_feedback(rating: int, plugin_version: string, ...) → PluginReportResult
```

Both tools return `status: submitted|failed`; reporting failures are visible
but do not raise an MCP tool error.

The hosted Streamable HTTP endpoint for remote connectors is
`https://app.ailtir.ai/ailtir-mcp`.

### `upload`

Uploads a ZIP archive of documents to Ailtir storage and returns a `kb_id`.

```
upload(file_path: string) → kb_id: string
```

| Parameter | Description |
|-----------|-------------|
| `file_path` | Absolute path to the ZIP file on your local machine, e.g. `/Users/alice/docs/tender.zip` |

Returns a `kb_id` that you pass to `analyse`, `list`, and `chat`.

---

### `analyse`

Unzips the uploaded archive and builds an [AWS Bedrock][bedrock] Knowledge
Base from its contents. Triggers the full ingestion pipeline — this typically
takes a few minutes.

```
analyse(kb_id: string) → status: string
```

| Parameter | Description |
|-----------|-------------|
| `kb_id` | The ID returned by `upload` |

---

### `list`

Lists all knowledge bases associated with your Ailtir account.

```
list() → string
```

Returns a formatted list of knowledge bases, each showing name, `kb_id`, and
status (e.g. `ready`, `analysing`, `failed`).

---

### `chat`

Asks a question answered using documents in a given knowledge base
(retrieval-augmented generation via AWS Bedrock).

```
chat(kb_id: string, question: string) → answer: string
```

| Parameter | Description |
|-----------|-------------|
| `kb_id` | The knowledge base to query |
| `question` | Your natural-language question |

## Getting your secret

1. Sign in to the [Ailtir app][ailtir]
2. Click your avatar or name to open the **Account** page
3. Find the **Secrets** cell and click **Reveal**
4. Copy the **MCP Key** — it starts with `amcp_`
5. Paste it as `AILTIR_MCP_API_TOKEN` in your client config (see [Installation](#installation))

## Links

- [Ailtir][ailtir]
- [MCP specification][mcp]
- [uv][uv]
- [Claude Desktop][claude-desktop]
- [api-mcp service][api-mcp] (the backend this server talks to)

[ailtir]: https://ailtir.ai
[mcp]: https://modelcontextprotocol.io
[uv]: https://docs.astral.sh/uv/
[claude-desktop]: https://claude.ai/download
[bedrock]: https://aws.amazon.com/bedrock/
[api-mcp]: https://github.com/Team-Ailtir/api-mcp
