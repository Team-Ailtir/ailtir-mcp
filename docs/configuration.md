# Configuration

Replace `amcp_your-secret-here` with the MCP key you copied during installation.

## Claude Code

Add via the CLI (recommended):

```sh
claude mcp add ailtir uvx ailtir-mcp \
  -e AILTIR_MCP_SECRET=amcp_your-secret-here
```

Or add manually to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ailtir": {
      "command": "uvx",
      "args": ["ailtir-mcp"],
      "env": {
        "AILTIR_MCP_SECRET": "amcp_your-secret-here"
      }
    }
  }
}
```

## Claude Desktop

Open `claude_desktop_config.json`
(`~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows)
and add:

```json
{
  "mcpServers": {
    "ailtir": {
      "command": "uvx",
      "args": ["ailtir-mcp"],
      "env": {
        "AILTIR_MCP_SECRET": "amcp_your-secret-here"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

---

Prefer a persistent install? Use `uv tool install ailtir-mcp` and replace `uvx` with
`ailtir-mcp` in the config above. Avoid `pip install` — it installs into the active
Python environment and can cause dependency conflicts.
