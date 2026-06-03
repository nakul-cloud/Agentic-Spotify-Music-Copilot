from src.utils.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET
)

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


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
