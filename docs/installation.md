# Installation

An [MCP][mcp] plugin that gives Claude direct access to [Ailtir][ailtir] — upload
documents, build a knowledge base, and run RAG chat from within your AI assistant.

## Step 1 — Get your MCP key

The `AILTIR_MCP_SECRET` is a per-user token that authenticates the plugin against the
Ailtir API. Retrieve it from your Account page:

1. Sign in to [app.ailtir.ai][app]
2. Click your avatar or name in the top-right corner to open the **Account** page
3. In the Account card, find the **Secrets** cell and click **Reveal**
4. Copy the **MCP Key** — it starts with `amcp_`

> **Keep this token private.** It grants API access on behalf of your account. Do not
> commit it to version control. You can reveal it again at any time from the same
> Account page.

## Step 2 — Install uv

The plugin runs via [uvx][uv] — no separate install step, always the latest version,
fully isolated. First, make sure uv is available:

```sh
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version
```

> **Why uvx and not pip install?** `uvx` runs ailtir-mcp in its own isolated
> environment — no virtual environment setup, no dependency conflicts, and it always
> fetches the latest version automatically.

[ailtir]: https://ailtir.ai
[app]: https://app.ailtir.ai
[mcp]: https://modelcontextprotocol.io
[uv]: https://docs.astral.sh/uv/
