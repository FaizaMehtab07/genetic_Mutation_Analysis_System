"""
Vector Database Cache Layer - Local memory with optional persistence.

Uses a simple in-process cache today and keeps a cache directory ready for
future vector-store persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorCache:
    """
    Local cache for API responses and retrieval artifacts.
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self.logger = logging.getLogger("vector_cache")
        default_dir = Path(settings.data_dir) / "cache"
        self.cache_dir = Path(cache_dir) if cache_dir else default_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.cache_ttl = settings.cache_ttl_seconds
        self.chroma_client = None
        self.chroma_collection = None

        if CHROMADB_AVAILABLE:
            try:
                self.chroma_client = chromadb.PersistentClient(path=str(self.cache_dir / "chromadb"))
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name="clinvar_cache"
                )
                self.logger.info("ChromaDB backend enabled")
            except Exception as exc:
                self.logger.warning("Failed to initialize ChromaDB backend: %s", str(exc))
                self.chroma_client = None
                self.chroma_collection = None

        self.logger.info("Vector cache initialized at %s", self.cache_dir)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if present and not expired."""

        if key not in self.cache:
            return None

        timestamp = self.timestamps.get(key)
        if timestamp and (datetime.now() - timestamp).total_seconds() > self.cache_ttl:
            self.logger.debug("Cache expired: %s", key)
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            return None

        self.logger.debug("Cache hit: %s", key)
        return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set a cache value."""

        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        if self.chroma_collection is not None:
            try:
                self.chroma_collection.upsert(
                    ids=[key],
                    documents=[json.dumps(value, default=str)],
                    metadatas=[{"timestamp": self.timestamps[key].isoformat()}],
                )
            except Exception as exc:
                self.logger.debug("Chroma upsert skipped for %s: %s", key, str(exc))
        self.logger.debug("Cached: %s", key)

    def cache_search_results(self, query: str, results: Any) -> None:
        """Cache search results by query string."""

        self.set(f"search:{query}", results)

    def get_cached_search(self, query: str) -> Optional[Any]:
        """Retrieve cached search results."""

        return self.get(f"search:{query}")

    def cache_evidence(self, mutation_id: str, evidence: Any) -> None:
        """Cache evidence for a specific mutation ID."""

        self.set(f"evidence:{mutation_id}", evidence)

    def get_cached_evidence(self, mutation_id: str) -> Optional[Any]:
        """Retrieve cached evidence for a mutation ID."""

        return self.get(f"evidence:{mutation_id}")

    def clear_expired(self) -> None:
        """Remove expired entries from cache."""

        expired_keys = [
            key
            for key, timestamp in self.timestamps.items()
            if (datetime.now() - timestamp).total_seconds() > self.cache_ttl
        ]

        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            self.logger.debug("Cleared expired: %s", key)

        if expired_keys:
            self.logger.info("Cleared %s expired cache entries", len(expired_keys))

    def persist_snapshot(self, filename: str = "cache_snapshot.json") -> Path:
        """Persist a lightweight cache snapshot for debugging."""

        self.clear_expired()
        snapshot_path = self.cache_dir / filename
        serializable = {
            "entries": self.cache,
            "timestamps": {key: value.isoformat() for key, value in self.timestamps.items()},
        }
        with snapshot_path.open("w", encoding="utf-8") as handle:
            json.dump(serializable, handle, indent=2, default=str)
        return snapshot_path

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""

        self.clear_expired()
        return {
            "total_entries": len(self.cache),
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.cache_ttl,
            "backend": "chromadb" if self.chroma_collection is not None else "memory",
        }


vector_cache = VectorCache()

__all__ = [
    "VectorCache",
    "vector_cache",
]
