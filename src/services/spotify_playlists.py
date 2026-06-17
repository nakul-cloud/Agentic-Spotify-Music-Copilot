from src.services.spotify_client import get_spotify_client


def create_playlist(playlist_name: str, description: str = ""):
    """
    Creates a new Spotify playlist for the authorized user.
    """
    try:
        sp = get_spotify_client(user_auth=True)
        user_info = sp.current_user()
        user_id = user_info.get("id")
        if not user_id:
            return {"error": "Could not retrieve user ID from Spotify."}

        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description=description
        )

        return {
            "id": playlist.get("id"),
            "name": playlist.get("name"),
            "description": playlist.get("description"),
            "owner": playlist.get("owner", {}).get("display_name"),
            "spotify_url": playlist.get("external_urls", {}).get("spotify")
        }
    except Exception as e:
        return {"error": f"Failed to create playlist: {str(e)}"}


def add_tracks_to_playlist(playlist_id: str, track_ids: list[str]):
    """
    Adds tracks to an existing playlist by track IDs.
    """
    try:
        sp = get_spotify_client(user_auth=True)
        # Format track IDs with 'spotify:track:' prefix if they don't have it
        uris = [
            tid if tid.startswith("spotify:track:") else f"spotify:track:{tid}"
            for tid in track_ids
        ]

        response = sp.playlist_add_items(playlist_id=playlist_id, items=uris)
        return {
            "success": True,
            "snapshot_id": response.get("snapshot_id"),
            "added_count": len(uris)
        }
    except Exception as e:
        return {"error": f"Failed to add tracks: {str(e)}"}


def get_playlist_tracks(playlist_name: str):
    """
    Retrieves tracks from a playlist by matching playlist name.
    """
    try:
        sp = get_spotify_client(user_auth=True)

        # 1. Search current user's playlists
        playlists = sp.current_user_playlists(limit=50)
        playlist_id = None
        playlist_title = None

        for p in playlists.get("items", []):
            if p.get("name", "").lower() == playlist_name.lower():
                playlist_id = p.get("id")
                playlist_title = p.get("name")
                break

        # 2. If not found, search globally
        if not playlist_id:
            results = sp.search(q=playlist_name, type="playlist", limit=5)
            items = results.get("playlists", {}).get("items", [])
            for item in items:
                if item.get("name", "").lower() == playlist_name.lower():
                    playlist_id = item.get("id")
                    playlist_title = item.get("name")
                    break
            # Fallback to first search result if no exact match but search succeeded
            if not playlist_id and items:
                playlist_id = items[0].get("id")
                playlist_title = items[0].get("name")

        if not playlist_id:
            return {"error": f"Playlist '{playlist_name}' not found."}

        # 3. Retrieve tracks
        results = sp.playlist_tracks(playlist_id=playlist_id)
        items = results.get("items", [])

        tracks = []
        for item in items:
            track = item.get("track")
            if track:
                tracks.append({
                    "name": track.get("name"),
                    "artist": track.get("artists", [{}])[0].get("name"),
                    "album": track.get("album", {}).get("name"),
                    "id": track.get("id"),
                    "spotify_url": track.get("external_urls", {}).get("spotify")
                })

        return {
            "playlist_name": playlist_title,
            "playlist_id": playlist_id,
            "tracks": tracks
        }
    except Exception as e:
        return {"error": f"Failed to get playlist tracks: {str(e)}"}
