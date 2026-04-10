"""
Aggregation Agent - Compiles final results.

Takes all agent outputs and creates the final analysis response.
"""

import logging
from typing import Any, Dict

from backend.models.pydantic_models import AnalysisResponse, ValidationOutput

logger = logging.getLogger(__name__)


class AggregationAgent:
    """
    Agent for aggregating results from all other agents.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("agents.aggregation")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate results from all nodes into the final response.
        """

        self.logger.info("Aggregation Agent: Compiling results")

        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            errors = state.get("errors", [])
            warnings = state.get("warnings", [])
            validation_result = state.get("validation_result")

            if validation_result is None:
                validation_result = ValidationOutput(
                    is_valid=False,
                    cleaned_sequence="",
                    length=0,
                    errors=["Validation result missing during aggregation"],
                    warnings=[],
                )
                errors.append("Validation result missing during aggregation")
                state["validation_result"] = validation_result

            if not validation_result.is_valid:
                status = "failed"
            elif errors:
                status = "partial_error"
            else:
                status = "completed"

            response = AnalysisResponse(
                analysis_id=state.get("analysis_id", ""),
                timestamp=state.get("timestamp", ""),
                gene=state.get("gene", ""),
                validation=validation_result,
                alignment=state.get("alignment_result"),
                mutations=state.get("mutations"),
                annotations=state.get("annotations"),
                classification=state.get("classification_result"),
                evidence=state.get("evidence_retrieval_output"),
                status=status,
                errors=errors,
                warnings=warnings,
            )

            state["final_response"] = response
            state["status"] = status

            self.logger.info(
                "Aggregation complete: status=%s, errors=%s",
                status,
                len(errors),
            )
            return state

        except Exception as exc:
            self.logger.error("Aggregation error: %s", str(exc), exc_info=True)
            state["errors"].append(f"Aggregation failed: {str(exc)}")
            state["status"] = "failed"
            return state


def aggregation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for aggregation."""

    agent = AggregationAgent()
    return agent.execute(state)
