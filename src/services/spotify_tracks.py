from src.services.spotify_client import get_spotify_client


def _build_track_summary(item: dict) -> dict:
    return {
        "name": item.get("name"),
        "artist": item.get("artists", [{}])[0].get("name"),
        "album": item.get("album", {}).get("name"),
        "release_date": item.get("album", {}).get("release_date"),
        "popularity": item.get("popularity"),
        "spotify_url": item.get("external_urls", {}).get("spotify")
    }


def search_tracks(query: str, limit: int = 5):
    sp = get_spotify_client()
    results = sp.search(q=query, type="track", limit=limit)

    return [_build_track_summary(item) for item in results.get("tracks", {}).get("items", [])]


def get_track_details(track_name: str):
    sp = get_spotify_client()
    results = sp.search(q=track_name, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])

    if not items:
        return {
            "error": "No tracks found."
        }

    return _build_track_summary(items[0])
