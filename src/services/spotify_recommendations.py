import logging
from src.services.spotify_client import get_spotify_client

LOGGER = logging.getLogger(__name__)


def _build_track_summary(item: dict) -> dict:
    return {
        "name": item.get("name"),
        "artist": item.get("artists", [{}])[0].get("name") if item.get("artists") else "Unknown",
        "album": item.get("album", {}).get("name") if item.get("album") else "Unknown",
        "spotify_url": item.get("external_urls", {}).get("spotify")
    }


def _get_recommendation_genres(sp) -> set[str]:
    try:
        seeds = sp.recommendation_genre_seeds().get("genres", [])
        return set(seeds)
    except Exception:
        # Fallback list of standard genres if the seed endpoint fails/is deprecated
        return {
            "pop", "dance", "rock", "jazz", "classical", "hip-hop", "rap",
            "edm", "house", "acoustic", "ambient", "metal", "country", "r-n-b",
            "alternative", "blues", "chill", "folk", "indie", "soul"
        }


def recommend_tracks_by_artist(artist_name: str, limit: int = 10):
    sp = get_spotify_client()
    try:
        results = sp.search(q=artist_name, type="artist", limit=1)
        items = results.get("artists", {}).get("items", [])

        if not items:
            return {
                "error": "No artists found."
            }

        artist = items[0]
        artist_id = artist.get("id")

        try:
            recommendations = sp.recommendations(seed_artists=[artist_id], limit=limit)
            tracks = recommendations.get("tracks", [])
            return [_build_track_summary(track) for track in tracks]
        except Exception as e:
            LOGGER.warning("Recommendations endpoint failed (%s). Falling back to artist top tracks/search.", str(e))
            # Fallback: Search for top tracks or general tracks of this artist
            tracks = sp.artist_top_tracks(artist_id).get("tracks", [])
            if not tracks:
                search_res = sp.search(q=f"artist:{artist.get('name')}", type="track", limit=limit)
                tracks = search_res.get("tracks", {}).get("items", [])
            return [_build_track_summary(track) for track in tracks[:limit]]
    except Exception as e:
        return {"error": f"Failed to recommend tracks: {str(e)}"}


def recommend_tracks_by_genre(genre: str, limit: int = 10):
    sp = get_spotify_client()
    available_genres = _get_recommendation_genres(sp)

    if genre.lower() not in [g.lower() for g in available_genres]:
        return {
            "error": "Invalid genre. Use a Spotify seed genre.",
            "genre": genre
        }

    try:
        try:
            recommendations = sp.recommendations(seed_genres=[genre.lower()], limit=limit)
            tracks = recommendations.get("tracks", [])
            return [_build_track_summary(track) for track in tracks]
        except Exception as e:
            LOGGER.warning("Recommendations endpoint failed (%s). Falling back to search.", str(e))
            # Fallback: search tracks by genre tag
            search_res = sp.search(q=f"genre:{genre.lower()}", type="track", limit=limit)
            tracks = search_res.get("tracks", {}).get("items", [])
            return [_build_track_summary(track) for track in tracks]
    except Exception as e:
        return {"error": f"Failed to recommend tracks: {str(e)}"}


def recommend_tracks_by_mood(mood: str, limit: int = 10):
    mood_to_genres = {
        "happy": ["pop", "dance"],
        "sad": ["acoustic", "piano"],
        "focus": ["ambient", "chill"],
        "workout": ["work-out", "edm"],
        "chill": ["chill", "ambient"],
        "party": ["party", "dance"],
        "driving": ["rock", "edm"]
    }

    if mood not in mood_to_genres:
        return {
            "error": "Unsupported mood.",
            "mood": mood,
            "supported_moods": sorted(mood_to_genres.keys())
        }

    sp = get_spotify_client()
    try:
        available_genres = _get_recommendation_genres(sp)
        seed_genres = [g for g in mood_to_genres[mood] if g in available_genres]

        if not seed_genres:
            seed_genres = [mood_to_genres[mood][0]]

        try:
            recommendations = sp.recommendations(seed_genres=seed_genres[:2], limit=limit)
            tracks = recommendations.get("tracks", [])
            return [_build_track_summary(track) for track in tracks]
        except Exception as e:
            LOGGER.warning("Recommendations endpoint failed (%s). Falling back to mood-search.", str(e))
            # Fallback: search using mood genre / keywords
            query = f"genre:{seed_genres[0]}"
            search_res = sp.search(q=query, type="track", limit=limit)
            tracks = search_res.get("tracks", {}).get("items", [])
            return [_build_track_summary(track) for track in tracks]
    except Exception as e:
        return {"error": f"Failed to recommend tracks: {str(e)}"}
