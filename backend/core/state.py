"""
Shared Workflow State for LangGraph.

This file defines the state object that flows through all agents.
Each agent reads from and writes to this state.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from backend.models.pydantic_models import (
    AnalysisResponse,
    AlignmentOutput,
    AnnotationOutput,
    ClassificationOutput,
    ClinVarRecord,
    Mutation,
    MutationDetectionOutput,
    RetrievalOutput,
    ValidationOutput,
)


class State(TypedDict, total=False):
    """
    Shared state for the LangGraph workflow.

    `total=False` means not all fields are required.
    """

    sequence: str
    gene: str
    disease_category: Optional[str]

    analysis_id: str
    timestamp: str

    cleaned_sequence: Optional[str]
    reference_sequence: Optional[str]

    validation_result: Optional[ValidationOutput]

    alignment_result: Optional[AlignmentOutput]
    aligned_reference: Optional[str]
    aligned_query: Optional[str]

    mutations: Optional[List[Mutation]]
    mutation_detection_output: Optional[MutationDetectionOutput]

    annotations: Optional[AnnotationOutput]
    annotated_mutations: Optional[List[Any]]

    classification_result: Optional[ClassificationOutput]

    clinical_evidence: Optional[List[ClinVarRecord]]
    evidence_retrieval_output: Optional[RetrievalOutput]

    final_response: Optional[AnalysisResponse]

    errors: List[str]
    warnings: List[str]

    metadata: Dict[str, Any]
    status: str


def create_initial_state(
    sequence: str,
    gene: str,
    analysis_id: str,
    disease_category: Optional[str] = None,
) -> State:
    """
    Create initial state for a new analysis.
    """

    return State(
        sequence=sequence,
        gene=gene,
        disease_category=disease_category,
        analysis_id=analysis_id,
        timestamp=datetime.now().isoformat(),
        cleaned_sequence=None,
        reference_sequence=None,
        validation_result=None,
        alignment_result=None,
        aligned_reference=None,
        aligned_query=None,
        mutations=None,
        mutation_detection_output=None,
        annotations=None,
        annotated_mutations=None,
        classification_result=None,
        clinical_evidence=None,
        evidence_retrieval_output=None,
        final_response=None,
        errors=[],
        warnings=[],
        metadata={
            "node_timings": {},
            "retries": {},
        },
        status="processing",
    )


def get_state_summary(state: State) -> Dict[str, Any]:
    """
    Get a compact summary of the current workflow state.
    """

    return {
        "analysis_id": state.get("analysis_id"),
        "gene": state.get("gene"),
        "status": state.get("status"),
        "validation_done": state.get("validation_result") is not None,
        "alignment_done": state.get("alignment_result") is not None,
        "mutations_detected": len(state.get("mutations", [])) if state.get("mutations") else 0,
        "annotations_done": state.get("annotations") is not None,
        "classification_done": state.get("classification_result") is not None,
        "evidence_retrieved": len(state.get("clinical_evidence", []))
        if state.get("clinical_evidence")
        else 0,
        "error_count": len(state.get("errors", [])),
        "warning_count": len(state.get("warnings", [])),
    }


def has_errors(state: State) -> bool:
    """Check whether the workflow state has collected errors."""

    return len(state.get("errors", [])) > 0


def add_error(state: State, error: str) -> State:
    """Add an error to state."""

    if "errors" not in state:
        state["errors"] = []
    state["errors"].append(error)
    return state


def add_warning(state: State, warning: str) -> State:
    """Add a warning to state."""

    if "warnings" not in state:
        state["warnings"] = []
    state["warnings"].append(warning)
    return state


__all__ = [
    "State",
    "create_initial_state",
    "get_state_summary",
    "has_errors",
    "add_error",
    "add_warning",
]
