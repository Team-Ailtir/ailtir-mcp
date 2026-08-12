# Register only the anonymous, dependency-free tools retained by the service.
from ailtir_mcp.tools import plugin, version

__all__ = ["plugin", "version"]
