from langchain_core.tools import tool
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

@tool
def search_tracks_tool(query: str) -> list:
    """Search Spotify tracks by keyword."""
    return search_tracks(query)

@tool
def search_artist_tool(artist_name: str) -> list:
    """Search Spotify artists by name."""
    return search_artist(artist_name)

@tool
def get_track_details_tool(track_name: str) -> dict:
    """Get track details by name."""
    return get_track_details(track_name)

@tool
def get_artist_top_tracks_tool(artist_name: str) -> list:
    """Get top tracks for an artist."""
    return get_artist_top_tracks(artist_name)

@tool
def search_album_tool(album_name: str) -> list:
    """Search Spotify albums by name."""
    return search_album(album_name)

@tool
def recommend_tracks_by_artist_tool(artist_name: str) -> list:
    """Recommend tracks based on an artist."""
    return recommend_tracks_by_artist(artist_name)

@tool
def recommend_tracks_by_genre_tool(genre: str) -> list:
    """Recommend tracks based on a genre."""
    return recommend_tracks_by_genre(genre)

@tool
def recommend_tracks_by_mood_tool(
    mood: str,
    target_energy: float = None,
    target_valence: float = None,
    target_danceability: float = None,
    target_tempo: float = None,
    target_acousticness: float = None
) -> list:
    """
    Recommend tracks based on a mood.
    Allows passing target audio features (energy, valence, danceability, tempo, acousticness) to fine-tune recommendations dynamically.
    """
    return recommend_tracks_by_mood(
        mood=mood,
        target_energy=target_energy,
        target_valence=target_valence,
        target_danceability=target_danceability,
        target_tempo=target_tempo,
        target_acousticness=target_acousticness
    )

@tool
def create_playlist_tool(playlist_name: str) -> dict:
    """Create a new Spotify playlist for the user."""
    return create_playlist(playlist_name)

@tool
def add_tracks_to_playlist_tool(playlist_id: str, track_ids: list[str]) -> dict:
    """Add tracks to a playlist using their Spotify track IDs."""
    return add_tracks_to_playlist(playlist_id, track_ids)

@tool
def get_playlist_tracks_tool(playlist_name: str) -> list:
    """Get all tracks from a playlist matching the given name."""
    return get_playlist_tracks(playlist_name)

@tool
def analyze_track_tool(track_name: str) -> dict:
    """Analyze a track's audio features (energy, danceability, valence, tempo, acousticness)."""
    return analyze_track(track_name)

@tool
def compare_tracks_tool(track_1: str, track_2: str) -> dict:
    """Compare the audio features of two tracks side-by-side."""
    return compare_tracks(track_1, track_2)

@tool
def mood_detection_tool(user_text: str) -> dict:
    """Detect the user's mood based on the text prompt."""
    return detect_mood(user_text)

@tool
def playlist_generation_tool(prompt: str, mood: str = None, genre: str = None) -> dict:
    """
    Generate a curated playlist structure (mood, genre, ranked tracks) from a prompt.
    Allows optional mood and genre overrides.
    """
    return generate_playlist(prompt, mood=mood, genre=genre)

# List of all tools
ALL_TOOLS = [
    search_tracks_tool,
    search_artist_tool,
    get_track_details_tool,
    get_artist_top_tracks_tool,
    search_album_tool,
    recommend_tracks_by_artist_tool,
    recommend_tracks_by_genre_tool,
    recommend_tracks_by_mood_tool,
    create_playlist_tool,
    add_tracks_to_playlist_tool,
    get_playlist_tracks_tool,
    analyze_track_tool,
    compare_tracks_tool,
    mood_detection_tool,
    playlist_generation_tool
]

# Dictionary of tools for easy lookup in execution
TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}
