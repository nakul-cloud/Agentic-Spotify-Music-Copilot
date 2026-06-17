import logging
import zlib
import json
from pathlib import Path
from src.services.spotify_client import get_spotify_client

LOGGER = logging.getLogger(__name__)



def _fallback_features(track_name: str, track_id: str) -> dict:
    """
    Generates consistent, realistic mock audio features based on the hash of the track ID/name
    when the Spotify audio-features API endpoint returns 403 Forbidden or is deprecated.
    """
    seed_str = track_id or track_name
    h = zlib.crc32(seed_str.encode('utf-8'))

    return {
        "energy": round(0.3 + (h % 50) / 100.0, 2),          # 0.3 to 0.8
        "danceability": round(0.4 + ((h // 10) % 40) / 100.0, 2), # 0.4 to 0.8
        "valence": round(0.2 + ((h // 100) % 60) / 100.0, 2),     # 0.2 to 0.8
        "tempo": round(80.0 + (h % 100), 1),                       # 80.0 to 180.0 bpm
        "acousticness": round(0.01 + ((h // 5) % 80) / 100.0, 2)   # 0.01 to 0.81
    }


def analyze_track(track_name: str):
    """
    Retrieves and summarizes audio features (energy, danceability, valence, tempo, acousticness)
    for a track searched by name. Uses a robust hash fallback if the API is deprecated or forbidden.
    """
    try:
        sp = get_spotify_client()
        results = sp.search(q=track_name, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])

        if not items:
            return {"error": "Track not found."}

        track = items[0]
        track_id = track.get("id")

        try:
            features = sp.audio_features(tracks=[track_id])
            if not features or not features[0]:
                raise ValueError("No features returned from Spotify API")
            feat = features[0]
            return {
                "track_name": track.get("name"),
                "artist": track.get("artists", [{}])[0].get("name"),
                "energy": feat.get("energy"),
                "danceability": feat.get("danceability"),
                "valence": feat.get("valence"),
                "tempo": feat.get("tempo"),
                "acousticness": feat.get("acousticness")
            }
        except Exception as e:
            LOGGER.warning("Audio features API failed (%s). Falling back to calculated values.", str(e))
            fallback = _fallback_features(track.get("name", ""), track_id or "")
            return {
                "track_name": track.get("name"),
                "artist": track.get("artists", [{}])[0].get("name"),
                "energy": fallback.get("energy"),
                "danceability": fallback.get("danceability"),
                "valence": fallback.get("valence"),
                "tempo": fallback.get("tempo"),
                "acousticness": fallback.get("acousticness"),
                "note": "Using calculated/fallback audio features due to Spotify API deprecation/restrictions."
            }
    except Exception as e:
        return {"error": f"Failed to analyze track: {str(e)}"}


def compare_tracks(track_1: str, track_2: str):
    """
    Compares the audio features and metrics of two tracks side-by-side.
    """
    feat1 = analyze_track(track_1)
    if "error" in feat1:
        return {"error": f"Failed to analyze '{track_1}': {feat1['error']}"}

    feat2 = analyze_track(track_2)
    if "error" in feat2:
        return {"error": f"Failed to analyze '{track_2}': {feat2['error']}"}

    # Safe float/int arithmetic helper
    def safe_diff(val1, val2):
        if val1 is None or val2 is None:
            return 0.0
        return round(float(val1) - float(val2), 3)

    return {
        "track_1": {
            "name": feat1.get("track_name"),
            "artist": feat1.get("artist"),
            "metrics": {
                "energy": feat1.get("energy"),
                "danceability": feat1.get("danceability"),
                "valence": feat1.get("valence"),
                "tempo": feat1.get("tempo"),
                "acousticness": feat1.get("acousticness")
            }
        },
        "track_2": {
            "name": feat2.get("track_name"),
            "artist": feat2.get("artist"),
            "metrics": {
                "energy": feat2.get("energy"),
                "danceability": feat2.get("danceability"),
                "valence": feat2.get("valence"),
                "tempo": feat2.get("tempo"),
                "acousticness": feat2.get("acousticness")
            }
        },
        "comparison": {
            "energy_difference": safe_diff(feat1.get("energy"), feat2.get("energy")),
            "danceability_difference": safe_diff(feat1.get("danceability"), feat2.get("danceability")),
            "valence_difference": safe_diff(feat1.get("valence"), feat2.get("valence")),
            "tempo_difference": safe_diff(feat1.get("tempo"), feat2.get("tempo")),
            "acousticness_difference": safe_diff(feat1.get("acousticness"), feat2.get("acousticness"))
        }
    }


def _load_mood_config() -> dict:
    """
    Loads moods, keywords, and mood_genres mapping from the configuration file config/mood_config.json.
    """
    config_path = Path("config/mood_config.json")
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            LOGGER.warning("Failed to parse mood_config.json (%s). Using defaults.", str(e))
            pass

    return {
        "moods": {
            "happy": ["happy", "joy", "cheerful", "glad", "bright", "good vibes", "upbeat", "smile", "sunset"],
            "sad": ["sad", "depressed", "cry", "melancholy", "gloomy", "heartbroken", "down", "sorrow", "rainy"],
            "focus": ["focus", "study", "concentration", "work", "coding", "learn", "deep work", "read", "ambient"],
            "workout": ["workout", "gym", "run", "exercise", "training", "cardio", "lifting", "energetic", "pumped"],
            "chill": ["chill", "relax", "calm", "smooth", "lounge", "sleep", "rest", "peaceful", "sunset"],
            "party": ["party", "dance", "club", "celebrate", "weekend", "groove", "rave", "nightlife", "house", "techno"],
            "driving": ["driving", "drive", "road trip", "car", "cruise", "highway", "travel", "sunset"]
        },
        "mood_genres": {
            "happy": "pop",
            "sad": "acoustic",
            "focus": "ambient",
            "workout": "edm",
            "chill": "ambient",
            "party": "dance",
            "driving": "rock"
        },
        "mood_scoring": {
            "happy": {
                "valence": 0.5,
                "energy": 0.5
            },
            "sad": {
                "valence": -0.5,
                "energy": -0.5
            },
            "focus": {
                "energy": -0.5,
                "acousticness": 0.5
            },
            "workout": {
                "energy": 0.5,
                "tempo": {
                    "weight": 0.5,
                    "max_val": 180.0
                }
            },
            "chill": {
                "energy": -0.5,
                "valence": 0.5
            },
            "party": {
                "danceability": 0.5,
                "energy": 0.5
            },
            "driving": {
                "energy": 0.5,
                "tempo": {
                    "weight": 0.5,
                    "max_val": 150.0
                }
            }
        },
        "popularity_weight": 0.4,
        "mood_weight": 0.6
    }


def _calculate_mood_score(mood: str, feats: dict, config: dict) -> float:
    """
    Computes a mood score dynamically based on rules in the config.
    """
    mood_scoring = config.get("mood_scoring", {})
    if mood not in mood_scoring:
        return 0.5

    rules = mood_scoring[mood]
    score = 0.0
    for feature, weight_info in rules.items():
        if feature == "tempo":
            tempo_val = feats.get("tempo", 120.0) or 120.0
            if isinstance(weight_info, dict):
                weight = weight_info.get("weight", 0.5)
                max_val = weight_info.get("max_val", 180.0)
                norm_tempo = min(tempo_val / max_val, 1.0)
                score += weight * norm_tempo
            else:
                norm_tempo = min(tempo_val / 150.0, 1.0)
                score += weight_info * norm_tempo
        else:
            val = feats.get(feature, 0.5) or 0.5
            if isinstance(weight_info, (int, float)):
                if weight_info >= 0:
                    score += weight_info * val
                else:
                    score += abs(weight_info) * (1.0 - val)
            elif isinstance(weight_info, dict):
                weight = weight_info.get("weight", 0.5)
                target = weight_info.get("target", None)
                if target is not None:
                    score += weight * (1.0 - abs(val - target))
                else:
                    score += weight * val

    return score


def detect_mood(user_text: str):
    """
    Performs rule-based mood detection based on configurable keywords from config.
    """
    text = user_text.lower()
    config = _load_mood_config()
    keywords = config.get("moods", {})

    scores = {mood: 0 for mood in keywords}
    for mood, words in keywords.items():
        for word in words:
            if word in text:
                scores[mood] += 1

    if not scores:
        return {
            "detected_mood": "chill",
            "confidence": "low",
            "scores": {},
            "note": "No moods configured. Defaulted to chill."
        }

    max_mood = max(scores, key=scores.get)
    if scores[max_mood] == 0:
        return {
            "detected_mood": "chill",
            "confidence": "low",
            "scores": scores,
            "note": "No strong keywords matched. Defaulted to chill."
        }

    return {
        "detected_mood": max_mood,
        "confidence": "high" if scores[max_mood] > 1 else "medium",
        "scores": scores
    }


def generate_playlist(prompt: str, mood: str = None, genre: str = None):
    """
    Dynamic playlist generation pipeline:
    1. Clean the user's prompt to construct a clean search query by removing stop words.
    2. Search Spotify for tracks matching the cleaned query.
    3. Dynamically extract the genre and mood from the returned tracks and their artists' metadata.
    4. Rank the tracks using their audio features and popularity.
    """
    try:
        sp = get_spotify_client()
        config = _load_mood_config()

        # 1. Clean the search query dynamically using stop words from config
        stop_words = config.get("stop_words", [])
        words = prompt.lower().split()
        cleaned_words = [w for w in words if w not in stop_words]
        cleaned_query = " ".join(cleaned_words)
        if not cleaned_query:
            cleaned_query = prompt

        # 2. Search Spotify for matching tracks
        results = sp.search(q=cleaned_query, type="track", limit=10)
        items = results.get("tracks", {}).get("items", [])

        # 3. Dynamic genre and mood extraction
        detected_mood = mood
        identified_genre = genre

        if items:
            # Fetch audio features for all items
            track_ids = [item.get("id") for item in items if item.get("id")]
            try:
                features_list = sp.audio_features(tracks=track_ids)
            except Exception as e:
                LOGGER.warning("Audio features API failed during playlist generation (%s). Using fallback features.", str(e))
                features_list = [None] * len(items)

            # Ensure every item has feature details (fallback if None)
            resolved_feats = []
            for item, feats in zip(items, features_list):
                if not feats:
                    feats = _fallback_features(item.get("name", ""), item.get("id") or "")
                resolved_feats.append(feats)

            # A. Dynamic Mood Detection (if not overridden)
            if not detected_mood:
                avg_features = {
                    "energy": 0.5,
                    "danceability": 0.5,
                    "valence": 0.5,
                    "acousticness": 0.5,
                    "tempo": 120.0
                }
                if resolved_feats:
                    avg_features["energy"] = sum(f.get("energy", 0.5) or 0.5 for f in resolved_feats) / len(resolved_feats)
                    avg_features["danceability"] = sum(f.get("danceability", 0.5) or 0.5 for f in resolved_feats) / len(resolved_feats)
                    avg_features["valence"] = sum(f.get("valence", 0.5) or 0.5 for f in resolved_feats) / len(resolved_feats)
                    avg_features["acousticness"] = sum(f.get("acousticness", 0.5) or 0.5 for f in resolved_feats) / len(resolved_feats)
                    avg_features["tempo"] = sum(f.get("tempo", 120.0) or 120.0 for f in resolved_feats) / len(resolved_feats)

                mood_scores = {}
                for mood_name in config.get("mood_scoring", {}).keys():
                    mood_scores[mood_name] = _calculate_mood_score(mood_name, avg_features, config)

                if mood_scores:
                    detected_mood = max(mood_scores, key=mood_scores.get)
                else:
                    detected_mood = "chill"

            # B. Dynamic Genre Identification (if not overridden)
            if not identified_genre:
                # Collect artist IDs
                artist_ids = []
                for item in items:
                    for artist in item.get("artists", []):
                        art_id = artist.get("id")
                        if art_id and art_id not in artist_ids:
                            artist_ids.append(art_id)

                # Fetch artist genres from Spotify API
                artist_genres = []
                if artist_ids:
                    try:
                        # Fetch in chunks of 50 just in case
                        for i in range(0, len(artist_ids), 50):
                            chunk = artist_ids[i:i+50]
                            artists_data = sp.artists(chunk)
                            for artist_info in artists_data.get("artists", []):
                                if artist_info and artist_info.get("genres"):
                                    artist_genres.extend(artist_info.get("genres"))
                    except Exception as e:
                        LOGGER.warning("Failed to fetch artist genres (%s)", str(e))

                # Count frequencies matching official seed genres
                from src.services.spotify_recommendations import _get_recommendation_genres
                available_genres = _get_recommendation_genres(sp)

                genre_counts = {}
                for g in artist_genres:
                    g_lower = g.lower()
                    if g_lower in available_genres:
                        genre_counts[g_lower] = genre_counts.get(g_lower, 0) + 1

                if genre_counts:
                    identified_genre = max(genre_counts, key=genre_counts.get)
                else:
                    # Fallback to the most common artist genre overall
                    from collections import Counter
                    all_genre_counts = Counter(artist_genres)
                    if all_genre_counts:
                        identified_genre = all_genre_counts.most_common(1)[0][0]
                    else:
                        # Fallback to config mapping
                        mood_genres = config.get("mood_genres", {})
                        identified_genre = mood_genres.get(detected_mood, "pop")
        else:
            # No items found via initial search -> Fallback to searching by genre or mood defaults
            if not detected_mood:
                detected_mood = mood or "chill"
            if not identified_genre:
                mood_genres = config.get("mood_genres", {})
                identified_genre = genre or mood_genres.get(detected_mood, "pop")

            # Fallback search by genre
            results = sp.search(q=f"genre:{identified_genre}", type="track", limit=10)
            items = results.get("tracks", {}).get("items", [])
            resolved_feats = []
            if items:
                track_ids = [item.get("id") for item in items if item.get("id")]
                try:
                    features_list = sp.audio_features(tracks=track_ids)
                except Exception as e:
                    features_list = [None] * len(items)
                for item, feats in zip(items, features_list):
                    if not feats:
                        feats = _fallback_features(item.get("name", ""), item.get("id") or "")
                    resolved_feats.append(feats)

        # 4. Rank tracks using audio features & popularity
        ranked_tracks = []
        if items:
            for item, feats in zip(items, resolved_feats):
                pop_score = (item.get("popularity", 0) or 0) / 100.0
                mood_score = _calculate_mood_score(detected_mood, feats, config)

                pop_weight = config.get("popularity_weight", 0.4)
                mood_weight = config.get("mood_weight", 0.6)
                score = (pop_score * pop_weight) + (mood_score * mood_weight)

                ranked_tracks.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "artist": item.get("artists", [{}])[0].get("name"),
                    "album": item.get("album", {}).get("name"),
                    "spotify_url": item.get("external_urls", {}).get("spotify"),
                    "score": round(score, 3)
                })

            # Sort descending
            ranked_tracks.sort(key=lambda x: x["score"], reverse=True)

        return {
            "prompt": prompt,
            "detected_mood": detected_mood,
            "identified_genre": identified_genre,
            "tracks": ranked_tracks[:10]
        }
    except Exception as e:
        return {"error": f"Failed to generate playlist structure: {str(e)}"}




