from src.services.spotify_client import get_spotify_client


def search_artist(artist_name: str):
    sp = get_spotify_client()
    results = sp.search(q=artist_name, type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])

    if not items:
        return {
            "error": "No artists found."
        }

    artist = items[0]
    return {
        "name": artist.get("name"),
        "followers": artist.get("followers", {}).get("total"),
        "genres": artist.get("genres", []),
        "popularity": artist.get("popularity"),
        "spotify_url": artist.get("external_urls", {}).get("spotify")
    }


def get_artist_top_tracks(artist_name: str, market: str = "US"):
    sp = get_spotify_client()
    results = sp.search(q=artist_name, type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])

    if not items:
        return {
            "error": "No artists found."
        }

    artist_id = items[0].get("id")
    top_tracks = sp.artist_top_tracks(artist_id, country=market).get("tracks", [])

    return [
        {
            "name": track.get("name"),
            "artist": track.get("artists", [{}])[0].get("name"),
            "album": track.get("album", {}).get("name"),
            "spotify_url": track.get("external_urls", {}).get("spotify")
        }
        for track in top_tracks
    ]
