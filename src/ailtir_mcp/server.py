"""Stdio entrypoint for the ailtir-mcp Claude Code plugin."""

import logging
import sys

import ailtir_mcp.tools  # noqa: F401 — registers all tools with mcp instance
from ailtir_mcp.mcp import mcp


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
