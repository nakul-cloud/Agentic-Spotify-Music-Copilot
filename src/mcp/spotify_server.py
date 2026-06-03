
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

from src.mcp.tool_registry import register_tools

mcp = FastMCP("Spotify Copilot")
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
register_tools(mcp)


if __name__ == "__main__":
    mcp.run()