from src.utils.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI
)

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def _create_retry_session():
    session = requests.Session()
    # Configure retry behavior with exponential backoff on 429 (Rate Limit) and 5xx errors
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def _require_credentials():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError(
            "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
        )


def get_spotify_client(user_auth: bool = False):
    _require_credentials()
    session = _create_retry_session()
    if user_auth:
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative",
                open_browser=False
            ),
            requests_timeout=10,
            requests_session=session
        )
    else:
        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ),
            requests_timeout=10,
            requests_session=session
        )

