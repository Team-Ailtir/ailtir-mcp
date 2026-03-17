from importlib.metadata import version

from ailtir_mcp.mcp import mcp


@mcp.tool(name="version")
def get_version() -> str:
    """Return the version of the ailtir-mcp server."""
    return version("ailtir-mcp")
