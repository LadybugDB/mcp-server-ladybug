"""LadybugDB MCP Server - An MCP server for interacting with LadybugDB graph database."""

import logging
from .configs import SERVER_VERSION
from .__main__ import main

logger = logging.getLogger("mcp_server_ladybug")

__version__ = SERVER_VERSION
__all__ = ["main"]
