import logging

from fastmcp import FastMCP

from src.services.spotify_search import search_tracks
from src.services.spotify_artist import search_artist, get_artist_top_tracks
from src.services.spotify_tracks import get_track_details
from src.services.spotify_albums import search_album
from src.services.spotify_recommendations import (
    recommend_tracks_by_artist,
    recommend_tracks_by_genre,
    recommend_tracks_by_mood
)
from src.services.spotify_playlists import (
    create_playlist,
    add_tracks_to_playlist,
    get_playlist_tracks
)
from src.services.spotify_analysis import (
    analyze_track,
    compare_tracks,
    detect_mood,
    generate_playlist
)


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

    @mcp.tool()
    def recommend_tracks_by_artist_tool(artist_name: str):
        """
        Recommend tracks based on an artist.
        """
        LOGGER.info("[MCP TOOL CALLED] Recommend by artist: %s", artist_name)
        return recommend_tracks_by_artist(artist_name)

    @mcp.tool()
    def recommend_tracks_by_genre_tool(genre: str):
        """
        Recommend tracks based on a genre.
        """
        LOGGER.info("[MCP TOOL CALLED] Recommend by genre: %s", genre)
        return recommend_tracks_by_genre(genre)

    @mcp.tool()
    def recommend_tracks_by_mood_tool(mood: str):
        """
        Recommend tracks based on a mood.
        """
        LOGGER.info("[MCP TOOL CALLED] Recommend by mood: %s", mood)
        return recommend_tracks_by_mood(mood)

    @mcp.tool()
    def create_playlist_tool(playlist_name: str):
        """
        Create a new Spotify playlist for the user.
        """
        LOGGER.info("[MCP TOOL CALLED] Create playlist: %s", playlist_name)
        return create_playlist(playlist_name)

    @mcp.tool()
    def add_tracks_to_playlist_tool(playlist_id: str, track_ids: list[str]):
        """
        Add tracks to a playlist using their Spotify track IDs.
        """
        LOGGER.info("[MCP TOOL CALLED] Add tracks to playlist %s: %s", playlist_id, track_ids)
        return add_tracks_to_playlist(playlist_id, track_ids)

    @mcp.tool()
    def get_playlist_tracks_tool(playlist_name: str):
        """
        Get all tracks from a playlist matching the given name.
        """
        LOGGER.info("[MCP TOOL CALLED] Get playlist tracks: %s", playlist_name)
        return get_playlist_tracks(playlist_name)

    @mcp.tool()
    def analyze_track_tool(track_name: str):
        """
        Analyze a track's audio features (energy, danceability, valence, tempo, acousticness).
        """
        LOGGER.info("[MCP TOOL CALLED] Analyze track: %s", track_name)
        return analyze_track(track_name)

    @mcp.tool()
    def compare_tracks_tool(track_1: str, track_2: str):
        """
        Compare the audio features of two tracks side-by-side.
        """
        LOGGER.info("[MCP TOOL CALLED] Compare tracks: %s vs %s", track_1, track_2)
        return compare_tracks(track_1, track_2)

    @mcp.tool()
    def mood_detection_tool(user_text: str):
        """
        Detect the user's mood based on the text prompt.
        """
        LOGGER.info("[MCP TOOL CALLED] Mood detection for: %s", user_text)
        return detect_mood(user_text)

    @mcp.tool()
    def playlist_generation_tool(prompt: str, mood: str = None, genre: str = None):
        """
        Generate a curated playlist structure (mood, genre, ranked tracks) from a prompt.
        Allows optional mood and genre overrides.
        """
        LOGGER.info("[MCP TOOL CALLED] Generate playlist structure for: %s (mood override: %s, genre override: %s)", prompt, mood, genre)
        return generate_playlist(prompt, mood=mood, genre=genre)

    return [
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
