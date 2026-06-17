from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseMemoryStore(ABC):
    """
    Abstract Base Class for Agent Memory Stores.
    Defines interfaces for key-value storage (preferences, context) and conversation history.
    """
    @abstractmethod
    def get(self, session_id: str, key: str) -> Any:
        """Retrieve a specific key for a session."""
        pass

    @abstractmethod
    def set(self, session_id: str, key: str, value: Any) -> None:
        """Store a key-value pair for a session."""
        pass

    @abstractmethod
    def get_history(self, session_id: str) -> List[Any]:
        """Get the message history list for a session."""
        pass

    @abstractmethod
    def append_history(self, session_id: str, message: Any) -> None:
        """Append a message to the session's conversation history."""
        pass

    @abstractmethod
    def clear(self, session_id: str) -> None:
        """Clear all memory for a session."""
        pass


class InMemoryStore(BaseMemoryStore):
    """
    In-memory implementation of the memory store.
    """
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._history: Dict[str, List[Any]] = {}

    def _ensure_session(self, session_id: str):
        if session_id not in self._store:
            self._store[session_id] = {
                "preferences": {},
                "favorite_genres": [],
                "favorite_artists": [],
                "previous_recommendations": []
            }
        if session_id not in self._history:
            self._history[session_id] = []

    def get(self, session_id: str, key: str) -> Any:
        self._ensure_session(session_id)
        return self._store[session_id].get(key)

    def set(self, session_id: str, key: str, value: Any) -> None:
        self._ensure_session(session_id)
        self._store[session_id][key] = value

    def get_history(self, session_id: str) -> List[Any]:
        self._ensure_session(session_id)
        return self._history[session_id]

    def append_history(self, session_id: str, message: Any) -> None:
        self._ensure_session(session_id)
        self._history[session_id].append(message)

    def clear(self, session_id: str) -> None:
        if session_id in self._store:
            del self._store[session_id]
        if session_id in self._history:
            del self._history[session_id]


class RedisMemoryStore(BaseMemoryStore):
    """
    Placeholder/Interface for Redis-backed Memory Store.
    """
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db

    def get(self, session_id: str, key: str) -> Any:
        raise NotImplementedError("Redis backend not configured.")

    def set(self, session_id: str, key: str, value: Any) -> None:
        raise NotImplementedError("Redis backend not configured.")

    def get_history(self, session_id: str) -> List[Any]:
        raise NotImplementedError("Redis backend not configured.")

    def append_history(self, session_id: str, message: Any) -> None:
        raise NotImplementedError("Redis backend not configured.")

    def clear(self, session_id: str) -> None:
        raise NotImplementedError("Redis backend not configured.")


class PostgresMemoryStore(BaseMemoryStore):
    """
    Placeholder/Interface for PostgreSQL-backed Memory Store.
    """
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get(self, session_id: str, key: str) -> Any:
        raise NotImplementedError("Postgres backend not configured.")

    def set(self, session_id: str, key: str, value: Any) -> None:
        raise NotImplementedError("Postgres backend not configured.")

    def get_history(self, session_id: str) -> List[Any]:
        raise NotImplementedError("Postgres backend not configured.")

    def append_history(self, session_id: str, message: Any) -> None:
        raise NotImplementedError("Postgres backend not configured.")

    def clear(self, session_id: str) -> None:
        raise NotImplementedError("Postgres backend not configured.")


import uuid
import time
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding

LOGGER = logging.getLogger(__name__)

