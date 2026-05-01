"""Stdio entrypoint for the ailtir-mcp Claude Code plugin."""

import ailtir_mcp.tools  # noqa: F401 — registers all tools with mcp instance
from ailtir_mcp.config import configure_logging
from ailtir_mcp.mcp import mcp


def main() -> None:
    configure_logging()
    mcp.run()


if __name__ == "__main__":
    main()
