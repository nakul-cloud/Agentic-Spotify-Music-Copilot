import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.utils.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET
)


sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)


def search_tracks(query: str, limit: int = 5):
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