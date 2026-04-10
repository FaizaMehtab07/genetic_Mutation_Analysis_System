"""
Analysis Service - LangGraph orchestration with cache-aware responses.

The analysis path is intentionally independent from Gemini. Gemini can be
added later for optional summarization without becoming a runtime dependency
for mutation detection or ClinVar retrieval.
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from backend.agents.aggregation_agent import aggregation_node
from backend.agents.alignment_agent import alignment_node
from backend.agents.annotation_agent import annotation_node
from backend.agents.classification_agent import classification_node
from backend.agents.mutation_detection_agent import mutation_detection_node
from backend.agents.validation_agent import validation_node
from backend.core.graph import analysis_graph
from backend.core.state import State, create_initial_state
from backend.models.pydantic_models import (
    AnalysisRequest,
    AnalysisResponse,
    ValidationOutput,
)
from backend.rag.retrieval_agent_llamaindex import retrieval_node
from backend.rag.sqlite_cache import sqlite_cache
from backend.utils.error_handling import ErrorTracker

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Main service for mutation analysis.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("services.analysis")
        self.logger.info("AnalysisService initialized")

    async def analyze(
        self,
        request: AnalysisRequest,
        analysis_id: Optional[str] = None,
    ) -> AnalysisResponse:
        """
        Analyze a DNA sequence request through the workflow.
        """

        analysis_id = analysis_id or str(uuid.uuid4())
        tracker = ErrorTracker()
        gene = request.gene.value if hasattr(request.gene, "value") else str(request.gene)

        self.logger.info("Starting analysis: %s", analysis_id)

        try:
            cache_key = self._build_cache_key(request)
            cached_payload = sqlite_cache.get_search_results(cache_key)
            if cached_payload:
                self.logger.info("Returning cached analysis response for %s", analysis_id)
                return self._cached_payload_to_response(cached_payload, analysis_id)

            state = create_initial_state(
                sequence=request.sequence,
                gene=gene,
                analysis_id=analysis_id,
                disease_category=self._stringify_optional_enum(
                    getattr(request, "disease_category", None)
                ),
            )

            if analysis_graph is not None:
                final_state = analysis_graph.invoke(state)
            else:
                self.logger.warning("LangGraph unavailable; using sequential fallback")
                final_state = self._run_sequential_fallback(state)

            tracker.errors.extend(final_state.get("errors", []))
            tracker.warnings.extend(final_state.get("warnings", []))

            response = self._compile_response(final_state)

            if response.status != "failed":
                sqlite_cache.set_search_results(cache_key, self._response_to_payload(response))

            self.logger.info(
                "Analysis complete: status=%s, errors=%s, warnings=%s",
                response.status,
                len(response.errors),
                len(response.warnings),
            )
            return response

        except Exception as exc:
            self.logger.error("Analysis failed: %s", str(exc), exc_info=True)
            tracker.add_error(f"Analysis failed: {str(exc)}", exc)
            return AnalysisResponse(
                analysis_id=analysis_id,
                timestamp=datetime.now().isoformat(),
                gene=gene,
                validation=ValidationOutput(
                    is_valid=False,
                    cleaned_sequence="",
                    length=len(request.sequence),
                    errors=tracker.errors or [f"Analysis failed: {str(exc)}"],
                    warnings=[],
                ),
                alignment=None,
                mutations=None,
                annotations=None,
                classification=None,
                evidence=None,
                status="failed",
                errors=tracker.errors or [f"Analysis failed: {str(exc)}"],
                warnings=[],
            )

    def _build_cache_key(self, request: AnalysisRequest) -> str:
        """Create a stable cache key for an analysis request."""

        disease_category = self._stringify_optional_enum(
            getattr(request, "disease_category", None)
        )
        payload = "|".join(
            [
                request.gene.value if hasattr(request.gene, "value") else str(request.gene),
                request.sequence,
                disease_category or "",
            ]
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"analysis:{digest}"

    def _stringify_optional_enum(self, value: Any) -> Optional[str]:
        """Convert enums or optional values to plain strings."""

        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)

    def _response_to_payload(self, response: AnalysisResponse) -> Dict[str, Any]:
        """Serialize an AnalysisResponse for cache storage."""

        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")
        return response.dict()

    def _cached_payload_to_response(
        self,
        cached_payload: Any,
        analysis_id: str,
    ) -> AnalysisResponse:
        """Rebuild a cached response and refresh request-specific metadata."""

        if isinstance(cached_payload, list):
            raise ValueError("Unexpected cached analysis payload format")

        payload = dict(cached_payload)
        warnings = list(payload.get("warnings") or [])
        warnings.append("Results retrieved from cache")
        payload["warnings"] = warnings
        payload["analysis_id"] = analysis_id
        payload["timestamp"] = datetime.now().isoformat()

        if hasattr(AnalysisResponse, "model_validate"):
            return AnalysisResponse.model_validate(payload)
        return AnalysisResponse.parse_obj(payload)

    def _compile_response(self, final_state: State) -> AnalysisResponse:
        """
        Compile the final API response from workflow state.
        """

        if final_state.get("final_response") is not None:
            return final_state["final_response"]

        errors = final_state.get("errors", [])
        warnings = final_state.get("warnings", [])

        status = "completed"
        if final_state.get("status") == "failed":
            status = "failed"
        elif errors:
            status = "partial_error"

        validation = final_state.get("validation_result") or ValidationOutput(
            is_valid=False,
            cleaned_sequence="",
            length=0,
            errors=["Validation result missing"],
            warnings=[],
        )

        return AnalysisResponse(
            analysis_id=final_state.get("analysis_id", ""),
            timestamp=final_state.get("timestamp", ""),
            gene=final_state.get("gene", ""),
            validation=validation,
            alignment=final_state.get("alignment_result"),
            mutations=final_state.get("mutations"),
            annotations=final_state.get("annotations"),
            classification=final_state.get("classification_result"),
            evidence=final_state.get("evidence_retrieval_output"),
            status=status,
            errors=errors,
            warnings=warnings,
        )

    def _run_sequential_fallback(self, state: State) -> State:
        """
        Fallback execution path when LangGraph is unavailable.
        """

        state = validation_node(state)
        validation = state.get("validation_result")
        if validation is None or not validation.is_valid:
            return aggregation_node(state)

        state = alignment_node(state)
        alignment = state.get("alignment_result")
        if alignment is None or not alignment.success:
            return aggregation_node(state)

        state = mutation_detection_node(state)
        if state.get("mutations"):
            state = annotation_node(state)
            state = classification_node(state)
            state = retrieval_node(state)

        return aggregation_node(state)


analysis_service = AnalysisService()

__all__ = ["AnalysisService", "analysis_service"]
