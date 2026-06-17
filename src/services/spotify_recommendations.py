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
    
    genre_lower = genre.lower()
    if genre_lower in [g.lower() for g in available_genres]:
        try:
            recommendations = sp.recommendations(seed_genres=[genre_lower], limit=limit)
            tracks = recommendations.get("tracks", [])
            return [_build_track_summary(track) for track in tracks]
        except Exception as e:
            LOGGER.warning("Recommendations endpoint failed (%s). Falling back to search.", str(e))
            
    try:
        # Fallback/Dynamic search if not a seed genre or endpoint failed
        search_res = sp.search(q=f"genre:\"{genre}\"", type="track", limit=limit)
        tracks = search_res.get("tracks", {}).get("items", [])
        if not tracks:
            search_res = sp.search(q=f"genre:{genre}", type="track", limit=limit)
            tracks = search_res.get("tracks", {}).get("items", [])
        return [_build_track_summary(track) for track in tracks]
    except Exception as e:
        return {"error": f"Failed to recommend tracks: {str(e)}"}


def recommend_tracks_by_mood(
    mood: str, 
    limit: int = 10,
    target_energy: float = None,
    target_valence: float = None,
    target_danceability: float = None,
    target_tempo: float = None,
    target_acousticness: float = None
):
    sp = get_spotify_client()
    
    # Common moods mapping as a guide/fallback
    mood_to_genres = {
        "happy": ["pop", "dance"],
        "sad": ["acoustic", "piano"],
        "focus": ["ambient", "chill"],
        "workout": ["work-out", "edm"],
        "chill": ["chill", "ambient"],
        "party": ["party", "dance"],
        "driving": ["rock", "edm"]
    }
    
    seed_genres = ["pop"]
    mood_lower = mood.lower()
    
    if mood_lower in mood_to_genres:
        seed_genres = mood_to_genres[mood_lower]
    else:
        matched = False
        for k, v in mood_to_genres.items():
            if k in mood_lower or mood_lower in k:
                seed_genres = v
                matched = True
                break
        if not matched:
            seed_genres = ["chill"]
            
    try:
        available_genres = _get_recommendation_genres(sp)
        resolved_seeds = [g for g in seed_genres if g in available_genres]
        if not resolved_seeds:
            resolved_seeds = ["chill"]
            
        kwargs = {}
        if target_energy is not None:
            kwargs["target_energy"] = target_energy
        if target_valence is not None:
            kwargs["target_valence"] = target_valence
        if target_danceability is not None:
            kwargs["target_danceability"] = target_danceability
        if target_tempo is not None:
            kwargs["target_tempo"] = target_tempo
        if target_acousticness is not None:
            kwargs["target_acousticness"] = target_acousticness
            
        try:
            recommendations = sp.recommendations(seed_genres=resolved_seeds[:2], limit=limit, **kwargs)
            tracks = recommendations.get("tracks", [])
            return [_build_track_summary(track) for track in tracks]
        except Exception as e:
            LOGGER.warning("Recommendations failed (%s). Falling back to search.", str(e))
            search_res = sp.search(q=mood, type="track", limit=limit)
            tracks = search_res.get("tracks", {}).get("items", [])
            return [_build_track_summary(track) for track in tracks]
    except Exception as e:
        return {"error": f"Failed to recommend tracks: {str(e)}"}
