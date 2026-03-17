# ailtir-mcp

An [MCP][mcp] server that gives Claude direct access to [Ailtir's][ailtir]
Knowledge Base platform. Upload documents, build a Bedrock-powered knowledge
base, and run RAG chat — all from within your AI assistant.

## Prerequisites

- Python 3.13+ (or [uv][uv] — no separate Python install needed with `uvx`)
- An [Ailtir account][ailtir]
- An `AILTIR_MCP_SECRET` — generate one from **Settings → Developer** in the
  Ailtir app (see [Getting your secret](#getting-your-secret))

## Installation

### Claude Code

The recommended way — no install step, always runs the latest version:

```bash
claude mcp add ailtir \
  --command uvx \
  --args ailtir-mcp \
  --env AILTIR_MCP_SECRET=your-secret-here
```

Or add manually to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ailtir": {
      "command": "uvx",
      "args": ["ailtir-mcp"],
      "env": {
        "AILTIR_MCP_SECRET": "your-secret-here"
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
        "AILTIR_MCP_SECRET": "your-secret-here"
      }
    }
  }
}
```

Replace `your-secret-here` with the secret you generated in the Ailtir app,
then restart Claude Desktop.

### pip / uv add

If you prefer an explicit install:

```bash
pip install ailtir-mcp
# or
uv add ailtir-mcp
```

Then use `ailtir-mcp` as the command instead of `uvx ailtir-mcp`.

## Tools

Once connected, your AI assistant has access to the following four tools.

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
2. Go to **Settings → Developer**
3. Click **Generate new secret**
4. Copy the secret immediately — it is shown only once
5. Paste it as `AILTIR_MCP_SECRET` in your client config (see [Installation](#installation))

To revoke a secret, return to **Settings → Developer** and click **Revoke**.

> **Note:** The Developer Settings UI is currently in development.
> Track progress at [app#130][secret-issue].

## Links

- [Ailtir][ailtir]
- [MCP specification][mcp]
- [uv][uv]
- [Claude Desktop][claude-desktop]
- [mcp-api service][mcp-api] (the backend this server talks to)

[ailtir]: https://ailtir.ai
[mcp]: https://modelcontextprotocol.io
[uv]: https://docs.astral.sh/uv/
[claude-desktop]: https://claude.ai/download
[bedrock]: https://aws.amazon.com/bedrock/
[mcp-api]: ../mcp-api/README.md
[secret-issue]: https://github.com/Team-Ailtir/app/issues/130
