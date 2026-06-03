import os

import pytest
from fastmcp import FastMCP

from src.mcp.tool_registry import register_tools
from src.services.spotify_tracks import search_tracks
from src.utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


def test_tool_registry_names():
    mcp = FastMCP("Spotify Copilot")
    tool_names = register_tools(mcp)

    assert "search_tracks_tool" in tool_names
    assert "search_artist_tool" in tool_names
    assert "get_track_details_tool" in tool_names
    assert "get_artist_top_tracks_tool" in tool_names
    assert "search_album_tool" in tool_names
    assert "recommend_tracks_by_artist_tool" in tool_names
    assert "recommend_tracks_by_genre_tool" in tool_names
    assert "recommend_tracks_by_mood_tool" in tool_names


@pytest.mark.integration
def test_spotify_auth_and_search():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        pytest.skip("Missing Spotify credentials")

    results = search_tracks("Afro House", limit=1)
    assert isinstance(results, list)
