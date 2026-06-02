
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from fastmcp import FastMCP
from src.services.spotify_search import search_tracks

mcp = FastMCP("Spotify Copilot")


@mcp.tool()
def search_tracks_tool(query: str):
    """
    Search Spotify tracks.
    """
    return search_tracks(query)


if __name__ == "__main__":
    mcp.run()