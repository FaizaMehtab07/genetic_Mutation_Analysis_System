"""
LangGraph Workflow Definition - Complete with conditional routing.

Defines the mutation analysis workflow with:
- Conditional edges based on intermediate results
- Error handling nodes
- Recovery paths for expected failures
"""

import logging
from typing import Any, Dict

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not installed")

from backend.agents.aggregation_agent import aggregation_node
from backend.agents.alignment_agent import alignment_node
from backend.agents.annotation_agent import annotation_node
from backend.agents.classification_agent import classification_node
from backend.agents.mutation_detection_agent import mutation_detection_node
from backend.agents.validation_agent import validation_node
from backend.core.state import State
from backend.rag.retrieval_agent_llamaindex import retrieval_node

logger = logging.getLogger(__name__)


def build_analysis_graph():
    """
    Build the full LangGraph workflow for mutation analysis.
    """

    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph not installed. Install with: pip install langgraph")

    logger.info("Building complete analysis graph with conditional routing...")

    graph = StateGraph(State)

    graph.add_node("validation", validation_node)
    graph.add_node("alignment", alignment_node)
    graph.add_node("mutation_detection", mutation_detection_node)
    graph.add_node("annotation", annotation_node)
    graph.add_node("classification", classification_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("aggregation", aggregation_node)
    graph.add_node("error_handler", error_handler_node)
    graph.add_node("no_mutations_handler", no_mutations_handler_node)

    graph.add_edge(START, "validation")

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "alignment": "alignment",
            "error": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "alignment",
        route_after_alignment,
        {
            "mutation_detection": "mutation_detection",
            "error": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "mutation_detection",
        route_after_mutation_detection,
        {
            "annotation": "annotation",
            "no_mutations": "no_mutations_handler",
            "error": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "annotation",
        route_after_annotation,
        {
            "classification": "classification",
            "error": "error_handler",
        },
    )

    graph.add_edge("classification", "retrieval")
    graph.add_edge("retrieval", "aggregation")
    graph.add_edge("no_mutations_handler", "aggregation")
    graph.add_edge("error_handler", "aggregation")
    graph.add_edge("aggregation", END)

    compiled_graph = graph.compile()
    logger.info("Graph compiled successfully with conditional routing")
    return compiled_graph


def route_after_validation(state: State) -> str:
    """Route after validation."""

    validation_result = state.get("validation_result")
    if validation_result and validation_result.is_valid:
        logger.debug("Validation passed -> alignment")
        return "alignment"

    logger.debug("Validation failed -> error handler")
    return "error"


def route_after_alignment(state: State) -> str:
    """Route after alignment."""

    alignment_result = state.get("alignment_result")
    if alignment_result and alignment_result.success:
        logger.debug("Alignment succeeded -> mutation detection")
        return "mutation_detection"

    logger.debug("Alignment failed -> error handler")
    return "error"


def route_after_mutation_detection(state: State) -> str:
    """Route after mutation detection."""

    if state.get("status") == "failed":
        logger.debug("Mutation detection failed -> error handler")
        return "error"

    mutations = state.get("mutations", [])
    if mutations and len(mutations) > 0:
        logger.debug("%s mutation(s) detected -> annotation", len(mutations))
        return "annotation"

    logger.debug("No mutations detected -> no_mutations_handler")
    return "no_mutations"


def route_after_annotation(state: State) -> str:
    """Route after annotation."""

    if state.get("status") == "failed":
        logger.debug("Annotation failed -> error handler")
        return "error"

    logger.debug("Annotation succeeded -> classification")
    return "classification"


def error_handler_node(state: Dict[str, Any]) -> State:
    """Handle validation or processing errors."""

    errors = state.get("errors", [])
    logger.error("Error handler: %s error(s) encountered", len(errors))
    for error in errors:
        logger.error("  - %s", error)

    state["status"] = "failed"
    return state


def no_mutations_handler_node(state: Dict[str, Any]) -> State:
    """Handle the no-mutations path."""

    logger.info("No mutations detected - sequence matches reference")
    state.setdefault("warnings", [])
    state["mutations"] = []
    state["status"] = "completed"
    state["warnings"].append(
        "No mutations detected - sequence is identical to reference"
    )
    return state


try:
    analysis_graph = build_analysis_graph()
    logger.info("Analysis graph initialized successfully with conditional routing")
except Exception as exc:
    logger.error("Failed to build analysis graph: %s", str(exc))
    analysis_graph = None


__all__ = [
    "build_analysis_graph",
    "route_after_validation",
    "route_after_alignment",
    "route_after_mutation_detection",
    "route_after_annotation",
    "error_handler_node",
    "no_mutations_handler_node",
    "analysis_graph",
]
