from src.services.spotify_client import get_spotify_client


def search_album(album_name: str):
    sp = get_spotify_client()
    results = sp.search(q=album_name, type="album", limit=1)
    items = results.get("albums", {}).get("items", [])

    if not items:
        return {
            "error": "No albums found."
        }

    album = items[0]
    return {
        "name": album.get("name"),
        "artist": album.get("artists", [{}])[0].get("name"),
        "release_date": album.get("release_date"),
        "total_tracks": album.get("total_tracks"),
        "spotify_url": album.get("external_urls", {}).get("spotify")
    }
