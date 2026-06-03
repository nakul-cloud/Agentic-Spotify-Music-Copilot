import os
from dotenv import load_dotenv
load_dotenv()
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials



print("CLIENT ID EXISTS:", bool(os.getenv("SPOTIFY_CLIENT_ID")))
print("CLIENT SECRET EXISTS:", bool(os.getenv("SPOTIFY_CLIENT_SECRET")))
print("CLIENT ID LENGTH:", len(os.getenv("SPOTIFY_CLIENT_ID") or ""))
print("CLIENT SECRET LENGTH:", len(os.getenv("SPOTIFY_CLIENT_SECRET") or ""))

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET"
    )
)

results = sp.search(
    q="Afro House",
    type="track",
    limit=5
)

print(results["tracks"]["items"][0]["name"])