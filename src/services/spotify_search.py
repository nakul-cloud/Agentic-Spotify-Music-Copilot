def search_tracks(query: str, limit: int = 5):
    from src.services.spotify_tracks import search_tracks as _search_tracks

    return _search_tracks(query, limit)