class QdrantMemoryStore(BaseMemoryStore):
    """
    Qdrant-backed Vector DB Memory Store.
    Provides semantic long-term memory store/retrieval and structured user profiles.
    """
    def __init__(self, location: str = "localhost", port: int = 6333):
        self.location = location
        self.port = port
        self.collection_name = "user_memory"
        
        try:
            self.client = QdrantClient(url=f"http://{location}:{port}")
            # Automatically creates collection using client.add when document is added
            self.online = True
        except Exception as e:
            LOGGER.warning("Failed to initialize Qdrant backend, falling back to offline mode: %s", str(e))
            self.online = False
            self._local_memories = []
            self._profiles = {}

    def add_memory(self, session_id: str, text: str, category: str, metadata: Optional[dict] = None) -> None:
        """Stores a semantic memory into Qdrant."""
        payload = {
            "text": text,
            "category": category,
            "session_id": session_id,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        if not self.online:
            self._local_memories.append(payload)
            return

        try:
            self.client.add(
                collection_name=self.collection_name,
                documents=[text],
                metadata=[payload],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            LOGGER.error("Failed to add memory to Qdrant: %s", str(e))

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search query over Qdrant memory collection."""
        if not self.online:
            # Simple keyword match fallback for testing
            results = []
            q_lower = query.lower()
            for mem in self._local_memories:
                if q_lower in mem["text"].lower() or any(q_lower in str(v).lower() for v in mem.get("metadata", {}).values()):
                    results.append(mem)
                if len(results) >= limit:
                    break
            return results

        try:
            hits = self.client.query(
                collection_name=self.collection_name,
                query_text=query,
                limit=limit
            )
            return [hit.metadata for hit in hits if hit.metadata]
        except Exception as e:
            LOGGER.error("Failed to search Qdrant memories: %s", str(e))
            return []


    def get_profile(self, session_id: str) -> Dict[str, Any]:
        """Retrieves user profile for the current session."""
        default_profile = {
            "favorite_genres": [],
            "favorite_artists": [],
            "favorite_moods": [],
            "playlist_history": [],
            "conversation_summary": ""
        }
        
        if not self.online:
            return self._profiles.get(session_id, default_profile)

        try:
            # Query for profile matching this session_id
            hits = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="category", match=models.MatchValue(value="profile")),
                        models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id))
                    ]
                ),
                limit=1
            )
            points = hits[0]
            if points:
                return points[0].payload.get("profile", default_profile)
        except Exception as e:
            LOGGER.error("Failed to get profile from Qdrant: %s", str(e))
            
        return default_profile

    def save_profile(self, session_id: str, profile: Dict[str, Any]) -> None:
        """Saves or updates user profile in Qdrant."""
        if not self.online:
            self._profiles[session_id] = profile
            return

        try:
            # Delete existing profiles for this session
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(key="category", match=models.MatchValue(value="profile")),
                            models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id))
                        ]
                    )
                )
            )
            
            # Add new profile
            self.client.add(
                collection_name=self.collection_name,
                documents=[f"Profile for {session_id}"],
                metadata=[{
                    "category": "profile",
                    "session_id": session_id,
                    "profile": profile,
                    "timestamp": time.time()
                }],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            LOGGER.error("Failed to save profile to Qdrant: %s", str(e))

    # Implement BaseMemoryStore abstract stubs
    def get(self, session_id: str, key: str) -> Any:
        profile = self.get_profile(session_id)
        return profile.get(key)

    def set(self, session_id: str, key: str, value: Any) -> None:
        profile = self.get_profile(session_id)
        profile[key] = value
        self.save_profile(session_id, profile)

    def get_history(self, session_id: str) -> List[Any]:
        if not self.online:
            return []
        try:
            hits = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="category", match=models.MatchValue(value="chat_history")),
                        models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id))
                    ]
                )
            )
            points = hits[0]
            # Sort by timestamp
            sorted_points = sorted(points, key=lambda x: x.payload.get("timestamp", 0))
            return [pt.payload.get("message") for pt in sorted_points]
        except Exception as e:
            LOGGER.error("Failed to retrieve chat history from Qdrant: %s", str(e))
            return []

    def append_history(self, session_id: str, message: Any) -> None:
        if not self.online:
            return
        try:
            self.client.add(
                collection_name=self.collection_name,
                documents=[str(message)],
                metadata=[{
                    "category": "chat_history",
                    "session_id": session_id,
                    "message": message,
                    "timestamp": time.time()
                }],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            LOGGER.error("Failed to append chat history to Qdrant: %s", str(e))

    def clear(self, session_id: str) -> None:
        if not self.online:
            if session_id in self._profiles:
                del self._profiles[session_id]
            self._local_memories = [m for m in self._local_memories if m["session_id"] != session_id]
            return
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id))
                        ]
                    )
                )
            )
        except Exception as e:
            LOGGER.error("Failed to clear Qdrant memory: %s", str(e))

