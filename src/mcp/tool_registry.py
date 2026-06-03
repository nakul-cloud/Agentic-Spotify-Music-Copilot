import logging

from fastmcp import FastMCP

from src.services.spotify_search import search_tracks
from src.services.spotify_artist import search_artist, get_artist_top_tracks
from src.services.spotify_tracks import get_track_details
from src.services.spotify_albums import search_album


LOGGER = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> list[str]:
    @mcp.tool()
    def search_tracks_tool(query: str):
        """
        Search Spotify tracks by keyword.
        """
        LOGGER.info("[MCP TOOL CALLED] Query: %s", query)
        return search_tracks(query)

    @mcp.tool()
    def search_artist_tool(artist_name: str):
        """
        Search Spotify artists by name.
        """
        LOGGER.info("[MCP TOOL CALLED] Artist: %s", artist_name)
        return search_artist(artist_name)

    @mcp.tool()
    def get_track_details_tool(track_name: str):
        """
        Get track details by name.
        """
        LOGGER.info("[MCP TOOL CALLED] Track: %s", track_name)
        return get_track_details(track_name)

    @mcp.tool()
    def get_artist_top_tracks_tool(artist_name: str):
        """
        Get top tracks for an artist.
        """
        LOGGER.info("[MCP TOOL CALLED] Artist top tracks: %s", artist_name)
        return get_artist_top_tracks(artist_name)

    @mcp.tool()
    def search_album_tool(album_name: str):
        """
        Search Spotify albums by name.
        """
        LOGGER.info("[MCP TOOL CALLED] Album: %s", album_name)
        return search_album(album_name)

    return [
        "search_tracks_tool",
        "search_artist_tool",
        "get_track_details_tool",
        "get_artist_top_tracks_tool",
        "search_album_tool"
    ]
