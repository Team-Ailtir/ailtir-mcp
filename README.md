# ailtir-mcp

An [MCP][mcp] server that gives any MCP-compatible AI client (Claude Desktop,
Jentic, and others) direct access to [Ailtir's][ailtir] Knowledge Base
platform. Upload documents, build a Bedrock-powered knowledge base, and run
RAG chat — all from within your AI assistant.

## Prerequisites

- An [Ailtir account][ailtir]
- An `AILTIR_MCP_SECRET` — generate one from **Settings → Developer** in the
  Ailtir app (see [Getting your secret](#getting-your-secret))
- An MCP-compatible client: [Claude Desktop][claude-desktop] or [Jentic][jentic]

## Installation

### Claude Desktop

Add the following to your `claude_desktop_config.json`
(`~/Library/Application Support/Claude/` on macOS,
`%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "ailtir": {
      "type": "sse",
      "url": "https://mcp.ailtir.ai/sse",
      "headers": {
        "Authorization": "Bearer YOUR_AILTIR_MCP_SECRET"
      }
    }
  }
}
```

Replace `YOUR_AILTIR_MCP_SECRET` with the secret you generated in the Ailtir
app, then restart Claude Desktop.

### Jentic

Install the plugin from the [Jentic marketplace][jentic-marketplace] and
follow the on-screen prompts. When asked for your API key, paste your
`AILTIR_MCP_SECRET`.

## Tools

Once connected, your AI assistant has access to the following four tools.

### `upload`

Uploads a ZIP archive of documents to your Ailtir S3 storage.

```
upload(file_path: string) → kb_id: string
```

| Parameter | Description |
|-----------|-------------|
| `file_path` | Absolute path to the local ZIP file to upload |

Returns a `kb_id` that you pass to `analyse`, `list`, and `chat`.

---

### `analyse`

Unzips the uploaded archive and builds an [AWS Bedrock][bedrock] Knowledge
Base from its contents. This triggers the full ingestion pipeline and may
take a few minutes.

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
list() → knowledge_bases: KnowledgeBase[]
```

Each `KnowledgeBase` item contains `kb_id`, `name`, `status`, and
`created_at`.

---

### `chat`

Asks a question answered using the documents in a given knowledge base
(retrieval-augmented generation via AWS Bedrock).

```
chat(kb_id: string, question: string) → answer: string, sources: Source[]
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
5. Set it as `AILTIR_MCP_SECRET` in your client config (see [Installation](#installation))

To revoke a secret, return to **Settings → Developer** and click **Revoke**.

> **Note:** The Developer Settings UI is currently in development.
> Track progress at [app#130][secret-issue].

## Marketplaces

- [Claude MCP marketplace][claude-marketplace]
- [Jentic marketplace][jentic-marketplace]

## Links

- [Ailtir][ailtir]
- [MCP specification][mcp]
- [Claude Desktop][claude-desktop]
- [Jentic][jentic]
- [mcp-api service][mcp-api] (the backend this server talks to)

[ailtir]: https://ailtir.ai
[mcp]: https://modelcontextprotocol.io
[claude-desktop]: https://claude.ai/download
[claude-marketplace]: https://claude.ai/mcp-marketplace
[jentic]: https://jentic.com
[jentic-marketplace]: https://jentic.com/marketplace
[bedrock]: https://aws.amazon.com/bedrock/
[mcp-api]: ../mcp-api/README.md
[secret-issue]: https://github.com/Team-Ailtir/app/issues/130
