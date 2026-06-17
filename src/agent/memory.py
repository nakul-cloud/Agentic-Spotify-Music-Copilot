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


class QdrantMemoryStore(BaseMemoryStore):
    """
    Placeholder/Interface for Qdrant (Vector DB) preference & semantic profile retrieval.
    """
    def __init__(self, location: str = "localhost", port: int = 6333):
        self.location = location
        self.port = port

    def get(self, session_id: str, key: str) -> Any:
        raise NotImplementedError("Qdrant backend not configured.")

    def set(self, session_id: str, key: str, value: Any) -> None:
        raise NotImplementedError("Qdrant backend not configured.")

    def get_history(self, session_id: str) -> List[Any]:
        raise NotImplementedError("Qdrant backend not configured.")

    def append_history(self, session_id: str, message: Any) -> None:
        raise NotImplementedError("Qdrant backend not configured.")

    def clear(self, session_id: str) -> None:
        raise NotImplementedError("Qdrant backend not configured.")
