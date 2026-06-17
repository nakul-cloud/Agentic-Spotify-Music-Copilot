from src.utils.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI
)

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


def _require_credentials():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError(
            "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
        )


def get_spotify_client(user_auth: bool = False):
    _require_credentials()
    if user_auth:
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative",
                open_browser=False
            ),
            requests_timeout=10
        )
    else:
        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ),
            requests_timeout=10
        )

