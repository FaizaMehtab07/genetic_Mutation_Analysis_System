"""
Gemini embedding and optional summarization helpers.

Gemini remains optional by design:
- core mutation analysis does not depend on Gemini
- embeddings are available for semantic tooling
- cache is persisted in SQLite when enabled
- summarization is exposed for later use without blocking the workflow
"""

import logging
from typing import Dict, List, Optional

from backend.core.config import settings
from backend.rag.sqlite_cache import SQLiteCache, sqlite_cache

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed")

logger = logging.getLogger(__name__)


class GeminiEmbeddingService:
    """
    Optional Gemini service for embeddings, similarity, and later summarization.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_backend: Optional[SQLiteCache] = None,
    ) -> None:
        self.logger = logging.getLogger("gemini_embeddings")
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = settings.gemini_embedding_model
        self.generation_model_name = settings.gemini_generation_model or settings.llm_model
        self.embedding_cache: Dict[str, List[float]] = {}
        self.available = False
        self.cache_backend = cache_backend or sqlite_cache

        if not GEMINI_AVAILABLE:
            self.logger.warning("Gemini client library unavailable")
            return

        if not self.api_key:
            self.logger.warning("Gemini API key not configured")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.available = True
            self.logger.info("Gemini API configured")
        except Exception as exc:
            self.logger.error("Failed to configure Gemini: %s", str(exc))
            self.available = False

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate or retrieve an embedding for a single text."""

        if text in self.embedding_cache:
            return self.embedding_cache[text]

        if self.cache_backend is not None:
            cached_embedding = self.cache_backend.get_embedding(text)
            if cached_embedding is not None:
                self.embedding_cache[text] = cached_embedding
                return cached_embedding

        if not self.available:
            self.logger.warning("Gemini API not available")
            return None

        try:
            response = genai.embed_content(
                model=self.model_name,
                content=text,
                title="Gene mutation query",
            )
            embedding = response["embedding"]
            self.embedding_cache[text] = embedding

            if self.cache_backend is not None:
                self.cache_backend.set_embedding(text, embedding)

            return embedding
        except Exception as exc:
            self.logger.error("Embedding failed: %s", str(exc))
            return None

    def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""

        return [self.embed_text(text) for text in texts]

    def similarity_search(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[tuple]:
        """Return the most similar documents to the query."""

        query_embedding = self.embed_text(query)
        if query_embedding is None:
            return []

        similarities = []
        for document, embedding in zip(documents, self.embed_texts(documents)):
            if embedding is None:
                continue
            score = self._cosine_similarity(query_embedding, embedding)
            similarities.append((document, score))

        similarities.sort(key=lambda item: item[1], reverse=True)
        return similarities[:top_k]

    def summarize_text(self, text: str, instruction: Optional[str] = None) -> Optional[str]:
        """
        Optionally summarize text with Gemini.

        This is intentionally separate from the analysis path so Gemini can be
        used later for user-facing summaries without affecting core execution.
        """

        if not self.available or not self.generation_model_name:
            return None

        try:
            model = genai.GenerativeModel(self.generation_model_name)
            prompt = instruction or "Summarize the following genetic analysis findings clearly and concisely."
            response = model.generate_content(f"{prompt}\n\n{text}")
            summary = getattr(response, "text", None)
            return summary.strip() if isinstance(summary, str) and summary.strip() else None
        except Exception as exc:
            self.logger.warning("Gemini summarization failed: %s", str(exc))
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""

        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a**2 for a in vec1))
        mag2 = math.sqrt(sum(b**2 for b in vec2))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    def get_cache_stats(self) -> dict:
        """Get Gemini cache and availability statistics."""

        persistent_cache_count = 0
        if self.cache_backend is not None:
            try:
                persistent_cache_count = int(
                    self.cache_backend.get_cache_stats().get("embeddings", 0)
                )
            except Exception:
                persistent_cache_count = 0

        return {
            "cache_size": len(self.embedding_cache),
            "persistent_cache_size": persistent_cache_count,
            "available": self.available,
            "embedding_model": self.model_name,
            "generation_model": self.generation_model_name,
            "cached_texts": list(self.embedding_cache.keys())[:10],
        }


gemini_service = GeminiEmbeddingService()

logger.info("Gemini Embedding Service initialized")

__all__ = [
    "GeminiEmbeddingService",
    "gemini_service",
]
