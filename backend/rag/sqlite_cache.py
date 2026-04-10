"""
SQLite Cache Service - Persistent caching.

Stores:
- Analysis response payloads
- NCBI search results
- Variant details
- Embeddings
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)


class SQLiteCache:
    """
    SQLite-based caching service.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.logger = logging.getLogger("sqlite_cache")
        self.db_path = Path(db_path) if db_path else Path(settings.sqlite_cache_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = settings.cache_ttl_seconds
        self._init_database()
        self.logger.info("SQLite cache initialized at %s", self.db_path)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_database(self) -> None:
        """Initialize database tables."""

        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY,
                    query TEXT UNIQUE,
                    results TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS variant_details (
                    id INTEGER PRIMARY KEY,
                    variant_id TEXT UNIQUE,
                    details TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY,
                    mutation_id TEXT,
                    evidence TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY,
                    text TEXT UNIQUE,
                    embedding TEXT,
                    created_at TIMESTAMP
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.error("Database initialization failed: %s", str(exc))

    def get_search_results(self, query: str) -> Optional[Any]:
        """Get cached search results."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT results, expires_at FROM search_results WHERE query = ?",
                (query,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            results_json, expires_at = result
            if datetime.fromisoformat(expires_at) < datetime.now():
                self.delete_search_results(query)
                return None

            return json.loads(results_json)
        except Exception as exc:
            self.logger.warning("Cache retrieval failed: %s", str(exc))
            return None

    def set_search_results(self, query: str, results: Any) -> None:
        """Cache search results."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(seconds=self.cache_ttl)
            cursor.execute(
                """
                INSERT OR REPLACE INTO search_results
                (query, results, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    query,
                    json.dumps(results, default=str),
                    datetime.now().isoformat(),
                    expires_at.isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.warning("Cache write failed: %s", str(exc))

    def delete_search_results(self, query: str) -> None:
        """Delete cached search results."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_results WHERE query = ?", (query,))
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.warning("Cache deletion failed: %s", str(exc))

    def get_variant_details(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Get cached variant details."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT details, expires_at FROM variant_details WHERE variant_id = ?",
                (variant_id,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            details_json, expires_at = result
            if datetime.fromisoformat(expires_at) < datetime.now():
                self.delete_variant_details(variant_id)
                return None

            return json.loads(details_json)
        except Exception as exc:
            self.logger.warning("Variant details retrieval failed: %s", str(exc))
            return None

    def set_variant_details(self, variant_id: str, details: Dict[str, Any]) -> None:
        """Cache variant details."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(seconds=self.cache_ttl)
            cursor.execute(
                """
                INSERT OR REPLACE INTO variant_details
                (variant_id, details, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    variant_id,
                    json.dumps(details, default=str),
                    datetime.now().isoformat(),
                    expires_at.isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.warning("Variant details cache failed: %s", str(exc))

    def delete_variant_details(self, variant_id: str) -> None:
        """Delete cached variant details."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM variant_details WHERE variant_id = ?", (variant_id,))
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.warning("Variant details deletion failed: %s", str(exc))

    def set_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache an embedding vector."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO embeddings
                (text, embedding, created_at)
                VALUES (?, ?, ?)
                """,
                (text, json.dumps(embedding), datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.warning("Embedding cache failed: %s", str(exc))

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get a cached embedding vector."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT embedding FROM embeddings WHERE text = ?", (text,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None
            return json.loads(result[0])
        except Exception as exc:
            self.logger.warning("Embedding retrieval failed: %s", str(exc))
            return None

    def cleanup_expired(self) -> int:
        """Delete expired entries."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("DELETE FROM search_results WHERE expires_at < ?", (now,))
            deleted_searches = cursor.rowcount
            cursor.execute("DELETE FROM variant_details WHERE expires_at < ?", (now,))
            deleted_variants = cursor.rowcount
            cursor.execute("DELETE FROM evidence WHERE expires_at < ?", (now,))
            deleted_evidence = cursor.rowcount

            total_deleted = deleted_searches + deleted_variants + deleted_evidence
            conn.commit()
            conn.close()
            return total_deleted
        except Exception as exc:
            self.logger.error("Cache cleanup failed: %s", str(exc))
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""

        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM search_results")
            search_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM variant_details")
            variant_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM evidence")
            evidence_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            embedding_count = cursor.fetchone()[0]
            conn.close()

            return {
                "search_results": search_count,
                "variant_details": variant_count,
                "evidence": evidence_count,
                "embeddings": embedding_count,
                "total": search_count + variant_count + evidence_count + embedding_count,
                "db_path": str(self.db_path),
                "db_size_mb": self.db_path.stat().st_size / (1024 * 1024)
                if self.db_path.exists()
                else 0,
            }
        except Exception as exc:
            self.logger.error("Stats retrieval failed: %s", str(exc))
            return {}


sqlite_cache = SQLiteCache()

logger.info("SQLite Cache initialized")

__all__ = [
    "SQLiteCache",
    "sqlite_cache",
]
