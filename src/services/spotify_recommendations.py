from src.services.spotify_client import get_spotify_client


def _build_track_summary(item: dict) -> dict:
	return {
		"name": item.get("name"),
		"artist": item.get("artists", [{}])[0].get("name"),
		"album": item.get("album", {}).get("name"),
		"spotify_url": item.get("external_urls", {}).get("spotify")
	}


def _get_recommendation_genres(sp) -> set[str]:
	seeds = sp.recommendation_genre_seeds().get("genres", [])
	return set(seeds)


def recommend_tracks_by_artist(artist_name: str, limit: int = 10):
	sp = get_spotify_client()
	results = sp.search(q=artist_name, type="artist", limit=1)
	items = results.get("artists", {}).get("items", [])

	if not items:
		return {
			"error": "No artists found."
		}

	artist_id = items[0].get("id")
	recommendations = sp.recommendations(seed_artists=[artist_id], limit=limit)
	tracks = recommendations.get("tracks", [])

	return [_build_track_summary(track) for track in tracks]


def recommend_tracks_by_genre(genre: str, limit: int = 10):
	sp = get_spotify_client()
	available_genres = _get_recommendation_genres(sp)

	if genre not in available_genres:
		return {
			"error": "Invalid genre. Use a Spotify seed genre.",
			"genre": genre
		}

	recommendations = sp.recommendations(seed_genres=[genre], limit=limit)
	tracks = recommendations.get("tracks", [])

	return [_build_track_summary(track) for track in tracks]


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
	available_genres = _get_recommendation_genres(sp)
	seed_genres = [g for g in mood_to_genres[mood] if g in available_genres]

	if not seed_genres:
		return {
			"error": "No available genres for mood.",
			"mood": mood
		}

	recommendations = sp.recommendations(seed_genres=seed_genres[:2], limit=limit)
	tracks = recommendations.get("tracks", [])

	return [_build_track_summary(track) for track in tracks]
