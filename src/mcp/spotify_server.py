
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from src.services.spotify_search import search_tracks

mcp = FastMCP("Spotify Copilot")
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)


@mcp.tool()
def search_tracks_tool(query: str):
    """
    Search Spotify tracks by keyword.
    """
    logging.info("[MCP TOOL CALLED] Query: %s", query)
    return search_tracks(query)


if __name__ == "__main__":
    mcp.run()