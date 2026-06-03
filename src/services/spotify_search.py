import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.utils.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET
)


def _require_credentials():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError(
            "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
        )


def get_spotify_client():
    _require_credentials()
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        ),
        requests_timeout=10
    )


def search_tracks(query: str, limit: int = 5):
    sp = get_spotify_client()

    results = sp.search(
        q=query,
        type="track",
        limit=limit
    )

    tracks = []

    for item in results["tracks"]["items"]:
        tracks.append(
            {
                "name": item["name"],
                "artist": item["artists"][0]["name"],
                "album": item["album"]["name"],
                "spotify_url": item["external_urls"]["spotify"]
            }
        )

    return tracks