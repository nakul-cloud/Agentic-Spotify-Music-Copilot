import os
import pytest
from dotenv import load_dotenv
load_dotenv()
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def test_search_demo():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret or "YOUR_CLIENT_ID" in client_id:
        pytest.skip("Missing or placeholder Spotify credentials")

    print("CLIENT ID EXISTS:", bool(client_id))
    print("CLIENT SECRET EXISTS:", bool(client_secret))

    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
    )

    results = sp.search(
        q="Afro House",
        type="track",
        limit=5
    )

    print(results["tracks"]["items"][0]["name"])
    assert len(results["tracks"]["items"]) > 0