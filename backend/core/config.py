"""
Configuration management for the application.
"""

from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic.v1 import BaseSettings

try:
    from pydantic import field_validator
except ImportError:
    field_validator = None

try:
    from pydantic.v1 import validator as v1_validator
except ImportError:
    from pydantic import validator as v1_validator

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent


def _coerce_bool(value):
    """Best-effort bool coercion for environment-backed settings."""

    if isinstance(value, bool):
        return value
    if value is None:
        return False

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", ""}:
        return False

    return True


def _normalize_path(value: Optional[Path]) -> Optional[Path]:
    """Normalize relative config paths against the repo layout."""

    if value is None:
        return None

    path_value = Path(value)
    if path_value.is_absolute():
        return path_value

    if path_value.parts and path_value.parts[0].lower() == "backend":
        return PROJECT_DIR / path_value

    return BACKEND_DIR / path_value

class Settings(BaseSettings):
    """Application settings from environment variables"""

    # ============================================================
    # ENVIRONMENT
    # ============================================================
    environment: str = "development"
    debug: bool = True

    @v1_validator("debug", pre=True)
    def _validate_debug_v1(cls, value):
        return _coerce_bool(value)

    if field_validator is not None:
        @field_validator("debug", mode="before")
        @classmethod
        def _validate_debug_v2(cls, value):
            return _coerce_bool(value)

    # ============================================================
    # SERVER
    # ============================================================
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # ============================================================
    # PATHS
    # ============================================================
    data_dir: Path = BACKEND_DIR / "data"
    models_dir: Path = BACKEND_DIR / "models"
    log_dir: Path = BACKEND_DIR / "logs"

    # ============================================================
    # CLINVAR & RAG
    # ============================================================
    clinvar_csv_path: Path = BACKEND_DIR / "data" / "clinvar_database.csv"
    vector_store_path: Path = BACKEND_DIR / "data" / "clinvar_indexed"
    embedding_model: str = "text-embedding-3-small"
    gemini_embedding_model: str = "models/embedding-001"
    gemini_generation_model: Optional[str] = None
    llm_model: Optional[str] = None
    use_llamaindex: bool = True
    use_gemini_embeddings: bool = True
    gemini_api_key: Optional[str] = None
    ncbi_email: str = "geneMutation@example.com"
    ncbi_api_key: Optional[str] = None
    cache_dir: Path = BACKEND_DIR / "data" / "cache"
    sqlite_cache_path: Path = BACKEND_DIR / "data" / "cache.db"
    cache_ttl_seconds: int = 86400

    # ============================================================
    # VECTOR DB
    # ============================================================
    vector_db_type: str = "faiss"  # "faiss" or "pinecone"
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: Optional[str] = None

    # ============================================================
    # ML MODEL
    # ============================================================
    ml_model_path: Path = BACKEND_DIR / "models" / "random_forest_model.pkl"
    ml_scaler_path: Path = BACKEND_DIR / "models" / "feature_scaler.pkl"
    ml_label_encoder_path: Path = BACKEND_DIR / "models" / "label_encoder.pkl"
    use_ml_classifier: bool = True

    # ============================================================
    # LOGGING
    # ============================================================
    log_level: str = "INFO"
    log_file: Optional[Path] = BACKEND_DIR / "logs" / "application.log"

    # ============================================================
    # PERFORMANCE
    # ============================================================
    max_sequence_length: int = 50000
    request_timeout: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()
settings.data_dir = _normalize_path(settings.data_dir)
settings.models_dir = _normalize_path(settings.models_dir)
settings.log_dir = _normalize_path(settings.log_dir)
settings.clinvar_csv_path = _normalize_path(settings.clinvar_csv_path)
settings.vector_store_path = _normalize_path(settings.vector_store_path)
settings.ml_model_path = _normalize_path(settings.ml_model_path)
settings.ml_scaler_path = _normalize_path(settings.ml_scaler_path)
settings.ml_label_encoder_path = _normalize_path(settings.ml_label_encoder_path)
settings.log_file = _normalize_path(settings.log_file)
settings.cache_dir = _normalize_path(settings.cache_dir)
settings.sqlite_cache_path = _normalize_path(settings.sqlite_cache_path)
