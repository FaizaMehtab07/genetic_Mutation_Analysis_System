"""
Mutation Detection Agent - Finds mutations in aligned sequences.

Scans aligned sequences to identify:
- Substitutions
- Deletions
- Insertions
"""

import logging
from typing import Any, Dict, List

from backend.models.pydantic_models import (
    Mutation,
    MutationDetectionOutput,
    MutationTypeEnum,
)

logger = logging.getLogger(__name__)


class MutationDetectionAgent:
    """
    Agent for detecting mutations in aligned sequences.

    Input State:
        - aligned_reference: str
        - aligned_query: str

    Output State (adds):
        - mutations: List[Mutation]
        - mutation_detection_output: MutationDetectionOutput
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("agents.mutation_detection")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect substitutions, insertions, and deletions from aligned sequences."""

        self.logger.info("Mutation Detection Agent: Starting detection")

        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            aligned_ref = state.get("aligned_reference", "") or ""
            aligned_query = state.get("aligned_query", "") or ""

            if not aligned_ref or not aligned_query:
                raise ValueError("Aligned sequences not found in state")

            if len(aligned_ref) != len(aligned_query):
                raise ValueError("Aligned sequences have different lengths")

            mutations: List[Mutation] = []
            ref_position = 0

            i = 0
            while i < len(aligned_ref):
                ref_base = aligned_ref[i]
                query_base = aligned_query[i]

                if ref_base != "-" and query_base != "-" and ref_base != query_base:
                    mutations.append(
                        Mutation(
                            type=MutationTypeEnum.SUBSTITUTION,
                            position=ref_position + 1,
                            reference_base=ref_base,
                            alternate_base=query_base,
                            context=self._get_context(aligned_ref, aligned_query, i),
                        )
                    )
                    ref_position += 1
                    i += 1
                    continue

                if ref_base != "-" and query_base == "-":
                    deletion_start = ref_position + 1
                    deleted_bases = ""

                    while (
                        i < len(aligned_ref)
                        and aligned_ref[i] != "-"
                        and aligned_query[i] == "-"
                    ):
                        deleted_bases += aligned_ref[i]
                        ref_position += 1
                        i += 1

                    mutations.append(
                        Mutation(
                            type=MutationTypeEnum.DELETION,
                            position=deletion_start,
                            reference_base=deleted_bases,
                            length=len(deleted_bases),
                            context=f"Deleted {len(deleted_bases)} base(s): {deleted_bases}",
                        )
                    )
                    continue

                if ref_base == "-" and query_base != "-":
                    insertion_pos = max(ref_position, 1)
                    inserted_bases = ""

                    while (
                        i < len(aligned_ref)
                        and aligned_ref[i] == "-"
                        and aligned_query[i] != "-"
                    ):
                        inserted_bases += aligned_query[i]
                        i += 1

                    mutations.append(
                        Mutation(
                            type=MutationTypeEnum.INSERTION,
                            position=insertion_pos,
                            alternate_base=inserted_bases,
                            length=len(inserted_bases),
                            context=f"Inserted {len(inserted_bases)} base(s): {inserted_bases}",
                        )
                    )
                    continue

                if ref_base != "-":
                    ref_position += 1
                i += 1

            substitution_count = sum(
                1 for mutation in mutations if mutation.type == MutationTypeEnum.SUBSTITUTION
            )
            insertion_count = sum(
                1 for mutation in mutations if mutation.type == MutationTypeEnum.INSERTION
            )
            deletion_count = sum(
                1 for mutation in mutations if mutation.type == MutationTypeEnum.DELETION
            )

            mutation_counts = {
                "substitution": substitution_count,
                "insertion": insertion_count,
                "deletion": deletion_count,
                "total": len(mutations),
            }

            result = MutationDetectionOutput(
                total_mutations=len(mutations),
                mutations=mutations,
                mutation_counts=mutation_counts,
                has_mutations=len(mutations) > 0,
            )

            state["mutations"] = mutations
            state["mutation_detection_output"] = result
            state["mutation_result"] = result

            self.logger.info(
                "Detected %s mutations: %s substitutions, %s insertions, %s deletions",
                len(mutations),
                substitution_count,
                insertion_count,
                deletion_count,
            )

            return state

        except Exception as exc:
            self.logger.error("Mutation detection error: %s", str(exc), exc_info=True)
            state["status"] = "failed"
            state["errors"].append(f"Mutation detection failed: {str(exc)}")
            empty_result = MutationDetectionOutput(
                total_mutations=0,
                mutations=[],
                mutation_counts={"substitution": 0, "insertion": 0, "deletion": 0, "total": 0},
                has_mutations=False,
            )
            state["mutations"] = []
            state["mutation_detection_output"] = empty_result
            state["mutation_result"] = empty_result
            return state

    def _get_context(self, ref: str, query: str, position: int, window: int = 5) -> str:
        """Return a short sequence window around a mutation."""

        start = max(0, position - window)
        end = min(len(ref), position + window + 1)
        return f"Ref: {ref[start:end]} | Query: {query[start:end]}"


def mutation_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node wrapper for mutation detection.
    """

    agent = MutationDetectionAgent()
    return agent.execute(state)
