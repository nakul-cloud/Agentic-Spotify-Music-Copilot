import os
import pytest
from fastmcp import FastMCP

from src.mcp.tool_registry import register_tools
from src.services.spotify_tracks import search_tracks
from src.services.spotify_analysis import detect_mood, generate_playlist
from src.utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


def test_tool_registry_names():
    mcp = FastMCP("Spotify Copilot")
    tool_names = register_tools(mcp)

    expected_tools = [
        "search_tracks_tool",
        "search_artist_tool",
        "get_track_details_tool",
        "get_artist_top_tracks_tool",
        "search_album_tool",
        "recommend_tracks_by_artist_tool",
        "recommend_tracks_by_genre_tool",
        "recommend_tracks_by_mood_tool",
        "create_playlist_tool",
        "add_tracks_to_playlist_tool",
        "get_playlist_tracks_tool",
        "analyze_track_tool",
        "compare_tracks_tool",
        "mood_detection_tool",
        "playlist_generation_tool"
    ]

    for tool in expected_tools:
        assert tool in tool_names


def test_mood_detection_unit():
    # Test happy mood keywords
    res1 = detect_mood("I want some happy cheerful pop songs")
    assert res1["detected_mood"] == "happy"

    # Test sad mood keywords
    res2 = detect_mood("some sad rainy day acoustic songs")
    assert res2["detected_mood"] == "sad"

    # Test workout mood keywords
    res3 = detect_mood("give me workout gym motivation music")
    assert res3["detected_mood"] == "workout"

    # Test chill mood default or fallback
    res4 = detect_mood("something random without keywords")
    assert res4["detected_mood"] == "chill"


@pytest.mark.integration
def test_spotify_auth_and_search():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET or "YOUR_CLIENT" in SPOTIFY_CLIENT_ID:
        pytest.skip("Missing Spotify credentials")

    results = search_tracks("Afro House", limit=1)
    assert isinstance(results, list)
    if results:
        assert "name" in results[0]


@pytest.mark.integration
def test_playlist_generation_workflow():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET or "YOUR_CLIENT" in SPOTIFY_CLIENT_ID:
        pytest.skip("Missing Spotify credentials")

    res = generate_playlist("energetic house music for working out")
    assert "prompt" in res
    assert "detected_mood" in res
    assert "identified_genre" in res
    assert "tracks" in res
    assert isinstance(res["tracks"], list)
