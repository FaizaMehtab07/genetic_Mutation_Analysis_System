"""
FastAPI server for the Gene Mutation Detection System.

The API now supports:
- LangGraph workflow execution
- automatic local ClinVar fallback when live NCBI is unavailable
- SQLite-backed caching for analysis and retrieval
- Gemini status reporting without making Gemini part of the critical path
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Allow `python server.py` from inside backend/ by adding the project root.
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import settings
from backend.core.constants import GENE_INFO, SUPPORTED_GENES
from backend.models.pydantic_models import (
    AnalysisRequest,
    AnalysisResponse,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    ErrorResponse,
    HealthResponse,
    ReferenceGenesResponse,
)
from backend.rag.gemini_embeddings import gemini_service
from backend.rag.sqlite_cache import sqlite_cache
from backend.services.analysis_service import analysis_service
from backend.utils.logger import setup_logging

logger = setup_logging()

app = FastAPI(
    title="Gene Mutation Detection API",
    description=(
        "Agentic AI system for mutation detection and risk classification "
        "using LangGraph with ClinVar fallback retrieval."
    ),
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every HTTP request with latency."""

    start_time = datetime.now()
    try:
        response = await call_next(request)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(
            "%s %s completed",
            request.method,
            request.url.path,
            extra={
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception as exc:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(
            "%s %s failed: %s",
            request.method,
            request.url.path,
            str(exc),
            extra={"duration_ms": duration_ms},
        )
        raise


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    """Handle validation-style errors."""

    logger.error("Validation error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "status_code": status.HTTP_400_BAD_REQUEST,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    """Handle unexpected exceptions."""

    logger.error("Unexpected error: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


@app.get("/", tags=["Info"])
async def root():
    """API root."""

    return {
        "message": "Gene Mutation Detection API",
        "version": "2.1.0",
        "features": [
            "LangGraph multi-agent workflow",
            "Automatic local ClinVar fallback",
            "SQLite analysis cache",
            "Optional Gemini support for future summarization",
        ],
        "docs": "/api/docs",
        "redoc": "/api/redoc",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health and feature status."""

    live_ncbi_configured = bool(
        settings.ncbi_email and settings.ncbi_email != "geneMutation@example.com"
    )
    retrieval_status = "live_ncbi" if live_ncbi_configured else "local_fallback"
    gemini_status = "configured_optional" if gemini_service.available else "not_configured"

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.1.0",
        services={
            "api": "operational",
            "validation": "operational",
            "alignment": "operational",
            "classification": "operational",
            "retrieval": retrieval_status,
            "sqlite_cache": "operational",
            "gemini": gemini_status,
        },
    )


@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze DNA Sequence",
    tags=["Analysis"],
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def analyze_sequence(request: AnalysisRequest) -> AnalysisResponse:
    """Run the complete mutation analysis pipeline."""

    analysis_id = str(uuid.uuid4())
    logger.info("Analysis request received: %s for gene %s", analysis_id, request.gene)

    try:
        response = await analysis_service.analyze(request, analysis_id=analysis_id)
        logger.info(
            "Analysis completed: %s",
            response.status,
            extra={
                "analysis_id": response.analysis_id,
                "errors": len(response.errors),
                "warnings": len(response.warnings),
            },
        )
        return response
    except Exception as exc:
        logger.error("Analysis endpoint failed: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@app.post(
    "/api/v1/bulk-analyze",
    response_model=BulkAnalysisResponse,
    summary="Bulk Analysis",
    tags=["Analysis"],
)
async def bulk_analyze(request: BulkAnalysisRequest) -> BulkAnalysisResponse:
    """Analyze multiple sequences."""

    logger.info("Bulk analysis requested for %s sequence(s)", len(request.requests))

    responses = []
    failed_count = 0
    for single_request in request.requests:
        try:
            responses.append(await analyze_sequence(single_request))
        except Exception as exc:
            failed_count += 1
            logger.error("Bulk analysis item failed: %s", str(exc))

    return BulkAnalysisResponse(
        responses=responses,
        total_submitted=len(request.requests),
        total_completed=len(responses),
        total_failed=failed_count,
    )


@app.get(
    "/api/v1/reference-genes",
    response_model=ReferenceGenesResponse,
    summary="List Supported Genes",
    tags=["Reference"],
)
async def get_reference_genes():
    """Return all supported reference genes."""

    genes_list = sorted(list(SUPPORTED_GENES))
    categorized: Dict[str, List[str]] = {}
    for gene, info in GENE_INFO.items():
        category = info.get("category", "Uncategorized")
        categorized.setdefault(category, []).append(gene)

    for gene_list in categorized.values():
        gene_list.sort()

    return ReferenceGenesResponse(
        available_genes=genes_list,
        categorized_genes=categorized,
        total_genes=len(genes_list),
    )


@app.get(
    "/api/v1/gene-info/{gene_name}",
    summary="Get Gene Information",
    tags=["Reference"],
)
async def get_gene_info(gene_name: str):
    """Return metadata for a supported gene."""

    normalized_gene = gene_name.upper()
    if normalized_gene not in GENE_INFO:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene {gene_name} not found",
        )

    return GENE_INFO[normalized_gene]


@app.get(
    "/api/v1/cache/stats",
    summary="Cache Statistics",
    tags=["Diagnostics"],
)
async def get_cache_stats():
    """Return SQLite and Gemini cache stats."""

    return {
        "sqlite_cache": sqlite_cache.get_cache_stats(),
        "gemini": gemini_service.get_cache_stats(),
        "timestamp": datetime.now().isoformat(),
    }


@app.post(
    "/api/v1/cache/cleanup",
    summary="Cleanup Cache",
    tags=["Diagnostics"],
)
async def cleanup_cache(background_tasks: BackgroundTasks):
    """Clean expired cache entries in the background."""

    def _cleanup() -> None:
        deleted = sqlite_cache.cleanup_expired()
        logger.info("Cache cleanup completed: %s deleted", deleted)

    background_tasks.add_task(_cleanup)
    return {
        "message": "Cache cleanup initiated",
        "timestamp": datetime.now().isoformat(),
    }


@app.get(
    "/api/v1/diagnostics/system",
    summary="System Diagnostics",
    tags=["Diagnostics"],
)
async def get_system_diagnostics():
    """Return high-level runtime diagnostics."""

    live_ncbi_configured = bool(
        settings.ncbi_email and settings.ncbi_email != "geneMutation@example.com"
    )

    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "features": {
            "langgraph": True,
            "llamaindex_retrieval": settings.use_llamaindex,
            "local_clinvar_fallback": True,
            "gemini_optional": gemini_service.available,
            "sqlite_cache": True,
        },
        "retrieval_mode": "live_ncbi" if live_ncbi_configured else "local_fallback",
        "clinvar_csv_path": str(settings.clinvar_csv_path),
        "cache": sqlite_cache.get_cache_stats(),
        "timestamp": datetime.now().isoformat(),
    }


@app.on_event("startup")
async def startup_event():
    """Startup logging."""

    logger.info("Application startup")
    logger.info("Environment: %s", settings.environment)
    logger.info("SQLite cache path: %s", settings.sqlite_cache_path)
    logger.info("ClinVar CSV path: %s", settings.clinvar_csv_path)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown logging."""

    logger.info("Application shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        reload_excludes=[
            "logs/*",
            "data/cache/*",
            "data/cache.db",
            "__pycache__/*",
            ".pytest_cache/*",
            "venv/*",
            "*.log",
        ],
        log_level=settings.log_level.lower(),
    )
